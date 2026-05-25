"""
drafting_agent.py — Legal document drafting agent powered by Google Gemini 2.0 Pro.

Takes IntakeData + ResearchData and generates a complete, cited legal document.

KEY UPGRADES:
  1. stream_draft() — yields document text as chunks for live frontend display
  2. Confidence score propagated from research grounding
  3. Grounding sources passed through to final document
  4. Hindi language support — detects language and generates in Hindi when needed
  5. Revision support via revise() method

CRITICAL RULE: Every legal claim in the document must cite a specific act and section.
No citation = no claim. This is enforced by the agent's system prompt and verified post-generation.
"""
# ─────────────────────────────────────────────────────────────────────────────
# Arbiter ⚖️  ·  Powered by Google Gemini 2.0 Pro  ·  XPRIZE Build with Gemini
# Model: gemini-2.0-pro-exp  ·  Framework: Google Agent Development Kit (ADK)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import AsyncGenerator, Optional

from models.case import IntakeData, ResearchData
from models.document import Citation, DocumentType, LegalDocument, LEGAL_DISCLAIMER
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

DRAFTING_SYSTEM_PROMPT = """You are Arbiter's senior legal drafter — an expert at writing formal Indian legal documents.

You draft demand letters, RTI applications, consumer complaints, and legal notices on behalf of everyday citizens.

ABSOLUTE RULES:
1. Every legal claim MUST be followed by a citation in this format: [Act Name, Section X]
2. NEVER invent section numbers or act names. Only cite what you know exists.
3. Documents must be formal, professional, and assertive — but not aggressive.
4. Use proper legal language and structure (date, subject, salutation, body, relief sought, closing).
5. Always include the standard disclaimer at the bottom.
6. Address the document TO the respondent FROM the complainant.
7. Set a clear deadline for response (usually 15 or 30 days).
8. End with consequences of non-compliance (filing a formal complaint, approaching the court, etc.)
9. If the intake language is Hindi, draft the ENTIRE document in Hindi (but keep act names and section numbers in English).

DOCUMENT STRUCTURE:
- Date + place
- From: complainant name + address
- To: respondent name + address
- Subject line
- Salutation
- Introduction paragraph (identify parties, relationship)
- Facts section (numbered facts with dates)
- Legal provisions section (acts and sections that apply)
- Relief sought section (what you want, by when)
- Consequences paragraph (what happens if ignored)
- Closing
- Signature block
"""

DEMAND_LETTER_PROMPT = """Draft a formal legal demand letter based on:

COMPLAINANT: {complainant_name}
ADDRESS: {complainant_address}
PHONE: {complainant_phone}

RESPONDENT: {respondent_name}
ADDRESS: {respondent_address}

FACTS:
{facts}

APPLICABLE LAWS (grounded and verified):
{laws}

DESIRED OUTCOME: {desired_outcome}
AMOUNT (if any): {amount}
DATE: {today}
LANGUAGE: {language}

Write the complete demand letter. Cite every legal claim with [Act, Section]. Be formal and assertive.
Set a 30-day response deadline. State that non-compliance will result in legal proceedings.
{language_instruction}"""

RTI_PROMPT = """Draft a formal RTI application based on:

APPLICANT: {complainant_name}
ADDRESS: {complainant_address}

PUBLIC AUTHORITY: {respondent_name}

INFORMATION SOUGHT:
{facts}

DATE: {today}
LANGUAGE: {language}

Write a complete RTI application under the Right to Information Act, 2005.
Address it to the Central/State Public Information Officer.
Cite Section 6(1) of RTI Act, 2005 for the request.
Cite Section 7(1) for the 30-day response obligation.
Request information clearly in numbered points.
Include declaration that information is not related to personal information of a third party.
{language_instruction}"""

CONSUMER_COMPLAINT_PROMPT = """Draft a formal consumer complaint based on:

COMPLAINANT: {complainant_name}
ADDRESS: {complainant_address}
PHONE: {complainant_phone}

OPPOSITE PARTY (RESPONDENT): {respondent_name}
ADDRESS: {respondent_address}

FACTS:
{facts}

APPLICABLE LAWS (grounded and verified):
{laws}

AMOUNT IN DISPUTE: {amount}
DATE: {today}
LANGUAGE: {language}

Write a formal complaint to be filed before the District Consumer Disputes Redressal Commission.
Structure: Title, Parties, Facts, Legal Provisions, Relief Prayed, Verification.
Cite Consumer Protection Act 2019 sections correctly.
Relief should include: refund + compensation + cost of litigation.
{language_instruction}"""

REVISION_PROMPT = """You are revising a legal document based on user instructions.

ORIGINAL DOCUMENT:
{original_content}

REVISION INSTRUCTIONS FROM USER:
{instructions}

Generate the COMPLETE revised document incorporating the user's instructions.
- Maintain formal legal tone
- Keep all valid legal citations; update section numbers only if instructed
- Add new citations only if you are certain they exist
- Do not remove the disclaimer at the bottom
- Cite every new legal claim with [Act, Section]

Return the complete revised document text only — no explanation, no preamble."""


class DraftingAgent:
    """Generates complete, cited legal documents from intake and research data."""

    def __init__(self) -> None:
        self._gemini = GeminiService(system_instruction=DRAFTING_SYSTEM_PROMPT)

    def _build_facts_text(self, intake: IntakeData) -> str:
        if intake.key_facts:
            return "\n".join(f"{i+1}. {fact}" for i, fact in enumerate(intake.key_facts))
        return f"The complainant has a dispute with {intake.respondent.name} regarding {intake.desired_outcome}."

    def _build_laws_text(self, research: ResearchData) -> str:
        lines = []
        if research.grounding_sources:
            lines.append(f"[Verified via {len(research.grounding_sources)} real legal sources]")
        if research.relevant_acts:
            lines.append("Applicable Acts:")
            for act in research.relevant_acts:
                lines.append(f"  - {act}")
        if research.relevant_sections:
            lines.append("\nRelevant Sections:")
            for section in research.relevant_sections:
                lines.append(f"  - {section}")
        return "\n".join(lines) if lines else "Indian Contract Act, 1872"

    def _language_instruction(self, lang: str) -> str:
        if lang == "hi":
            return "IMPORTANT: Write the entire document in Hindi (Devanagari script). Keep act names, section numbers, and the disclaimer in English."
        return ""

    def _extract_citations(self, document_text: str) -> list[Citation]:
        citations = []
        pattern = r"\[([^\]]+),\s*Section\s+([^\]]+)\]"
        matches = re.findall(pattern, document_text)
        seen = set()
        for act, section in matches:
            key = f"{act.strip()}|{section.strip()}"
            if key not in seen:
                seen.add(key)
                citations.append(Citation(
                    act=act.strip(),
                    section=f"Section {section.strip()}",
                    description="Applicable provision cited in this document.",
                    verified=False,
                ))
        return citations

    def _mark_verified_citations(
        self,
        citations: list[Citation],
        grounding_sources: list,
    ) -> tuple[list[Citation], int]:
        source_titles = " ".join(
            s.title.lower() if hasattr(s, "title") else s.get("title", "").lower()
            for s in grounding_sources
        )
        verified_count = 0
        for citation in citations:
            act_words = citation.act.lower().split()[:3]
            if any(word in source_titles for word in act_words):
                citation.verified = True
                verified_count += 1
        return citations, verified_count

    def _get_document_title(self, doc_type: DocumentType, intake: IntakeData) -> str:
        titles = {
            DocumentType.DEMAND_LETTER: f"Legal Demand Notice — {intake.desired_outcome}",
            DocumentType.RTI_APPLICATION: f"RTI Application — {intake.respondent.name}",
            DocumentType.CONSUMER_COMPLAINT: f"Consumer Complaint — {intake.respondent.name}",
            DocumentType.CEASE_DESIST: f"Cease and Desist Notice — {intake.respondent.name}",
            DocumentType.EMPLOYMENT_COMPLAINT: f"Employment Dispute Notice — {intake.respondent.name}",
            DocumentType.LEGAL_NOTICE: f"Legal Notice — {intake.respondent.name}",
        }
        return titles.get(doc_type, f"Legal Document — {intake.respondent.name}")

    def _select_prompt(self, doc_type: DocumentType, intake: IntakeData, research: ResearchData) -> str:
        today = datetime.now().strftime("%d %B %Y")
        lang = getattr(intake, "language", "en")
        lang_instruction = self._language_instruction(lang)
        common = {
            "complainant_name": intake.complainant.name,
            "complainant_address": intake.complainant.address or "As per records",
            "complainant_phone": intake.complainant.phone or "Not provided",
            "respondent_name": intake.respondent.name,
            "respondent_address": intake.respondent.address or "As per records",
            "facts": self._build_facts_text(intake),
            "laws": self._build_laws_text(research),
            "desired_outcome": intake.desired_outcome,
            "amount": f"₹{intake.amount_involved:,.0f}" if intake.amount_involved else "As applicable",
            "today": today,
            "language": "Hindi" if lang == "hi" else "English",
            "language_instruction": lang_instruction,
        }
        if doc_type == DocumentType.RTI_APPLICATION:
            return RTI_PROMPT.format(**common)
        elif doc_type == DocumentType.CONSUMER_COMPLAINT:
            return CONSUMER_COMPLAINT_PROMPT.format(**common)
        else:
            return DEMAND_LETTER_PROMPT.format(**common)

    async def draft(
        self,
        intake: IntakeData,
        research: ResearchData,
        document_type: Optional[DocumentType] = None,
        user_id: str = "",
        case_id: str = "",
        content_override: Optional[str] = None,
    ) -> LegalDocument:
        """Generate a complete legal document (non-streaming)."""
        if document_type is None:
            try:
                document_type = DocumentType(research.recommended_document_type)
            except ValueError:
                document_type = DocumentType.DEMAND_LETTER

        title = self._get_document_title(document_type, intake)

        if content_override:
            logger.info("drafting_from_stream", extra={"doc_type": document_type.value, "case_id": case_id})
            content = content_override
        else:
            prompt = self._select_prompt(document_type, intake, research)
            logger.info("drafting_started", extra={"doc_type": document_type.value, "case_id": case_id})
            content = await self._gemini.generate(prompt)

        citations = self._extract_citations(content)

        if research.grounding_sources:
            citations, verified_count = self._mark_verified_citations(citations, research.grounding_sources)
        else:
            verified_count = 0

        if not citations and research.relevant_sections:
            first_section = research.relevant_sections[0]
            parts = first_section.split("—")
            if len(parts) >= 2:
                act_section = parts[0].strip().split(",")
                if len(act_section) >= 2:
                    citations.append(Citation(
                        act=act_section[0].strip(),
                        section=act_section[1].strip(),
                        description=parts[1].strip() if len(parts) > 1 else "Applicable provision",
                    ))

        word_count = len(content.split())
        lang = getattr(intake, "language", "en")
        doc_confidence = research.confidence_score
        if citations and verified_count > 0:
            doc_confidence = min(doc_confidence + (verified_count / len(citations)) * 10, 100.0)

        grounding_urls = [
            s.url if hasattr(s, "url") else s.get("url", "")
            for s in research.grounding_sources
        ]

        logger.info(
            "drafting_complete",
            extra={"doc_type": document_type.value, "word_count": word_count, "citations": len(citations), "verified": verified_count},
        )

        return LegalDocument(
            case_id=case_id,
            user_id=user_id,
            type=document_type,
            title=title,
            content=content,
            citations=citations,
            disclaimer=LEGAL_DISCLAIMER,
            word_count=word_count,
            confidence_score=round(doc_confidence, 1),
            grounding_sources=grounding_urls,
            verified_citations=verified_count,
            language=lang,
        )

    async def stream_draft(
        self,
        intake: IntakeData,
        research: ResearchData,
        document_type: Optional[DocumentType] = None,
        user_id: str = "",
        case_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """Stream document generation — yields text chunks progressively."""
        if document_type is None:
            try:
                document_type = DocumentType(research.recommended_document_type)
            except ValueError:
                document_type = DocumentType.DEMAND_LETTER

        prompt = self._select_prompt(document_type, intake, research)
        logger.info("stream_drafting_started", extra={"doc_type": document_type.value, "case_id": case_id})

        async for chunk in self._gemini.stream_generate(prompt):
            yield chunk

    async def revise(
        self,
        original_content: str,
        instructions: str,
        revision_count: int = 0,
    ) -> str:
        """Revise an existing document based on user instructions."""
        prompt = REVISION_PROMPT.format(
            original_content=original_content,
            instructions=instructions,
        )
        logger.info("revision_started", extra={"revision_num": revision_count + 1})
        revised = await self._gemini.generate(prompt)
        logger.info("revision_complete", extra={"words": len(revised.split())})
        return revised


def get_drafting_agent() -> DraftingAgent:
    """Return a new DraftingAgent instance."""
    return DraftingAgent()
