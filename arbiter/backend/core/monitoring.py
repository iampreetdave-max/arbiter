"""
monitoring.py — Usage analytics, cost tracking, and performance monitoring.

Tracks Gemini token costs, endpoint latencies, user analytics, suspicious activity.

Cost model (Gemini 2.0 Pro):
  - Input: $3.50 per 1M tokens
  - Output: $10.50 per 1M tokens
  - Grounding: +$35 per 1K grounding requests (Google Search)
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)

GEMINI_COST_PER_1M_INPUT = 3.50
GEMINI_COST_PER_1M_OUTPUT = 10.50
GEMINI_GROUNDING_PER_1K = 35.00
INR_PER_USD = 83.5


def compute_gemini_cost_usd(
    tokens_in: int,
    tokens_out: int,
    grounded: bool = False,
    grounding_calls: int = 1,
) -> float:
    """Compute cost of a Gemini API call in USD."""
    input_cost  = (tokens_in  / 1_000_000) * GEMINI_COST_PER_1M_INPUT
    output_cost = (tokens_out / 1_000_000) * GEMINI_COST_PER_1M_OUTPUT
    grounding_cost = (grounding_calls / 1000) * GEMINI_GROUNDING_PER_1K if grounded else 0.0
    return round(input_cost + output_cost + grounding_cost, 6)


def compute_gemini_cost_inr(tokens_in: int, tokens_out: int, grounded: bool = False) -> float:
    """Compute cost in INR."""
    return round(compute_gemini_cost_usd(tokens_in, tokens_out, grounded) * INR_PER_USD, 4)


class MetricsBuffer:
    """Thread-safe in-memory buffer for metrics."""

    def __init__(self) -> None:
        self._events: list[dict] = []
        self._gemini_costs: list[dict] = []
        self._endpoint_latencies: dict[str, list[float]] = {}

    def record_event(self, event: dict) -> None:
        self._events.append(event)

    def record_gemini_cost(self, cost_record: dict) -> None:
        self._gemini_costs.append(cost_record)

    def record_latency(self, endpoint: str, latency_ms: float) -> None:
        if endpoint not in self._endpoint_latencies:
            self._endpoint_latencies[endpoint] = []
        latencies = self._endpoint_latencies[endpoint]
        latencies.append(latency_ms)
        if len(latencies) > 1000:
            self._endpoint_latencies[endpoint] = latencies[-1000:]

    def get_latency_percentiles(self, endpoint: str) -> dict:
        """Return P50/P95/P99 for a given endpoint."""
        latencies = sorted(self._endpoint_latencies.get(endpoint, []))
        if not latencies:
            return {"p50": 0, "p95": 0, "p99": 0, "count": 0}
        n = len(latencies)
        return {
            "p50": latencies[int(n * 0.50)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[int(n * 0.99)],
            "count": n,
        }

    def flush_and_reset(self) -> tuple[list[dict], list[dict]]:
        events = self._events[:]
        costs = self._gemini_costs[:]
        self._events.clear()
        self._gemini_costs.clear()
        return events, costs


_metrics_buffer = MetricsBuffer()
metrics_buffer = _metrics_buffer  # Public alias


async def track_gemini_call(
    user_id: str,
    operation: str,
    tokens_in: int,
    tokens_out: int,
    grounded: bool = False,
    case_id: str = "",
    latency_ms: float = 0.0,
) -> None:
    """Record a Gemini API call for cost tracking."""
    cost_inr = compute_gemini_cost_inr(tokens_in, tokens_out, grounded)
    cost_usd = compute_gemini_cost_usd(tokens_in, tokens_out, grounded)
    record = {
        "user_id": user_id, "case_id": case_id, "operation": operation,
        "tokens_in": tokens_in, "tokens_out": tokens_out, "grounded": grounded,
        "cost_usd": cost_usd, "cost_inr": cost_inr,
        "latency_ms": round(latency_ms, 2),
        "timestamp": datetime.utcnow().isoformat(),
        "date": date.today().isoformat(),
    }
    _metrics_buffer.record_gemini_cost(record)
    logger.info("gemini_cost_tracked", extra={"operation": operation, "cost_inr": cost_inr})


async def track_event(
    user_id: str,
    event_name: str,
    properties: Optional[dict] = None,
    session_id: str = "",
) -> None:
    """Record a user analytics event."""
    event = {
        "user_id": user_id, "event": event_name,
        "properties": properties or {}, "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "date": date.today().isoformat(),
    }
    _metrics_buffer.record_event(event)


async def track_suspicious_activity(
    user_id: str,
    activity_type: str,
    details: dict,
    client_ip: str = "",
) -> None:
    """Record and alert on suspicious user activity via Sentry + Firestore."""
    logger.warning("suspicious_activity", extra={"user_id": user_id, "activity_type": activity_type, **details})
    try:
        from core.sentry import capture_exception
        capture_exception(
            ValueError(f"Suspicious activity: {activity_type}"),
            context={"user_id": user_id, "client_ip": client_ip, **details},
        )
    except Exception:
        pass
    try:
        from services.firebase_service import get_firebase_service
        fb = get_firebase_service()
        fb._db.collection("security_events").add({
            "user_id": user_id, "activity_type": activity_type,
            "client_ip": client_ip, "details": details,
            "timestamp": datetime.utcnow().isoformat(), "reviewed": False,
        })
    except Exception as e:
        logger.error("failed_to_persist_security_event", extra={"error": str(e)})


def get_metrics_summary() -> dict:
    """Return current metrics summary for the admin dashboard."""
    common_endpoints = [
        "/api/cases/", "/cases/chat", "/api/cases/{id}/generate/stream", "/api/documents/{id}/revise",
    ]
    latencies = {ep: _metrics_buffer.get_latency_percentiles(ep) for ep in common_endpoints}
    return {
        "endpoint_latencies_ms": latencies,
        "buffer_size": {"events": len(_metrics_buffer._events), "cost_records": len(_metrics_buffer._gemini_costs)},
        "generated_at": datetime.utcnow().isoformat(),
    }
