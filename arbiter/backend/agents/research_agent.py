"""
research_agent.py — Legal research agent powered by Gemini.

Takes structured IntakeData and finds all applicable Indian laws,
relevant sections, and legal remedies for the user's situation.

The ResearchAgent is the backbone of Arbiter's legal accuracy.
Every claim it produces must be a real, verifiable Indian law.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from models.case import IntakeData, ProblemType, ResearchData
from services.gemini_service import GeminiService, get_gemini_service

logger = logging.getLogger(__name__)

# ── Legal knowledge base: problem type → primary acts ────────────────────────────────────────
PROBLEM_TYPE_ACTS: dict[str, list[str]] = {
    "tenant_dispute": [
        "Transfer of Property Act, 1882",
        "Specific Relief Act, 1963",
        "State Rent Control Acts (e.g. Delhi Rent Control Act, Maharashtra Rent Control Act)",
        "Indian Contract Act, 1872 (Section 74 — penalty clauses)",
        "Consumer Protection Act, 2019 (for builder/developer disputes)",
    ],
    "employment": [
        "Payment of Wages Act, 1936",
        "Industrial Disputes Act, 1947",
        "Shops and Establishments Act (state-specific)",
        "Sexual Harassment of Women at Workplace Act, 2013 (POSH)",
        "Employees' Provident Funds Act, 1952",
        "Labour Code on Wages, 2019",
    ],
    "consumer": [
        "Consumer Protection Act, 2019",
        "Consumer Protection (E-Commerce) Rules, 2020",
        "Information Technology Act, 2000 (for online fraud)",
        "Indian Penal Code, Section 420 (cheating)",
    ],
    "rti": [
        "Right to Information Act, 2005",
        "RTI Rules, 2012",
    ],
    "harassment": [
        "Sexual Harassment of Women at Workplace Act, 2013",
        "Information Technology Act, 2000 — Section 66A (cyber harassment)",
        "Indian Penal Code — Section 354A, 354D (stalking, sexual harassment)",
        "Protection of Women from Domestic Violence Act, 2005",
        "SC/ST (Prevention of Atrocities) Act, 1989",
    ],
    "debt_recovery": [
        "Recovery of Debts and Bankruptcy Act, 1993",
        "Indian Contract Act, 1872",
        "Negotiable Instruments Act, 1881 (Section 138 — cheque bounce)",
        "SARFAESI Act, 2002 (secured creditors)",
    ],
    "other": [
        "Indian Contract Act, 1872",
        "Specific Relief Act, 1963",
        "Code of Civil Procedure, 1908",
    ],
}

RESEARCH_SYSTEM_PROMPT = """You are Arbiter's senior legal researcher specialising in Indian law.

Your job is to identify the exact laws, sections, and remedies that apply to a user's legal problem.

CRITICAL RULES:
1. ONLY cite real, existing Indian laws with correct section numbers.
2. NEVER fabricate case names, section numbers, or legal provisions.
3. If you are not certain a section exists, do not cite it.
4. Focus on laws that are PRACTICALLY useful — the user needs to send a demand letter or file a complaint, not write a thesis.
5. Prioritise the most commonly used and enforceable remedies.
6. Consider the jurisdiction (Indian state) when citing state-specific laws.

OUTPUT FORMAT: Always respond with valid JSON only. No markdown, no explanation outside the JSON.
"""

RESEARCH_PROMPT_TEMPLATE = """Research the applicable Indian laws for this legal problem:

PROBLEM TYPE: {problem_type}
JURISDICTION: {jurisdiction}
SITUATION: {situation_summary}
DESIRED OUTCOME: {desired_outcome}
AMOUNT INVOLVED: {amount_involved}

PRIMARY ACTS TO CONSIDER: {primary_acts}

Return ONLY this JSON structure (no markdown):
{{
  "relevant_acts": [
    "Consumer Protection Act, 2019",
    "Indian Penal Code, 1860"
  ],
  "relevant_sections": [
    "Consumer Protection Act, 2019 — Section 35(1): Right to file complaint before District Commission",
    "Consumer Protection Act, 2019 — Section 69: Limitation period of 2 years from date of cause"
  ],
  "case_precedents": [
    "National Insurance Co. Ltd v. Hindustan Safety Glass Works Ltd (2017) — Supreme Court held that delay must be condoned if sufficient cause shown"
  ],
  "legal_remedies": [
    "File complaint with District Consumer Disputes Redressal Commission",
    "Claim refund + compensation + litigation costs under Section 39(1)",
    "Send demand letter citing Section 2(11) definition of deficiency in service"
  ],
  "recommended_document_type": "demand_letter|rti_application|consumer_complaint|cease_desist|employment_complaint|legal_notice",
  "research_summary": "Plain English explanation in 2-3 sentences of the user's legal position and best next step.",
  "time_limit_days": 30,
  "authority_to_approach": "District Consumer Commission, Delhi"
}}

Be precise. Real section numbers only. If unsure of a case name, omit it.
"""


class ResearchAgent:
    """
    Researches applicable Indian laws for a given legal problem.

    Takes IntakeData → returns ResearchData with acts, sections, remedies.
    """

    def __init__(self, gemini_service: Optional[GeminiService] = None) -> None:
        """
        Initialise ResearchAgent.

        Args:
            gemini_service: Optional injected GeminiService for testing.
        """
        self._gemini = GeminiService(system_instruction=RESEARCH_SYSTEM_PROMPT)

    def _build_situation_summary(self, intake: IntakeData) -> str:
        """Build a concise situation description for the research prompt."""
        parts = [
            f"Complainant: {intake.complainant.name}",
            f"Respondent: {intake.respondent.name}",
            f"Desired outcome: {intake.desired_outcome}",
        ]
        if intake.incident_date:
            parts.append(f"Date of incident: {intake.incident_date}")
        if intake.key_facts:
            parts.append("Key facts: " + "; ".join(intake.key_facts))
        if intake.previous_attempts:
            parts.append(f"Previous attempts: {intake.previous_attempts}")
        return "\n".join(parts)

    async def research(self, intake: IntakeData) -> ResearchData:
        """
        Run legal research for the given IntakeData.

        Args:
            intake: Structured intake data from IntakeAgent.

        Returns:
            ResearchData with relevant laws, sections, remedies, and recommendations.
        """
        problem_type_str = intake.problem_type.value
        primary_acts = PROBLEM_TYPE_ACTS.get(problem_type_str, PROBLEM_TYPE_ACTS["other"])
        situation_summary = self._build_situation_summary(intake)
        amount_str = f"₹{intake.amount_involved:,.0f}" if intake.amount_involved else "Not specified"

        prompt = RESEARCH_PROMPT_TEMPLATE.format(
            problem_type=problem_type_str.replace("_", " ").title(),
            jurisdiction=intake.jurisdiction,
            situation_summary=situation_summary,
            desired_outcome=intake.desired_outcome,
            amount_involved=amount_str,
            primary_acts="\n".join(f"- {act}" for act in primary_acts),
        )

        logger.info(
            "research_started",
            extra={"problem_type": problem_type_str, "jurisdiction": intake.jurisdiction},
        )

        raw = await self._gemini.generate(prompt)
        raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

        try:
            data = json.loads(raw)
            result = ResearchData(
                relevant_acts=data.get("relevant_acts", []),
                relevant_sections=data.get("relevant_sections", []),
                case_precedents=data.get("case_precedents", []),
                legal_remedies=data.get("legal_remedies", []),
                recommended_document_type=data.get("recommended_document_type", "demand_letter"),
                research_summary=data.get("research_summary", ""),
            )
            logger.info(
                "research_complete",
                extra={
                    "acts": len(result.relevant_acts),
                    "sections": len(result.relevant_sections),
                    "remedies": len(result.legal_remedies),
                },
            )
            return result

        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error("research_parse_failed", extra={"error": str(exc), "raw": raw[:300]})
            return ResearchData(
                relevant_acts=primary_acts[:3],
                relevant_sections=[],
                legal_remedies=["Consult a qualified lawyer for specific legal advice"],
                recommended_document_type="demand_letter",
                research_summary=(
                    f"Based on the problem type ({problem_type_str}), the following acts may apply: "
                    + ", ".join(primary_acts[:2])
                ),
            )


def get_research_agent() -> ResearchAgent:
    """Return a new ResearchAgent instance."""
    return ResearchAgent()
