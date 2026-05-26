""" 
admin.py — Internal admin API endpoints.

These endpoints are for operational visibility, not user-facing.
All require a secret admin key (X-Admin-Key header) instead of Firebase auth.

Endpoints:
  GET  /api/admin/health/full        → Deep health check (all services)
  GET  /api/admin/metrics            → Usage analytics and cost summary
  GET  /api/admin/compliance         → Compliance status overview
  POST /api/admin/backup             → Trigger Firestore backup to GCS
  GET  /api/admin/cache/stats        → Cache hit rates
  POST /api/admin/cache/clear        → Clear research cache (after law changes)
  GET  /api/admin/security-events    → Recent suspicious activity log
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_key(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> str:
    """Verify the admin secret key from the request header."""
    settings = get_settings()
    expected = settings.admin_secret_key
    if not expected or expected == "change-me-in-production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin key not configured on server.",
        )
    if x_admin_key != expected:
        logger.warning("invalid_admin_key_attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key.",
        )
    return x_admin_key


AdminAuth = Annotated[str, Depends(verify_admin_key)]


@router.get("/health/full")
async def full_health_check(admin: AdminAuth) -> dict:
    """
    Deep health check — verifies all external service connections.
    Returns detailed status for each service.
    """
    checks: dict = {}

    # Firebase
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        fb._db.collection("_health").limit(1).get()
        checks["firestore"] = {"status": "ok"}
    except Exception as e:
        checks["firestore"] = {"status": "error", "detail": str(e)}

    # Gemini
    try:
        from services.gemini_service import get_gemini_service
        gs = get_gemini_service()
        checks["gemini"] = {"status": "ok", "model": gs._model_name}
    except Exception as e:
        checks["gemini"] = {"status": "error", "detail": str(e)}

    # Razorpay
    try:
        from services.razorpay_service import get_razorpay_service
        rp = get_razorpay_service()
        checks["razorpay"] = {"status": "ok"}
    except Exception as e:
        checks["razorpay"] = {"status": "error", "detail": str(e)}

    # GCS
    try:
        from services.storage_service import get_storage_service
        ss = get_storage_service()
        checks["gcs"] = {"status": "ok"}
    except Exception as e:
        checks["gcs"] = {"status": "error", "detail": str(e)}

    # Cache
    try:
        from core.cache import research_cache
        checks["cache"] = {"status": "ok", **research_cache.stats}
    except Exception as e:
        checks["cache"] = {"status": "error", "detail": str(e)}

    all_ok = all(v.get("status") == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "services": checks,
        "checked_at": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
async def get_metrics(admin: AdminAuth) -> dict:
    """Returns usage analytics and Gemini cost summary."""
    from core.monitoring import get_metrics_summary
    return {
        "metrics": get_metrics_summary(),
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/compliance")
async def get_compliance_status(admin: AdminAuth) -> dict:
    """Returns Indian regulatory compliance status."""
    from core.compliance import get_compliance_metadata
    return get_compliance_metadata()


@router.post("/backup")
async def trigger_backup(admin: AdminAuth) -> dict:
    """Trigger a Firestore database backup to GCS."""
    from core.config import get_settings
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
    return {
        "research_cache": research_cache.stats,
        "revision_cache": revision_cache.stats,
    }


@router.post("/cache/clear")
async def clear_cache(admin: AdminAuth) -> dict:
    """Clear the research cache (use after Indian law updates)."""
    from core.cache import research_cache
    size_before = research_cache.stats["size"]
    research_cache.clear()
    logger.info("cache_cleared_by_admin", extra={"entries_cleared": size_before})
    return {
        "status": "cleared",
        "entries_removed": size_before,
        "cleared_at": datetime.utcnow().isoformat(),
    }


@router.get("/security-events")
async def get_security_events(admin: AdminAuth, limit: int = 50) -> dict:
    """Returns recent suspicious activity events for review."""
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        query = (
            fb._db.collection("security_events")
            .order_by("timestamp", direction="DESCENDING")
            .limit(min(limit, 100))
        )
        docs = query.stream()
        events = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            events.append(data)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error("failed_to_fetch_security_events", extra={"error": str(e)})
        return {"events": [], "count": 0, "error": str(e)}


# ── Lawyer Management ─────────────────────────────────────────────────────────

@router.get("/lawyers")
async def list_all_lawyers(
    admin: AdminAuth,
    status_filter: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """
    List all registered lawyers.
    Query params: status_filter (pending|verified|rejected), country_code, limit.
    """
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        query = fb._db.collection("lawyers")
        if status_filter:
            query = query.where("status", "==", status_filter)
        if country_code:
            query = query.where("country_code", "==", country_code.upper())
        docs = query.limit(min(limit, 500)).stream()
        lawyers = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            lawyers.append(data)
        # Sort: pending first, then verified, then rejected
        status_order = {"pending": 0, "verified": 1, "rejected": 2}
        lawyers.sort(key=lambda x: status_order.get(x.get("status", "pending"), 99))
        return {"lawyers": lawyers, "count": len(lawyers)}
    except Exception as e:
        logger.error("admin_lawyers_fetch_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/lawyers/{lawyer_id}/verify")
async def update_lawyer_status(
    lawyer_id: str,
    body: dict,
    admin: AdminAuth,
) -> dict:
    """
    Approve or reject a lawyer application.
    Body: {"status": "verified" | "rejected", "rejection_reason": "optional string"}
    """
    new_status = body.get("status")
    if new_status not in ("verified", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'verified' or 'rejected'")
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        lawyer_ref = fb._db.collection("lawyers").document(lawyer_id)
        doc = lawyer_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Lawyer not found")
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow().isoformat(),
            "reviewed_at": datetime.utcnow().isoformat(),
        }
        if new_status == "rejected" and body.get("rejection_reason"):
            update_data["rejection_reason"] = body["rejection_reason"]
        elif new_status == "verified":
            update_data.pop("rejection_reason", None)
        lawyer_ref.update(update_data)
        logger.info("lawyer_status_updated", extra={"lawyer_id": lawyer_id, "status": new_status})
        return {"success": True, "lawyer_id": lawyer_id, "new_status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("lawyer_status_update_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ── User Management ───────────────────────────────────────────────────────────

@router.get("/users")
async def list_all_users(
    admin: AdminAuth,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    List all users with their case counts and revenue.
    Aggregates data from the 'cases' collection grouped by user_id.
    """
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()

        # Get all cases (we'll aggregate by user_id)
        cases_query = fb._db.collection("cases").limit(2000)
        all_cases = list(cases_query.stream())

        # Aggregate by user_id
        user_stats: dict = {}
        for doc in all_cases:
            data = doc.to_dict()
            uid = data.get("user_id", "unknown")
            if uid not in user_stats:
                user_stats[uid] = {
                    "user_id": uid,
                    "email": data.get("user_email", ""),
                    "total_cases": 0,
                    "paid_cases": 0,
                    "complete_cases": 0,
                    "escalated_cases": 0,
                    "countries": set(),
                    "latest_case_at": None,
                    "revenue_inr": 0,
                }
            stats = user_stats[uid]
            stats["total_cases"] += 1
            status = data.get("status", "")
            if status == "paid":
                stats["paid_cases"] += 1
                stats["revenue_inr"] += 299  # ₹299 per document
            elif status == "complete":
                stats["complete_cases"] += 1
            elif status == "escalated":
                stats["escalated_cases"] += 1
            if data.get("country_code"):
                stats["countries"].add(data["country_code"])
            created = data.get("created_at")
            if created and (stats["latest_case_at"] is None or created > stats["latest_case_at"]):
                stats["latest_case_at"] = created

        users_list = []
        for uid, stats in user_stats.items():
            stats["countries"] = list(stats["countries"])
            users_list.append(stats)

        # Sort by total_cases desc
        users_list.sort(key=lambda x: x["total_cases"], reverse=True)
        total = len(users_list)
        paginated = users_list[offset:offset + limit]

        total_revenue = sum(u["revenue_inr"] for u in users_list)
        return {
            "users": paginated,
            "total": total,
            "total_revenue_inr": total_revenue,
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        logger.error("admin_users_fetch_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def admin_overview(admin: AdminAuth) -> dict:
    """
    Quick overview stats for the admin dashboard home.
    Returns aggregate counts across all collections.
    """
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()

        # Count cases by status
        cases = list(fb._db.collection("cases").limit(5000).stream())
        case_stats = {"total": len(cases), "intake": 0, "complete": 0, "paid": 0, "escalated": 0}
        user_ids = set()
        revenue_inr = 0
        for doc in cases:
            data = doc.to_dict()
            user_ids.add(data.get("user_id", ""))
            status = data.get("status", "")
            if status in case_stats:
                case_stats[status] += 1
            if status == "paid":
                revenue_inr += 299

        # Count lawyers by status
        lawyers = list(fb._db.collection("lawyers").limit(1000).stream())
        lawyer_stats = {"total": len(lawyers), "pending": 0, "verified": 0, "rejected": 0}
        for doc in lawyers:
            data = doc.to_dict()
            status = data.get("status", "pending")
            if status in lawyer_stats:
                lawyer_stats[status] += 1

        return {
            "cases": case_stats,
            "unique_users": len(user_ids),
            "lawyers": lawyer_stats,
            "revenue_inr": revenue_inr,
            "revenue_usd": round(revenue_inr / 83.5, 2),
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("admin_overview_failed", extra={"error": str(e)})
        return {"error": str(e), "generated_at": datetime.utcnow().isoformat()}
