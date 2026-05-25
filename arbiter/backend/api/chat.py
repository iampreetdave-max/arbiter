"""
api/chat.py — Intake conversation endpoints.

Provides a two-endpoint chat flow:
  POST /cases/chat         — Start a new case via conversation (creates case)
  POST /cases/{id}/message — Continue an existing case's conversation

The intake agent uses Google Gemini to:
  1. Ask clarifying questions about the user's legal problem
  2. Gather jurisdiction, parties, facts, relief sought
  3. Identify the right document type
  4. Signal when it has enough info to generate the document
"""
from __future__ import annotations

import json
import re
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.security import get_current_user
from services.firebase_service import get_firebase_service
from services.gemini_service import get_gemini_service

router = APIRouter(tags=["chat"])
logger = structlog.get_logger()

# ── Request / response models ─────────────────────────────────────────────────────────────────────────────────────

class ChatStartRequest(BaseModel):
    """First message — creates a new case and starts the intake."""
    message: str


class ChatMessageRequest(BaseModel):
    """Follow-up message in an ongoing intake conversation."""
    message: str


class ChatResponse(BaseModel):
    """Unified response for both chat endpoints."""
    response: str
    case_id: str
    ready_to_generate: bool = False
    suggested_document_type: str | None = None
    updated_case: dict[str, Any] | None = None


# ── System prompt ───────────────────────────────────────────────────────────────────────────────────────────

INTAKE_SYSTEM_PROMPT = """You are Arbiter, an AI legal assistant specialising in Indian law.
Your job is to gather information from users about their legal problem and help them get the right legal document.

DOCUMENT TYPES you can draft:
- demand_letter: For unpaid dues, deposit refunds, salary claims, debt recovery
- legal_notice: Formal notice before litigation — works for most disputes
- rti_application: Right to Information requests to government bodies
- consumer_complaint: Complaints to Consumer Disputes Redressal Commission
- cease_and_desist: Stop illegal/harassing activity
- employment_complaint: Labour court / Labour Commissioner complaint

INTAKE FLOW:
1. Ask the user to briefly describe their problem (they may have already done this)
2. Ask for: (a) jurisdiction/city, (b) name of opposing party, (c) key dates and amounts, (d) what outcome they want
3. Once you have all four pieces of information, output a JSON block at the END of your message:

<intake_complete>
{
  "ready_to_generate": true,
  "suggested_document_type": "<type>",
  "title": "<short 5-8 word case title>",
  "facts": "<2-3 sentence summary of facts>",
  "opposing_party": "<name>",
  "jurisdiction": "<city/state>",
  "relief_sought": "<what the user wants>"
}
</intake_complete>

RULES:
- Ask one follow-up question at a time — do not overwhelm the user
- Be empathetic but professional
- Always respond in the same language the user uses (English or Hindi)
- Never give legal advice — only help draft documents
- Keep responses concise (under 120 words) except for the final intake_complete block
- Never mention the intake_complete JSON to the user — it is a machine-readable signal
"""


def _extract_intake_complete(text: str) -> dict | None:
    """Extract the <intake_complete> JSON block from the model's response."""
    match = re.search(r"<intake_complete>(.*?)</intake_complete>", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None


def _strip_intake_tag(text: str) -> str:
    """Remove the machine-readable tag before sending the response to the user."""
    return re.sub(r"<intake_complete>.*?</intake_complete>", "", text, flags=re.DOTALL).strip()


# ── Endpoints ──────────────────────────────────────────────────────────────────────────────────────────────

@router.post("/cases/chat", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def start_chat(
    body: ChatStartRequest,
    current_user: dict = Depends(get_current_user),
) -> ChatResponse:
    """
    Start an intake conversation — creates a new case and returns the AI's first response.

    The frontend calls this on the user's very first message.
    A case is created in Firestore with status='intake' and the conversation begins.
    """
    firebase = get_firebase_service()
    gemini   = get_gemini_service()

    # Build conversation with system prompt + user's opening message
    conversation = [
        {"role": "user",  "parts": [INTAKE_SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Understood. I will follow the intake flow."]},
        {"role": "user",  "parts": [body.message]},
    ]

    try:
        raw_response = await gemini.chat(conversation)
    except Exception as exc:
        logger.error("gemini_chat_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again.",
        )

    intake_data = _extract_intake_complete(raw_response)
    clean_response = _strip_intake_tag(raw_response)

    # Create the case in Firestore
    case_payload: dict[str, Any] = {
        "user_id":      current_user["uid"],
        "problem_type": "tenant_dispute",        # default; will be updated when intake completes
        "title":        body.message[:60] + ("…" if len(body.message) > 60 else ""),
        "description":  body.message,
        "status":       "intake",
        "chat_history": [
            {"role": "user",      "content": body.message},
            {"role": "assistant", "content": clean_response},
        ],
    }

    if intake_data:
        case_payload.update({
            "status":       "draft_ready" if intake_data.get("ready_to_generate") else "intake",
            "title":        intake_data.get("title", case_payload["title"]),
            "facts":        intake_data.get("facts", ""),
            "opposing_party": intake_data.get("opposing_party", ""),
            "jurisdiction": intake_data.get("jurisdiction", ""),
            "relief_sought": intake_data.get("relief_sought", ""),
            "problem_type": _map_doc_type_to_problem(intake_data.get("suggested_document_type", "")),
        })

    case = firebase.create_case(case_payload)

    logger.info("chat_case_created", case_id=case["id"], user_id=current_user["uid"])

    return ChatResponse(
        response=clean_response,
        case_id=case["id"],
        ready_to_generate=bool(intake_data and intake_data.get("ready_to_generate")),
        suggested_document_type=intake_data.get("suggested_document_type") if intake_data else None,
        updated_case=case,
    )


@router.post("/cases/{case_id}/message", response_model=ChatResponse)
async def send_message(
    case_id: str,
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
) -> ChatResponse:
    """
    Send a follow-up message in an existing intake conversation.

    Retrieves chat history from the case, appends the new message,
    sends to Gemini, and updates the case in Firestore.
    """
    firebase = get_firebase_service()
    gemini   = get_gemini_service()

    # Load the case
    case = firebase.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if case["user_id"] != current_user["uid"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Rebuild conversation from history
    history: list[dict] = case.get("chat_history", [])
    conversation: list[dict] = [
        {"role": "user",  "parts": [INTAKE_SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Understood. I will follow the intake flow."]},
    ]
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        conversation.append({"role": role, "parts": [msg["content"]]})
    conversation.append({"role": "user", "parts": [body.message]})

    try:
        raw_response = await gemini.chat(conversation)
    except Exception as exc:
        logger.error("gemini_chat_failed", case_id=case_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again.",
        )

    intake_data    = _extract_intake_complete(raw_response)
    clean_response = _strip_intake_tag(raw_response)

    # Update chat history
    history.append({"role": "user",      "content": body.message})
    history.append({"role": "assistant", "content": clean_response})

    update_payload: dict[str, Any] = {"chat_history": history}

    if intake_data and intake_data.get("ready_to_generate"):
        update_payload.update({
            "status":         "draft_ready",
            "title":          intake_data.get("title", case.get("title", "")),
            "facts":          intake_data.get("facts", ""),
            "opposing_party": intake_data.get("opposing_party", ""),
            "jurisdiction":   intake_data.get("jurisdiction", ""),
            "relief_sought":  intake_data.get("relief_sought", ""),
            "problem_type":   _map_doc_type_to_problem(intake_data.get("suggested_document_type", "")),
        })

    updated_case = firebase.update_case(case_id, update_payload)

    logger.info(
        "chat_message_sent",
        case_id=case_id,
        ready=bool(intake_data and intake_data.get("ready_to_generate")),
    )

    return ChatResponse(
        response=clean_response,
        case_id=case_id,
        ready_to_generate=bool(intake_data and intake_data.get("ready_to_generate")),
        suggested_document_type=intake_data.get("suggested_document_type") if intake_data else None,
        updated_case=updated_case,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────────────────────────────────────

def _map_doc_type_to_problem(doc_type: str) -> str:
    """Map document_type to the closest problem_type enum value."""
    mapping = {
        "demand_letter":       "debt_recovery",
        "legal_notice":        "tenant_dispute",
        "rti_application":     "rti",
        "consumer_complaint":  "consumer",
        "cease_and_desist":    "harassment",
        "employment_complaint":"employment",
    }
    return mapping.get(doc_type, "tenant_dispute")
