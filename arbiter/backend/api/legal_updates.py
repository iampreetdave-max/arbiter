"""
api/legal_updates.py — Legal updates feed endpoints.

Endpoints:
  GET /api/legal-updates          — Browse recent legal updates (public)
  GET /api/legal-updates/{id}     — Get a specific update
  GET /api/legal-updates/countries — List available countries
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

import structlog

router = APIRouter(prefix="/api/legal-updates", tags=["legal-updates"])
logger = structlog.get_logger()


@router.get("")
async def list_legal_updates(
    country_code: str | None = Query(default=None, description="Filter by country (IN, US, GB, CA, AU)"),
    category: str | None = Query(default=None, description="Filter: legislation | judgment | regulation | advisory"),
    days_back: int = Query(default=30, le=90, description="How many days back to look"),
    limit: int = Query(default=20, le=50),
) -> dict:
    """
    Get recent legal updates for all or a specific country.
    Public endpoint — no authentication required.
    """
    from services.legal_update_service import get_legal_update_service
    svc = get_legal_update_service()

    updates = svc.get_updates(
        country_code=country_code,
        category=category,
        limit=limit,
        days_back=days_back,
    )

    from core.countries import get_supported_country_list
    return {
        "updates": updates,
        "total": len(updates),
        "filters": {
            "country_code": country_code,
            "category": category,
            "days_back": days_back,
        },
        "supported_countries": get_supported_country_list(),
    }


@router.get("/countries")
async def list_supported_countries() -> dict:
    """Return list of supported countries for the country selector."""
    from core.countries import get_supported_country_list
    return {"countries": get_supported_country_list()}
