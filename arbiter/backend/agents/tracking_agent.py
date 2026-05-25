"""
tracking_agent.py — Deadline tracking and follow-up agent powered by Google Gemini 2.0 Pro + ADK.

After a legal document is sent, TrackingAgent:
1. Sets a response deadline (typically 30 days)
2. Generates scheduled reminders for the user
3. Suggests next steps if there's no response
4. Decides when to escalate to a lawyer referral
"""
# ─────────────────────────────────────────────────────────────────────────────
# Arbiter ⚖️  ·  Powered by Google Gemini 2.0 Pro  ·  XPRIZE Build with Gemini
# Model: gemini-2.0-pro-exp  ·  Framework: Google Agent Development Kit (ADK)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from models.case import IntakeData, ResearchData
from models.document import DocumentType, LegalDocument
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

TRACKING_SYSTEM_PROMPT = """You are Arbiter's case tracking specialist.

Your job is to create a clear follow-up plan after a user sends a legal document.

Be practical and realistic. Tell the user:
- When to expect a response
- What to do if they get no response
- When to escalate to a lawyer
- What evidence to collect in the meantime

Use simple, supportive language. The user is already stressed.
"""

DEFAULT_DEADLINES: dict[str, int] = {
    "demand_letter": 30,
    "rti_application": 30,
    "consumer_complaint": 45,
    "cease_desist": 15,
    "employment_complaint": 30,
    "legal_notice": 30,
}


class TrackingPlan:
    """The output of the TrackingAgent — a structured follow-up plan."""

    def __init__(
        self,
        response_deadline_date: datetime,
        reminders: list[dict],
        next_steps_if_no_response: list[str],
        next_steps_if_response: list[str],
        escalation_advice: str,
        summary: str,
    ) -> None:
        self.response_deadline_date = response_deadline_date
        self.reminders = reminders
        self.next_steps_if_no_response = next_steps_if_no_response
        self.next_steps_if_response = next_steps_if_response
        self.escalation_advice = escalation_advice
        self.summary = summary


class TrackingAgent:
    """
    Creates follow-up plans and reminders after a legal document is sent.
    """

    def __init__(self) -> None:
        self._gemini = GeminiService(system_instruction=TRACKING_SYSTEM_PROMPT)

    def _get_deadline_days(self, document: LegalDocument) -> int:
        return DEFAULT_DEADLINES.get(document.type.value, 30)

    def _build_reminders(
        self, sent_date: datetime, deadline_date: datetime, user_id: str, case_id: str
    ) -> list[dict]:
        """
        Generate a schedule of reminder notifications.
        Reminders at: Day 7, Day 15, Day 25, and Day 30 (deadline).
        """
        deadline_days = (deadline_date - sent_date).days
        reminder_schedule = []

        checkpoints = [7, 15, min(25, deadline_days - 5), deadline_days]
        messages = [
            "Friendly reminder: You sent a legal notice {days} days ago. Check if the respondent has replied.",
            "2 weeks since your legal notice was sent. No response yet? Keep records of all communication.",
            f"Deadline approaching in {max(5, deadline_days - 25)} days. Prepare your next steps.",
            "DEADLINE REACHED: Your response deadline has passed. Time to decide your next move. Open Arbiter for options.",
        ]

        for i, days in enumerate(checkpoints):
            if days <= 0:
                continue
            remind_at = sent_date + timedelta(days=days)
            reminder_schedule.append({
                "user_id": user_id,
                "case_id": case_id,
                "remind_at": remind_at,
                "message": messages[i].format(days=days),
                "type": "deadline_reminder",
                "sent": False,
            })

        return reminder_schedule

    async def _generate_next_steps(
        self,
        intake: IntakeData,
        research: ResearchData,
        document_type: str,
        deadline_days: int,
    ) -> tuple[list[str], list[str], str]:
        prompt = f"""A user in {intake.jurisdiction} sent a {document_type.replace('_', ' ')} to {intake.respondent.name}.
The deadline for response is {deadline_days} days.
Problem: {intake.desired_outcome}
Amount: {'₹' + str(intake.amount_involved) if intake.amount_involved else 'Not specified'}
Legal remedies available: {', '.join(research.legal_remedies[:3]) if research.legal_remedies else 'As per applicable law'}

Generate practical next steps in JSON:
{{
  "if_no_response": [
    "Step 1 to take if respondent ignores the notice",
    "Step 2...",
    "Step 3..."
  ],
  "if_response": [
    "Step 1 if respondent replies but refuses",
    "Step 2 if they agree to resolve..."
  ],
  "escalation_advice": "One paragraph: when and how to escalate to a lawyer or court"
}}

Be specific to Indian legal system. Name actual courts, commissions, authorities."""

        try:
            data = await self._gemini.generate_structured(
                prompt=prompt,
                expected_keys=["if_no_response", "if_response", "escalation_advice"],
            )
            return (
                data.get("if_no_response", []),
                data.get("if_response", []),
                data.get("escalation_advice", ""),
            )
        except Exception as exc:
            logger.warning("tracking_next_steps_failed", extra={"error": str(exc)})
            authority = research.legal_remedies[0] if research.legal_remedies else "relevant court"
            return (
                [
                    f"File a formal complaint with the {authority}",
                    "Collect all evidence (receipts, screenshots, messages)",
                    "Consult a lawyer if amount exceeds ₹1 lakh",
                ],
                [
                    "If they agree — get it in writing before accepting",
                    "If they refuse — proceed to formal complaint",
                ],
                f"If the matter is not resolved within {deadline_days} days, consult a lawyer or approach the appropriate court/commission in {intake.jurisdiction}.",
            )

    async def create_tracking_plan(
        self,
        document: LegalDocument,
        intake: IntakeData,
        research: ResearchData,
        sent_date: Optional[datetime] = None,
    ) -> TrackingPlan:
        """Create a complete tracking plan for a sent legal document."""
        if sent_date is None:
            sent_date = datetime.utcnow()

        deadline_days = self._get_deadline_days(document)
        deadline_date = sent_date + timedelta(days=deadline_days)

        logger.info(
            "tracking_plan_started",
            extra={"doc_type": document.type.value, "deadline_days": deadline_days, "case_id": document.case_id},
        )

        reminders = self._build_reminders(
            sent_date=sent_date,
            deadline_date=deadline_date,
            user_id=document.user_id,
            case_id=document.case_id,
        )

        no_response_steps, response_steps, escalation = await self._generate_next_steps(
            intake=intake,
            research=research,
            document_type=document.type.value,
            deadline_days=deadline_days,
        )

        summary = (
            f"Your {document.type.value.replace('_', ' ')} has been prepared. "
            f"The respondent ({intake.respondent.name}) has {deadline_days} days to respond "
            f"(deadline: {deadline_date.strftime('%d %B %Y')}). "
            f"Arbiter will send you reminders at key checkpoints."
        )

        logger.info("tracking_plan_complete", extra={"reminders": len(reminders), "case_id": document.case_id})

        return TrackingPlan(
            response_deadline_date=deadline_date,
            reminders=reminders,
            next_steps_if_no_response=no_response_steps,
            next_steps_if_response=response_steps,
            escalation_advice=escalation,
            summary=summary,
        )


def get_tracking_agent() -> TrackingAgent:
    """Return a new TrackingAgent instance."""
    return TrackingAgent()
