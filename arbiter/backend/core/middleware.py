"""
middleware.py — Production-grade HTTP middleware for Arbiter.

Middleware stack (applied in order):
  1. RequestIDMiddleware    — Attach X-Request-ID to every request + response
  2. SecurityHeadersMiddleware — Add OWASP-recommended security headers
  3. SuspiciousRequestMiddleware — Detect and alert on suspicious inputs
  4. RateLimitMiddleware      — Per-IP limits via slowapi
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

SUSPICIOUS_PATTERNS = [
    r"(?i)(drop\s+table|delete\s+from|insert\s+into|union\s+select)",
    r"(?i)(<script|javascript:|onerror=|onload=)",
    r"(?i)(\.\.\/|\.\.\\/\/etc\/passwd|\/proc\/self)",
    r"(?i)(system\(|exec\(|eval\(|__import__)",
    r"(?i)(curl\s+http|wget\s+http|nc\s+-)",
]
SUSPICIOUS_RE = [re.compile(p) for p in SUSPICIOUS_PATTERNS]

LEGAL_KEYWORDS = {
    "law", "legal", "court", "case", "complaint", "dispute", "rights",
    "notice", "demand", "rent", "deposit", "salary", "wages", "fraud",
    "consumer", "rti", "police", "fir", "advocate", "lawyer", "section",
    "act", "ipc", "crpc", "landlord", "tenant", "employer", "employee",
    "refund", "harassment", "cheque", "bounce", "contract", "agreement",
    "witness", "evidence", "filing", "petition", "appeal", "judge",
    "magistrate", "arbitration", "mediation", "compensation", "damages",
    "emi", "loan", "debt", "recovery", "property", "eviction", "lease",
    "kanoon", "adalat", "mukadma", "vakil", "shikayat", "nyaya",
}


def is_off_topic(text: str) -> bool:
    """Returns True if the user message appears unrelated to legal matters."""
    words = set(text.lower().split())
    return len(words & LEGAL_KEYWORDS) == 0 and len(text.split()) > 8


def is_suspicious(text: str) -> tuple[bool, str]:
    """Returns (is_suspicious, matched_pattern) if text matches attack patterns."""
    for pattern in SUSPICIOUS_RE:
        match = pattern.search(text)
        if match:
            return True, match.group()
    return False, ""


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attaches a unique X-Request-ID to every request and response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds OWASP-recommended HTTP security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://checkout.razorpay.com; "
            "frame-src https://api.razorpay.com; "
            "connect-src 'self' https://api.razorpay.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com"
        )
        return response


class SuspiciousRequestMiddleware(BaseHTTPMiddleware):
    """Detects and blocks suspicious request patterns (SQLi, XSS, injection)."""

    INSPECT_PATHS = {"/cases/chat", "/cases/", "/api/cases/"}
    MAX_BODY_INSPECT = 2000

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in ("POST", "PATCH", "PUT"):
            return await call_next(request)

        path = request.url.path
        should_inspect = any(path.startswith(p) for p in self.INSPECT_PATHS)
        if not should_inspect:
            return await call_next(request)

        try:
            body_bytes = await request.body()
            body_text = body_bytes.decode("utf-8", errors="replace")[:self.MAX_BODY_INSPECT]

            suspicious, pattern = is_suspicious(body_text)
            if suspicious:
                client_ip = request.client.host if request.client else "unknown"
                logger.warning(
                    "suspicious_request_blocked",
                    extra={"path": path, "client_ip": client_ip, "matched_pattern": pattern[:50]},
                )
                try:
                    from core.sentry import capture_exception
                    capture_exception(
                        ValueError(f"Suspicious request blocked: {pattern[:50]}"),
                        context={"client_ip": client_ip, "path": path},
                    )
                except Exception:
                    pass

                return JSONResponse(
                    status_code=400,
                    content={"detail": "Request contains invalid characters. Please rephrase."},
                    headers={"X-Request-ID": getattr(request.state, "request_id", "")},
                )
        except Exception:
            pass

        return await call_next(request)


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure slowapi rate limiting on the FastAPI app."""
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware

        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["60/minute", "500/day"],
            storage_uri="memory://",
        )
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)
        logger.info("rate_limiting_enabled")
    except ImportError:
        logger.warning("slowapi not installed — rate limiting disabled")
