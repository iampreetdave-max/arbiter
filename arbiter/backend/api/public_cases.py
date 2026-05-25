"""
api/public_cases.py — Public case showcase endpoints.

Endpoints:
  GET /api/public-cases           — Browse showcase cases
  GET /api/public-cases/{id}      — Get a specific case (increments view count)
"""
from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, status

import structlog

router = APIRouter(prefix="/api/public-cases", tags=["public-cases"])
logger = structlog.get_logger()


@router.get("")
async def list_public_cases(
    country_code: str | None = Query(default=None),
    category: str | None = Query(default=None, description="consumer | employment | tenant | civil_rights | landmark | cyber | corporate"),
    landmark_only: bool = Query(default=False),
    limit: int = Query(default=12, le=50),
) -> dict:
    """
    Browse interesting public legal cases (educational content).
    Public endpoint — no auth required.
    """
    from services.case_showcase_service import get_case_showcase_service
    svc = get_case_showcase_service()

    cases = svc.get_cases(
        country_code=country_code,
        category=category,
        landmark_only=landmark_only,
        limit=limit,
    )

    return {
        "cases": cases,
        "total": len(cases),
        "categories": ["consumer", "employment", "tenant", "civil_rights", "landmark", "cyber", "corporate"],
    }


@router.get("/{case_id}")
async def get_public_case(case_id: str) -> dict:
    """Get a single public case by ID. Increments view count."""
    from services.case_showcase_service import get_case_showcase_service
    from services.firebase_service import get_firebase_service

    firebase = get_firebase_service()
    doc = firebase.db.collection("public_cases").document(case_id).get()

    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    d = doc.to_dict()
    if not d.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    d["id"] = doc.id

    # Increment view count asynchronously (non-blocking)
    svc = get_case_showcase_service()
    svc.increment_view(case_id)

    return d
