"""
api/content_refresh.py — Admin-protected endpoints to refresh legal content.

These are called by Cloud Scheduler weekly to refresh:
  - Legal updates (new laws, judgments)
  - Public case showcase (interesting cases)

All endpoints require X-Admin-Key header.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, status

from core.config import get_settings

router = APIRouter(prefix="/api/admin/content", tags=["admin", "content"])
logger = structlog.get_logger()
settings = get_settings()


def _verify_admin(x_admin_key: str = Header(...)) -> None:
    """Verify the X-Admin-Key header."""
    if x_admin_key != settings.admin_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key.",
        )


@router.post("/legal-updates/refresh", dependencies=[Depends(_verify_admin)])
async def refresh_legal_updates(
    country_code: str | None = None,
) -> dict:
    """
    Trigger a legal updates refresh for all countries or a specific one.

    Called weekly by Cloud Scheduler.
    """
    from services.legal_update_service import get_legal_update_service
    svc = get_legal_update_service()

    if country_code:
        count = await svc.refresh_country(country_code)
        result = {country_code: count}
    else:
        result = await svc.refresh_all_countries()

    logger.info("legal_updates_refreshed", result=result)
    return {"success": True, "updates_added": result}


@router.post("/public-cases/refresh", dependencies=[Depends(_verify_admin)])
async def refresh_public_cases(
    country_code: str | None = None,
) -> dict:
    """
    Trigger a public cases refresh for all countries or a specific one.

    Called weekly by Cloud Scheduler.
    """
    from services.case_showcase_service import get_case_showcase_service
    svc = get_case_showcase_service()

    if country_code:
        from core.countries import SUPPORTED_COUNTRIES
        data = SUPPORTED_COUNTRIES.get((country_code or "").upper())
        if not data:
            raise HTTPException(status_code=400, detail=f"Unknown country: {country_code}")
        from services.case_showcase_service import fetch_showcase_cases_for_country
        from services.gemini_service import get_gemini_service
        from services.firebase_service import get_firebase_service
        firebase = get_firebase_service()
        cases = await fetch_showcase_cases_for_country(
            country_code=country_code.upper(),
            country_name=data["name"],
            gemini_service=get_gemini_service(),
        )
        for case in cases:
            doc_ref = firebase.db.collection("public_cases").document()
            doc_ref.set(case)
        result = {country_code: len(cases)}
    else:
        result = await svc.refresh_all_countries()

    logger.info("public_cases_refreshed", result=result)
    return {"success": True, "cases_added": result}


@router.get("/status", dependencies=[Depends(_verify_admin)])
async def get_content_status() -> dict:
    """Get content freshness status for all countries."""
    from services.firebase_service import get_firebase_service
    from core.countries import SUPPORTED_COUNTRIES
    from datetime import datetime, timezone, timedelta

    firebase = get_firebase_service()
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    status_data = {}
    for code, data in SUPPORTED_COUNTRIES.items():
        updates_recent = len(list(
            firebase.db.collection("legal_updates")
            .where("country_code", "==", code)
            .where("fetched_at", ">=", cutoff_7d)
            .limit(1)
            .stream()
        ))
        cases_total = len(list(
            firebase.db.collection("public_cases")
            .where("country_code", "==", code)
            .limit(1)
            .stream()
        ))
        status_data[code] = {
            "name": data["name"],
            "has_recent_updates": updates_recent > 0,
            "has_showcase_cases": cases_total > 0,
        }

    return {"countries": status_data}
