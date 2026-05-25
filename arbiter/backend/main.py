"""
main.py — Arbiter FastAPI application entry point v2.0.

Session 7 additions:
  - Multi-country support (IN, US, GB, CA, AU)
  - Lawyer registration + matching system
  - Legal updates feed (weekly refresh)
  - Public case showcase
  - Content refresh admin endpoints
  - /health/countries endpoint
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.cases import router as cases_router
from api.chat import router as chat_router
from api.documents import router as documents_router
from api.payments import router as payments_router
from api.admin import router as admin_router
from api.lawyers import router as lawyers_router
from api.lawyers import escalate_router
from api.legal_updates import router as legal_updates_router
from api.public_cases import router as public_cases_router
from api.content_refresh import router as content_refresh_router
from core.config import get_settings
from core.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    SuspiciousRequestMiddleware,
    setup_rate_limiting,
)

settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("arbiter_starting", environment=settings.environment)

    if settings.sentry_dsn:
        try:
            from core.sentry import init_sentry
            init_sentry(dsn=settings.sentry_dsn, environment=settings.environment)
            logger.info("sentry_initialized")
        except Exception as exc:
            logger.warning("sentry_init_failed", error=str(exc))
    else:
        logger.info("sentry_disabled", reason="SENTRY_DSN not set")

    try:
        from services.firebase_service import get_firebase_service
        get_firebase_service()
        logger.info("firebase_connected")
    except Exception as exc:
        logger.warning("firebase_warmup_failed", error=str(exc))

    yield

    logger.info("arbiter_shutdown")


app = FastAPI(
    title="Arbiter API",
    description="AI-powered legal agent for everyday people. XPRIZE Build with Gemini 2026. Supports India, US, UK, Canada, Australia.",
    version="2.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

setup_rate_limiting(app)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SuspiciousRequestMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    request_id = getattr(request.state, "request_id", "-")
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
        request_id=request_id,
    )
    try:
        from core.monitoring import metrics_buffer
        metrics_buffer.record_latency(request.url.path, duration_ms)
    except Exception:
        pass
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    try:
        from core.sentry import capture_exception
        capture_exception(exc, context={"path": request.url.path, "method": request.method})
    except Exception:
        pass
    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again."},
        )
    raise exc


app.include_router(chat_router)
app.include_router(cases_router)
app.include_router(documents_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(lawyers_router)
app.include_router(escalate_router)
app.include_router(legal_updates_router)
app.include_router(public_cases_router)
app.include_router(content_refresh_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "arbiter-api",
        "version": "2.0.0",
        "environment": settings.environment,
        "supported_countries": ["IN", "US", "GB", "CA", "AU"],
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check() -> dict:
    checks: dict[str, str] = {}
    all_ready = True
    try:
        from services.firebase_service import get_firebase_service
        get_firebase_service()
        checks["firebase"] = "ok"
    except Exception as exc:
        checks["firebase"] = f"error: {exc}"
        all_ready = False
    if settings.gemini_api_key:
        checks["gemini_api_key"] = "ok"
    else:
        checks["gemini_api_key"] = "missing"
        all_ready = False
    if settings.razorpay_key_id and settings.razorpay_key_secret:
        checks["razorpay"] = "ok"
    else:
        checks["razorpay"] = "missing credentials"
        all_ready = False
    status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content={"ready": all_ready, "checks": checks})


@app.get("/health/agents", tags=["health"])
async def agents_health() -> dict:
    checks: dict[str, str] = {}
    for agent_name, import_path in [
        ("intake_agent",   ("agents.intake_agent",   "get_intake_agent")),
        ("research_agent", ("agents.research_agent",  "get_research_agent")),
        ("drafting_agent", ("agents.drafting_agent",  "get_drafting_agent")),
        ("tracking_agent", ("agents.tracking_agent",  "get_tracking_agent")),
        ("gemini_service", ("services.gemini_service","get_gemini_service")),
    ]:
        try:
            import importlib
            mod = importlib.import_module(import_path[0])
            getattr(mod, import_path[1])()
            checks[agent_name] = "ok"
        except Exception as exc:
            checks[agent_name] = f"error: {exc}"
    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "agents": checks,
        "gemini_model": settings.gemini_model,
    }


@app.get("/health/compliance", tags=["health"])
async def compliance_check() -> dict:
    try:
        from core.compliance import get_compliance_metadata
        return get_compliance_metadata()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@app.get("/health/countries", tags=["health"])
async def countries_health() -> dict:
    from core.countries import get_supported_country_list
    return {
        "supported_countries": get_supported_country_list(),
        "default_country": "IN",
        "total": 5,
    }


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "service": "Arbiter API",
        "description": "AI legal agent for everyday people — India, US, UK, Canada, Australia",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "supported_countries": ["🇮🇳 India", "🇺🇸 United States", "🇬🇧 United Kingdom", "🇨🇦 Canada", "🇦🇺 Australia"],
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
