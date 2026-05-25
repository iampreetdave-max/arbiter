"""
cases.py — FastAPI routes for legal case management.

Endpoints:
    POST /api/cases/start        → Start new case (begins intake)
    GET  /api/cases/{case_id}    → Get case details
    POST /api/cases/{case_id}/message → Continue intake conversation
    POST /api/cases/{case_id}/generate → Trigger document generation
    GET  /api/cases/             → List user's cases
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from agents.intake_agent import get_intake_agent
from agents.research_agent import get_research_agent
from core.security import CurrentUser
from models.case import (
    CaseCreate,
    CaseListResponse,
    CaseMessage,
    CaseResponse,
    CaseStatus,
    ConversationMessage,
)
from models.document import DocumentGenerateRequest
from services.firebase_service import FirebaseService, get_firebase_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("/start", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def start_case(
    body: CaseCreate,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> CaseResponse:
    """
    Start a new legal case.

    Creates a case record, runs the first IntakeAgent turn,
    and returns Arbiter's opening question.
    """
    intake_agent = get_intake_agent()

    response_text, intake_complete, intake_data = await intake_agent.process_message(
        user_message=body.initial_message,
        conversation_history=[],
    )

    conversation = [
        ConversationMessage(role="user", content=body.initial_message),
        ConversationMessage(role="assistant", content=response_text),
    ]

    case_data: dict = {
        "user_id": user.uid,
        "status": CaseStatus.INTAKE.value,
        "conversation_history": [m.model_dump(mode="json") for m in conversation],
        "intake_complete": intake_complete,
    }

    if intake_complete and intake_data:
        case_data["status"] = CaseStatus.RESEARCH.value
        case_data["problem_type"] = intake_data.problem_type.value
        case_data["jurisdiction"] = intake_data.jurisdiction
        case_data["intake_data"] = intake_data.model_dump(mode="json")

    case_id = firebase.create_case(case_data)
    logger.info("case_started", extra={"case_id": case_id, "user_id": user.uid})

    return CaseResponse(
        id=case_id,
        user_id=user.uid,
        status=CaseStatus(case_data["status"]),
        problem_type=intake_data.problem_type if intake_data else None,
        jurisdiction=intake_data.jurisdiction if intake_data else None,
        intake_data=intake_data,
        conversation_history=conversation,
        intake_complete=intake_complete,
        next_message=response_text,
    )


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> CaseListResponse:
    """Return all cases for the authenticated user."""
    cases_raw = firebase.get_user_cases(user.uid)
    cases = [_raw_to_response(c) for c in cases_raw]
    return CaseListResponse(cases=cases, total=len(cases))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> CaseResponse:
    """Get a specific case by ID."""
    case = firebase.get_case(case_id)
    _assert_case_access(case, case_id, user.uid)
    return _raw_to_response(case)


@router.post("/{case_id}/message", response_model=CaseResponse)
async def send_message(
    case_id: str,
    body: CaseMessage,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> CaseResponse:
    """
    Continue the intake conversation.

    Sends a user message to the IntakeAgent and returns the next response.
    When intake is complete, automatically triggers legal research.
    """
    case = firebase.get_case(case_id)
    _assert_case_access(case, case_id, user.uid)

    if case.get("status") not in (CaseStatus.INTAKE.value,):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This case is no longer in intake phase.",
        )

    history = case.get("conversation_history", [])
    intake_agent = get_intake_agent()

    response_text, intake_complete, intake_data = await intake_agent.process_message(
        user_message=body.message,
        conversation_history=history,
    )

    firebase.append_conversation_message(case_id, "user", body.message)
    firebase.append_conversation_message(case_id, "assistant", response_text)

    updates: dict = {}
    if intake_complete and intake_data:
        updates["status"] = CaseStatus.RESEARCH.value
        updates["intake_complete"] = True
        updates["problem_type"] = intake_data.problem_type.value
        updates["jurisdiction"] = intake_data.jurisdiction
        updates["intake_data"] = intake_data.model_dump(mode="json")

        research_agent = get_research_agent()
        research_data = await research_agent.research(intake_data)
        updates["research_data"] = research_data.model_dump(mode="json")
        updates["status"] = CaseStatus.DRAFTING.value

    if updates:
        firebase.update_case(case_id, updates)

    refreshed = firebase.get_case(case_id)
    response = _raw_to_response(refreshed)
    response.next_message = response_text
    return response


@router.post("/{case_id}/generate", response_model=dict)
async def generate_document(
    case_id: str,
    body: DocumentGenerateRequest,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> dict:
    """
    Trigger document generation for a completed intake case.

    Returns the document ID. Full document is in /api/documents/{id}.
    """
    from agents.drafting_agent import get_drafting_agent
    from models.case import IntakeData, ResearchData

    case = firebase.get_case(case_id)
    _assert_case_access(case, case_id, user.uid)

    if not case.get("intake_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case intake is not complete yet.",
        )

    intake_data = IntakeData(**case["intake_data"])
    research_data = ResearchData(**case["research_data"]) if case.get("research_data") else None

    if not research_data:
        research_agent = get_research_agent()
        research_data = await research_agent.research(intake_data)

    drafting_agent = get_drafting_agent()
    document = await drafting_agent.draft(
        intake=intake_data,
        research=research_data,
        document_type=body.document_type,
        user_id=user.uid,
        case_id=case_id,
    )

    doc_id = firebase.create_document(document.model_dump(mode="json"))
    firebase.update_case(case_id, {"status": CaseStatus.COMPLETE.value})

    logger.info("document_generated", extra={"doc_id": doc_id, "case_id": case_id})
    return {"document_id": doc_id, "case_id": case_id, "status": "generated"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _assert_case_access(case: dict | None, case_id: str, user_id: str) -> None:
    """Raise 404/403 if case doesn't exist or doesn't belong to user."""
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if case.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")


def _raw_to_response(raw: dict) -> CaseResponse:
    """Convert raw Firestore dict to CaseResponse."""
    from models.case import IntakeData, ResearchData

    intake_data = None
    if raw.get("intake_data"):
        try:
            intake_data = IntakeData(**raw["intake_data"])
        except Exception:
            pass

    research_data = None
    if raw.get("research_data"):
        try:
            research_data = ResearchData(**raw["research_data"])
        except Exception:
            pass

    return CaseResponse(
        id=raw.get("id", ""),
        user_id=raw.get("user_id", ""),
        status=CaseStatus(raw.get("status", CaseStatus.INTAKE.value)),
        problem_type=raw.get("problem_type"),
        jurisdiction=raw.get("jurisdiction"),
        intake_data=intake_data,
        research_data=research_data,
        conversation_history=raw.get("conversation_history", []),
        intake_complete=raw.get("intake_complete", False),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )
