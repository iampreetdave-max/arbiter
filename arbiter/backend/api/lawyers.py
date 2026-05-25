"""
api/lawyers.py — Lawyer registration and case matching endpoints.

Endpoints:
  POST /api/lawyers/register       — Register as a lawyer (creates profile)
  GET  /api/lawyers/me             — Get own lawyer profile
  PUT  /api/lawyers/me             — Update own lawyer profile
  GET  /api/lawyers/me/cases       — Get cases matched to me (lawyer dashboard)
  POST /api/lawyers/me/cases/{match_id}/respond — Accept or decline a case
  POST /api/cases/{case_id}/escalate-to-lawyer  — User requests lawyer escalation
  GET  /api/lawyers                — Browse verified lawyers (public)
  GET  /api/lawyers/{id}           — Get a specific lawyer's public profile
"""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.security import get_current_user
from models.lawyer import (
    LawyerCaseMatch,
    LawyerMatchResponse,
    LawyerRegisterRequest,
    LawyerResponse,
    LawyerStatus,
    LawyerUpdateRequest,
    CaseMatchUpdateRequest,
)
from services.firebase_service import get_firebase_service
from services.lawyer_matching_service import get_lawyer_matching_service

router = APIRouter(prefix="/api/lawyers", tags=["lawyers"])
logger = structlog.get_logger()

# ── Private (lawyer's own profile) ─────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_lawyer(
    body: LawyerRegisterRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Register as a lawyer service provider.

    Creates a lawyer profile with status=PENDING (requires admin verification).
    A user can only have one lawyer profile.
    """
    firebase = get_firebase_service()
    user_id = current_user["uid"]

    existing = firebase.db.collection("lawyers").where("user_id", "==", user_id).limit(1).stream()
    if any(True for _ in existing):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a lawyer profile. Use PUT /api/lawyers/me to update it.",
        )

    from core.countries import is_supported
    if not is_supported(body.country_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Country '{body.country_code}' is not yet supported. Supported: IN, US, GB, CA, AU",
        )

    from datetime import datetime, timezone
    profile_data = {
        "user_id": user_id,
        "full_name": body.full_name,
        "bar_registration_number": body.bar_registration_number,
        "country_code": body.country_code.upper(),
        "jurisdiction": body.jurisdiction,
        "specialties": [s.value for s in body.specialties],
        "years_of_experience": body.years_of_experience,
        "languages": body.languages,
        "available_for_pro_bono": body.available_for_pro_bono,
        "status": LawyerStatus.PENDING.value,
        "bio": body.bio,
        "contact_email": body.contact_email,
        "contact_phone": body.contact_phone,
        "website_url": body.website_url,
        "cases_received": 0,
        "cases_accepted": 0,
        "cases_resolved": 0,
        "rating": 0.0,
        "rating_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    doc_ref = firebase.db.collection("lawyers").document()
    doc_ref.set(profile_data)

    logger.info("lawyer_registered", user_id=user_id, name=body.full_name, country=body.country_code)
    return {
        "id": doc_ref.id,
        **profile_data,
        "message": "Registration submitted. An admin will verify your Bar registration number within 24–48 hours.",
    }


@router.get("/me")
async def get_my_lawyer_profile(current_user: dict = Depends(get_current_user)) -> dict:
    """Get the authenticated user's lawyer profile."""
    firebase = get_firebase_service()
    docs = list(
        firebase.db.collection("lawyers")
        .where("user_id", "==", current_user["uid"])
        .limit(1)
        .stream()
    )
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No lawyer profile found. Register at POST /api/lawyers/register",
        )
    d = docs[0].to_dict()
    d["id"] = docs[0].id
    return d


@router.put("/me")
async def update_my_lawyer_profile(
    body: LawyerUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Update the authenticated lawyer's profile."""
    firebase = get_firebase_service()
    docs = list(
        firebase.db.collection("lawyers")
        .where("user_id", "==", current_user["uid"])
        .limit(1)
        .stream()
    )
    if not docs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer profile not found.")

    doc_ref = docs[0].reference
    from datetime import datetime, timezone
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if body.specialties is not None:
        update_data["specialties"] = [s.value for s in body.specialties]
    if body.available_for_pro_bono is not None:
        update_data["available_for_pro_bono"] = body.available_for_pro_bono
    if body.bio is not None:
        update_data["bio"] = body.bio
    if body.contact_phone is not None:
        update_data["contact_phone"] = body.contact_phone
    if body.website_url is not None:
        update_data["website_url"] = body.website_url
    if body.languages is not None:
        update_data["languages"] = body.languages

    doc_ref.update(update_data)
    d = doc_ref.get().to_dict()
    d["id"] = docs[0].id
    return d


@router.get("/me/cases")
async def get_my_matched_cases(
    status_filter: str | None = Query(default=None, description="Filter: pending | accepted | declined | completed"),
    limit: int = Query(default=20, le=50),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get cases matched to this lawyer (lawyer dashboard feed)."""
    firebase = get_firebase_service()
    matching_svc = get_lawyer_matching_service()

    docs = list(
        firebase.db.collection("lawyers")
        .where("user_id", "==", current_user["uid"])
        .limit(1)
        .stream()
    )
    if not docs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer profile not found.")

    lawyer_id = docs[0].id
    lawyer_data = docs[0].to_dict()

    if lawyer_data.get("status") != LawyerStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your profile is {lawyer_data.get('status')}. Only verified lawyers can view matched cases.",
        )

    matches = await matching_svc.get_lawyer_matches(
        lawyer_id=lawyer_id,
        status_filter=status_filter,
        limit=limit,
    )

    return {"matches": matches, "total": len(matches), "lawyer_id": lawyer_id}


@router.post("/me/cases/{match_id}/respond")
async def respond_to_case_match(
    match_id: str,
    body: CaseMatchUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Lawyer accepts or declines a case match."""
    firebase = get_firebase_service()
    matching_svc = get_lawyer_matching_service()

    docs = list(
        firebase.db.collection("lawyers")
        .where("user_id", "==", current_user["uid"])
        .limit(1)
        .stream()
    )
    if not docs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer profile not found.")

    lawyer_id = docs[0].id

    if body.action not in ("accept", "decline"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action must be 'accept' or 'decline'",
        )

    result = await matching_svc.respond_to_match(
        match_id=match_id,
        lawyer_id=lawyer_id,
        action=body.action,
        notes=body.notes,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found or you don't have access to it.",
        )

    logger.info("case_match_responded", match_id=match_id, action=body.action, lawyer_id=lawyer_id)
    return result


# ── Case escalation (user-facing) ───────────────────────────────────────────────

escalate_router = APIRouter(prefix="/api/cases", tags=["lawyers"])


@escalate_router.post("/{case_id}/escalate-to-lawyer")
async def escalate_case_to_lawyer(
    case_id: str,
    current_user: dict = Depends(get_current_user),
) -> LawyerMatchResponse:
    """
    User requests lawyer escalation for a case.

    Finds the best matching lawyer, creates a match record,
    and notifies the lawyer.
    """
    firebase = get_firebase_service()
    matching_svc = get_lawyer_matching_service()

    case = firebase.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if case["user_id"] != current_user["uid"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    country_code = case.get("country_code", "IN")

    best_lawyer = await matching_svc.find_best_match(
        case_id=case_id,
        case_data=case,
        country_code=country_code,
    )

    if not best_lawyer:
        return LawyerMatchResponse(
            matched=False,
            message=(
                "No matching lawyers are available in your region right now. "
                "We've noted your request and will notify you when one is available."
            ),
        )

    match = await matching_svc.create_match(
        case_id=case_id,
        lawyer_id=best_lawyer["id"],
        user_id=current_user["uid"],
        case_data=case,
        match_score=best_lawyer["match_score"],
    )

    firebase.update_case(case_id, {"status": "escalated", "escalated_to_lawyer_id": best_lawyer["id"]})

    lawyer_response = LawyerResponse(
        id=best_lawyer["id"],
        full_name=best_lawyer["full_name"],
        country_code=best_lawyer["country_code"],
        jurisdiction=best_lawyer["jurisdiction"],
        specialties=best_lawyer["specialties"],
        years_of_experience=best_lawyer["years_of_experience"],
        languages=best_lawyer.get("languages", ["en"]),
        available_for_pro_bono=best_lawyer.get("available_for_pro_bono", False),
        status=LawyerStatus(best_lawyer["status"]),
        bio=best_lawyer["bio"],
        cases_resolved=best_lawyer.get("cases_resolved", 0),
        rating=best_lawyer.get("rating", 0.0),
        rating_count=best_lawyer.get("rating_count", 0),
    )

    logger.info("case_escalated", case_id=case_id, lawyer_id=best_lawyer["id"])

    return LawyerMatchResponse(
        matched=True,
        lawyer=lawyer_response,
        match_id=match["id"],
        message=(
            f"Your case has been matched with {best_lawyer['full_name']}, "
            f"a {best_lawyer.get('years_of_experience', 0)}-year specialist "
            f"in {', '.join(best_lawyer.get('specialties', [])[:2])}. "
            f"They will review your case within 24 hours."
        ),
    )


# ── Public lawyer directory ────────────────────────────────────────────────────────

@router.get("")
async def list_lawyers(
    country_code: str | None = Query(default=None),
    specialty: str | None = Query(default=None),
    pro_bono_only: bool = Query(default=False),
    limit: int = Query(default=20, le=50),
) -> dict:
    """Browse verified lawyers (public endpoint — no auth required)."""
    firebase = get_firebase_service()

    query = firebase.db.collection("lawyers").where("status", "==", "verified")
    if country_code:
        query = query.where("country_code", "==", country_code.upper())
    if pro_bono_only:
        query = query.where("available_for_pro_bono", "==", True)

    docs = query.limit(limit).stream()
    lawyers = []
    for doc in docs:
        d = doc.to_dict()
        if specialty and specialty not in d.get("specialties", []):
            continue
        lawyers.append({
            "id": doc.id,
            "full_name": d["full_name"],
            "country_code": d.get("country_code"),
            "jurisdiction": d.get("jurisdiction"),
            "specialties": d.get("specialties", []),
            "years_of_experience": d.get("years_of_experience", 0),
            "available_for_pro_bono": d.get("available_for_pro_bono", False),
            "bio": d.get("bio", "")[:200] + "..." if len(d.get("bio", "")) > 200 else d.get("bio", ""),
            "rating": d.get("rating", 0.0),
            "rating_count": d.get("rating_count", 0),
            "cases_resolved": d.get("cases_resolved", 0),
            "languages": d.get("languages", ["en"]),
        })

    return {"lawyers": lawyers, "total": len(lawyers)}


@router.get("/{lawyer_id}")
async def get_lawyer(lawyer_id: str) -> dict:
    """Get a specific lawyer's public profile."""
    firebase = get_firebase_service()
    doc = firebase.db.collection("lawyers").document(lawyer_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer not found.")
    d = doc.to_dict()
    if d.get("status") != "verified":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer not found.")
    d["id"] = doc.id
    d.pop("user_id", None)
    d.pop("contact_email", None)
    d.pop("contact_phone", None)
    return d
