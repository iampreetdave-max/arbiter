"""
admin.py — Internal admin API endpoints.

All require a secret admin key (X-Admin-Key header) instead of Firebase auth.

Endpoints:
  GET  /api/admin/health/full        → Deep health check (all services)
  GET  /api/admin/metrics            → Usage analytics and cost summary
  GET  /api/admin/compliance         → Compliance status overview
  POST /api/admin/backup             → Trigger Firestore backup to GCS
  GET  /api/admin/cache/stats        → Cache hit rates
  POST /api/admin/cache/clear        → Clear research cache
  GET  /api/admin/security-events    → Recent suspicious activity log
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_key(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> str:
    """Verify the admin secret key from the request header."""
    settings = get_settings()
    expected = settings.admin_secret_key
    if not expected or expected == "change-me-in-production":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin key not configured on server.")
    if x_admin_key != expected:
        logger.warning("invalid_admin_key_attempt")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key.")
    return x_admin_key


AdminAuth = Annotated[str, Depends(verify_admin_key)]


@router.get("/health/full")
async def full_health_check(admin: AdminAuth) -> dict:
    """Deep health check — verifies all external service connections."""
    checks: dict = {}
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        fb._db.collection("_health").limit(1).get()
        checks["firestore"] = {"status": "ok"}
    except Exception as e:
        checks["firestore"] = {"status": "error", "detail": str(e)}
    try:
        from services.gemini_service import get_gemini_service
        gs = get_gemini_service()
        checks["gemini"] = {"status": "ok", "model": gs._model_name}
    except Exception as e:
        checks["gemini"] = {"status": "error", "detail": str(e)}
    try:
        from services.razorpay_service import get_razorpay_service
        get_razorpay_service()
        checks["razorpay"] = {"status": "ok"}
    except Exception as e:
        checks["razorpay"] = {"status": "error", "detail": str(e)}
    try:
        from services.storage_service import get_storage_service
        get_storage_service()
        checks["gcs"] = {"status": "ok"}
    except Exception as e:
        checks["gcs"] = {"status": "error", "detail": str(e)}
    try:
        from core.cache import research_cache
        checks["cache"] = {"status": "ok", **research_cache.stats}
    except Exception as e:
        checks["cache"] = {"status": "error", "detail": str(e)}
    all_ok = all(v.get("status") == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "services": checks, "checked_at": datetime.utcnow().isoformat()}


@router.get("/metrics")
async def get_metrics(admin: AdminAuth) -> dict:
    """Returns usage analytics and Gemini cost summary."""
    from core.monitoring import get_metrics_summary
    return {"metrics": get_metrics_summary(), "generated_at": datetime.utcnow().isoformat()}


@router.get("/compliance")
async def get_compliance_status(admin: AdminAuth) -> dict:
    """Returns Indian regulatory compliance status."""
    from core.compliance import get_compliance_metadata
    return get_compliance_metadata()


@router.post("/backup")
async def trigger_backup(admin: AdminAuth) -> dict:
    """Trigger a Firestore database backup to GCS."""
    from services.backup_service import get_backup_service
    settings = get_settings()
    backup_bucket = getattr(settings, "backup_bucket_name", settings.gcs_bucket_name)
    backup_svc = get_backup_service()
    result = await backup_svc.trigger_firestore_backup(backup_bucket)
    logger.info("manual_backup_triggered", extra=result)
    return result


@router.get("/cache/stats")
async def cache_stats(admin: AdminAuth) -> dict:
    """Returns research cache hit/miss statistics."""
    from core.cache import research_cache, revision_cache
    return {"research_cache": research_cache.stats, "revision_cache": revision_cache.stats}


@router.post("/cache/clear")
async def clear_cache(admin: AdminAuth) -> dict:
    """Clear the research cache (use after Indian law updates)."""
    from core.cache import research_cache
    size_before = research_cache.stats["size"]
    research_cache.clear()
    return {"status": "cleared", "entries_removed": size_before, "cleared_at": datetime.utcnow().isoformat()}


@router.get("/security-events")
async def get_security_events(admin: AdminAuth, limit: int = 50) -> dict:
    """Returns recent suspicious activity events for review."""
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        query = fb._db.collection("security_events").order_by("timestamp", direction="DESCENDING").limit(min(limit, 100))
        docs = query.stream()
        events = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            events.append(data)
        return {"events": events, "count": len(events)}
    except Exception as e:
        return {"events": [], "count": 0, "error": str(e)}
