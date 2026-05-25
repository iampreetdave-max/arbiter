"""
sentry.py — Sentry crash alerting and error tracking.

Sentry captures every unhandled exception with full stack trace,
request context, and user info. Alerts are sent to email/Slack.

Set SENTRY_DSN in environment to enable. If not set, Sentry is disabled
(safe for local development, required in production).
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def init_sentry(dsn: Optional[str] = None, environment: str = "development") -> bool:
    """
    Initialise Sentry SDK. Returns True if successfully initialised.

    Args:
        dsn: Sentry DSN from https://sentry.io — set as SENTRY_DSN env var.
        environment: development | staging | production — controls alert filtering.
    """
    effective_dsn = dsn or os.environ.get("SENTRY_DSN", "")
    if not effective_dsn:
        logger.info("sentry_disabled — set SENTRY_DSN to enable crash alerts")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration

        sentry_logging = LoggingIntegration(
            level=logging.WARNING,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=effective_dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                sentry_logging,
                AsyncioIntegration(),
            ],
            traces_sample_rate=0.2 if environment == "production" else 1.0,
            profiles_sample_rate=0.1,
            send_default_pii=False,
            before_send=_before_send,
        )
        logger.info("sentry_initialised", extra={"environment": environment})
        return True

    except ImportError:
        logger.warning("sentry_sdk not installed — run: pip install sentry-sdk[fastapi]")
        return False
    except Exception as exc:
        logger.error("sentry_init_failed", extra={"error": str(exc)})
        return False


def _before_send(event: dict, hint: dict) -> Optional[dict]:
    """Filter and sanitise events before sending to Sentry."""
    if "exc_info" in hint:
        from fastapi import HTTPException
        if isinstance(hint["exc_info"][1], HTTPException):
            status_code = hint["exc_info"][1].status_code
            if status_code in (401, 403, 404, 422):
                return None

    request = event.get("request", {})
    headers = request.get("headers", {})
    for sensitive_key in ("authorization", "x-api-key", "cookie"):
        if sensitive_key in headers:
            headers[sensitive_key] = "[Filtered]"

    for field in ("password", "razorpay_key_secret", "gemini_api_key", "token"):
        data = event.get("request", {}).get("data", {})
        if isinstance(data, dict) and field in data:
            data[field] = "[Filtered]"

    return event


def capture_exception(exc: Exception, context: Optional[dict] = None) -> None:
    """Manually capture an exception and send to Sentry."""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
    except ImportError:
        logger.error("exception_not_tracked", extra={"error": str(exc)})


def set_sentry_user(user_id: str, email: str = "") -> None:
    """Tag all subsequent Sentry events with the current user."""
    try:
        import sentry_sdk
        sentry_sdk.set_user({"id": user_id, "email": email})
    except ImportError:
        pass
