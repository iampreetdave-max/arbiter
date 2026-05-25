"""
main.py — Arbiter FastAPI application entry point.

Starts the web server, registers all routers, configures middleware,
and sets up health check endpoints for Google Cloud Run.
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
from api.documents import router as documents_router
from api.payments import router as payments_router
from core.config import get_settings

settings = get_settings()

# ── Structured logging setup ────────────────────────────────────────────────────────
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    logger.info("arbiter_starting", environment=settings.environment)

    try:
        from services.firebase_service import get_firebase_service
        get_firebase_service()
        logger.info("firebase_connected")
    except Exception as exc:
        logger.warning("firebase_warmup_failed", error=str(exc))

    yield

    logger.info("arbiter_shutdown")


# ── FastAPI app ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Arbiter API",
    description="AI-powered legal agent for everyday Indians. XPRIZE Build with Gemini 2026.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ────────────────────────────────────────────────────────
@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Log request duration for every API call."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    return response


# ── Global exception handler ────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler — never expose stack traces in production."""
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again."},
        )
    raise exc


# ── Routers ────────────────────────────────────────────────────────────────────────
app.include_router(cases_router)
app.include_router(documents_router)
app.include_router(payments_router)


# ── Health checks (required for Cloud Run + hackathon submission evidence) ────────
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Basic health check — Cloud Run uses this to verify the container is alive."""
    return {
        "status": "healthy",
        "service": "arbiter-api",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get("/health/agents", tags=["health"])
async def agents_health() -> dict:
    """
    Agent system health check.

    Verifies Gemini API is reachable and agents can be instantiated.
    Included in hackathon submission as evidence of live AI operation.
    """
    checks: dict[str, str] = {}

    try:
        from agents.intake_agent import get_intake_agent
        get_intake_agent()
        checks["intake_agent"] = "ok"
    except Exception as exc:
        checks["intake_agent"] = f"error: {exc}"

    try:
        from agents.research_agent import get_research_agent
        get_research_agent()
        checks["research_agent"] = "ok"
    except Exception as exc:
        checks["research_agent"] = f"error: {exc}"

    try:
        from agents.drafting_agent import get_drafting_agent
        get_drafting_agent()
        checks["drafting_agent"] = "ok"
    except Exception as exc:
        checks["drafting_agent"] = f"error: {exc}"

    try:
        from agents.tracking_agent import get_tracking_agent
        get_tracking_agent()
        checks["tracking_agent"] = "ok"
    except Exception as exc:
        checks["tracking_agent"] = f"error: {exc}"

    try:
        from services.gemini_service import get_gemini_service
        get_gemini_service()
        checks["gemini_service"] = "ok"
    except Exception as exc:
        checks["gemini_service"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "agents": checks,
        "gemini_model": settings.gemini_model,
    }


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": "Arbiter API",
        "description": "AI legal agent for everyday Indians",
        "docs": "/docs",
        "health": "/health",
    }


# ── Dev runner ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
