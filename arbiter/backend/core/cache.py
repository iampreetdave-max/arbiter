"""
cache.py — In-memory TTL cache for expensive operations.

Primary use: Cache legal research results so identical queries don't re-call Gemini.

Cache policy:
  - TTL: 6 hours (laws don't change frequently)
  - Max size: 500 entries
  - Key: SHA256(problem_type + jurisdiction + desired_outcome[:50])
"""
from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Thread-safe in-memory TTL cache.

    Usage:
        cache = TTLCache(ttl_seconds=3600, max_size=500)
        cache.set("key", value)
        value = cache.get("key")  # None if expired or missing
    """

    def __init__(self, ttl_seconds: int = 21600, max_size: int = 500) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expire_at = entry
            if time.monotonic() > expire_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self._max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest_key]
            self._store[key] = (value, time.monotonic() + self._ttl)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "size": len(self._store),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": round(hit_rate, 1),
                "ttl_seconds": self._ttl,
            }


# Module-level singletons
research_cache = TTLCache(ttl_seconds=21600, max_size=500)
revision_cache = TTLCache(ttl_seconds=300, max_size=200)


def make_research_cache_key(problem_type: str, jurisdiction: str, desired_outcome: str) -> str:
    """Generate a stable cache key for research results."""
    raw = f"{problem_type}|{jurisdiction.lower().strip()}|{desired_outcome[:80].lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
