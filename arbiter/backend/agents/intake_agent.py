"""
intake_agent.py — Conversational intake agent powered by Gemini | Google Gemini 2.0 Pro + ADK

The IntakeAgent drives a multi-turn conversation with the user to
collect all information needed to research and draft their legal document.

Flow:
    1. User sends initial problem description
    2. IntakeAgent asks clarifying questions (jurisdiction, parties, dates, outcome)
    3. When enough info is collected → extracts structured IntakeData
    4. Returns intake_complete=True to trigger ResearchAgent
"""
# ─────────────────────────────────────────────────────────────────────────────
# Arbiter ⚖️  ·  Powered by Google Gemini 2.0 Pro  ·  XPRIZE Build with Gemini
# Model: gemini-2.0-pro-exp  ·  Framework: Google Agent Development Kit (ADK)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from models.case import (
    CaseStatus,
    IntakeData,
    Party,
    ProblemType,
    ResearchData,
)
from services.gemini_service import GeminiService, get_gemini_service

logger = logging.getLogger(__name__)

# ── System prompt for the intake agent ───────────────────────────────────────────
INTAKE_SYSTEM_PROMPT = """You are Arbiter's intake specialist — a warm, empathetic AI legal assistant helping everyday Indians navigate legal problems.

Your job is to collect information about the user's legal problem through a natural conversation.

INFORMATION YOU NEED TO COLLECT:
1. Nature of the problem (tenant dispute, unpaid wages, consumer fraud, RTI, harassment, debt recovery, other)
2. Which Indian state did this happen in? (jurisdiction)
3. Who is the complainant (user) — full name, address if possible
4. Who is the respondent (company/person being complained against) — name, address, contact if known
5. When did the problem start? Key dates?
6. How much money is involved (if applicable)?
7. What outcome does the user want? (refund, apology, stop behaviour, etc.)
8. What evidence does the user have? (receipts, screenshots, emails, contracts)
9. Has the user already tried to resolve this? What happened?

RULES:
- Ask 1-2 questions at a time. Never overwhelm with a long list.
- Be warm and supportive — users are often stressed.
- Use simple language. Avoid legal jargon.
- When you have enough to proceed (at minimum: problem type, jurisdiction, parties, desired outcome), say exactly: "INTAKE_COMPLETE"
- After saying INTAKE_COMPLETE, output a JSON block with the structured data.

LANGUAGE: Respond in English. If user writes in Hindi, respond in Hindi.
"""

# ── Extraction prompt ─────────────────────────────────────────────────────────────
EXTRACTION_PROMPT_TEMPLATE = """Based on this conversation, extract the structured intake data.

Conversation:
{conversation}

Extract and return ONLY valid JSON with this exact structure:
{{
  "problem_type": "tenant_dispute|employment|consumer|rti|harassment|debt_recovery|other",
  "jurisdiction": "Indian state name",
  "complainant": {{
    "name": "full name",
    "address": "address or null",
    "phone": "phone or null",
    "email": "email or null",
    "role": "complainant"
  }},
  "respondent": {{
    "name": "name of person/company",
    "address": "address or null",
    "phone": "phone or null",
    "email": "email or null",
    "role": "respondent"
  }},
  "incident_date": "date string or null",
  "amount_involved": number_or_null,
  "desired_outcome": "what the user wants",
  "key_facts": ["fact 1", "fact 2", "fact 3"],
  "evidence_available": ["evidence 1", "evidence 2"],
  "previous_attempts": "what they tried or null"
}}

If any field is unknown from the conversation, use null. Do not invent information."""


class IntakeAgent:
    """
    Drives multi-turn intake conversation and extracts structured case data.

    Usage:
        agent = IntakeAgent()
        response, complete, intake_data = await agent.process_message(
            user_message="My landlord won't return my deposit",
            conversation_history=[]
        )
    """

    def __init__(self, gemini_service: Optional[GeminiService] = None) -> None:
        """
        Initialise with optional GeminiService (uses singleton by default).

        Args:
            gemini_service: Injected GeminiService for testing.
        """
        self._gemini = gemini_service or get_gemini_service()
        self._intake_gemini = GeminiService(system_instruction=INTAKE_SYSTEM_PROMPT)

    def _build_chat_history(self, conversation_history: list[dict]) -> list[dict]:
        """
        Convert stored conversation history to Gemini chat format.

        Args:
            conversation_history: List of {"role": "user"|"assistant", "content": str}

        Returns:
            Gemini-formatted history: [{"role": "user"|"model", "parts": [str]}]
        """
        gemini_history = []
        for msg in conversation_history:
            role = "model" if msg.get("role") == "assistant" else "user"
            gemini_history.append({
                "role": role,
                "parts": [msg.get("content", "")]
            })
        return gemini_history

    def _is_intake_complete(self, response_text: str) -> bool:
        """Check if the agent has signalled intake completion."""
        return "INTAKE_COMPLETE" in response_text

    async def _extract_intake_data(self, conversation_history: list[dict]) -> Optional[IntakeData]:
        """
        Extract structured IntakeData from completed conversation.

        Args:
            conversation_history: Full conversation history.

        Returns:
            IntakeData if extraction succeeds, None otherwise.
        """
        conversation_text = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history
        )

        extraction_prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            conversation=conversation_text
        )

        try:
            raw = await self._gemini.generate(extraction_prompt)
            raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            data = json.loads(raw)

            complainant = Party(
                name=data.get("complainant", {}).get("name", "Unknown"),
                address=data.get("complainant", {}).get("address"),
                phone=data.get("complainant", {}).get("phone"),
                email=data.get("complainant", {}).get("email"),
                role="complainant",
            )
            respondent = Party(
                name=data.get("respondent", {}).get("name", "Unknown"),
                address=data.get("respondent", {}).get("address"),
                phone=data.get("respondent", {}).get("phone"),
                email=data.get("respondent", {}).get("email"),
                role="respondent",
            )

            problem_type_str = data.get("problem_type", "other")
            try:
                problem_type = ProblemType(problem_type_str)
            except ValueError:
                problem_type = ProblemType.OTHER

            return IntakeData(
                problem_type=problem_type,
                jurisdiction=data.get("jurisdiction", "India"),
                complainant=complainant,
                respondent=respondent,
                incident_date=data.get("incident_date"),
                amount_involved=data.get("amount_involved"),
                desired_outcome=data.get("desired_outcome", "Resolve dispute"),
                key_facts=data.get("key_facts", []),
                evidence_available=data.get("evidence_available", []),
                previous_attempts=data.get("previous_attempts"),
            )

        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("intake_extraction_failed", extra={"error": str(exc)})
            return None

    async def process_message(
        self,
        user_message: str,
        conversation_history: list[dict],
    ) -> tuple[str, bool, Optional[IntakeData]]:
        """
        Process a user message and advance the intake conversation.

        Args:
            user_message: Latest message from the user.
            conversation_history: All prior messages in this case.

        Returns:
            Tuple of:
                - agent_response (str): Arbiter's reply to show the user
                - intake_complete (bool): True when all info collected
                - intake_data (Optional[IntakeData]): Structured data when complete
        """
        gemini_history = self._build_chat_history(conversation_history)

        response_text = await self._intake_gemini.generate(
            prompt=user_message,
            chat_history=gemini_history,
        )

        intake_complete = self._is_intake_complete(response_text)
        intake_data = None

        display_response = re.sub(r"INTAKE_COMPLETE", "", response_text)
        display_response = re.sub(r"\{[\s\S]*\}", "", display_response).strip()

        if intake_complete:
            full_history = conversation_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response_text},
            ]
            intake_data = await self._extract_intake_data(full_history)

            if not display_response:
                display_response = (
                    "Thank you — I have all the information I need. "
                    "I'm now researching the applicable laws for your case. "
                    "This will take just a moment..."
                )

            logger.info("intake_complete", extra={"has_data": intake_data is not None})
        else:
            logger.info("intake_in_progress", extra={"history_len": len(conversation_history)})

        return display_response, intake_complete, intake_data


def get_intake_agent() -> IntakeAgent:
    """Return a new IntakeAgent instance (stateless, safe to create per request)."""
    return IntakeAgent()
