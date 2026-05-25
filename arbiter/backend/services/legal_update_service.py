"""
legal_update_service.py — Weekly legal update fetcher using Gemini + Google Search grounding.
"""
# Arbiter - Powered by Google Gemini 2.0 Pro - XPRIZE Build with Gemini
from __future__ import annotations

import structlog
from datetime import datetime, timezone, timedelta
from typing import Any

logger = structlog.get_logger()

_UPDATE_PROMPT_TEMPLATE = """You are a legal research assistant. Search for the LATEST (last 7 days) legal developments in {country_name}.

Find 3-5 of the most important:
1. New legislation or amendments enacted
2. Major Supreme/High Court judgments affecting citizens' rights
3. Regulatory changes (RBI, SEBI, consumer protection agencies, etc.)
4. Important government advisories or policy changes

For each development, provide EXACTLY this JSON structure (return an array):
[
  {{
    "category": "legislation" | "judgment" | "regulation" | "advisory",
    "title": "Short descriptive title (max 80 chars)",
    "summary": "2-3 sentence summary of what happened and why it matters",
    "impact": "How this directly affects ordinary citizens/consumers/employees",
    "effective_date": "YYYY-MM-DD or 'effective immediately' or 'pending gazette notification'",
    "source_hint": "Court name, ministry, or publication where this was announced"
  }}
]

CRITICAL:
- Only include REAL, verifiable developments from the past 7 days
- If you cannot find 3-5 real developments, return fewer - do not fabricate
- Focus on things that affect everyday people (tenants, employees, consumers, borrowers)
- Always include the source_hint so users can verify

Return ONLY the JSON array. No preamble, no explanation."""


async def fetch_legal_updates_for_country(
    country_code: str,
    country_name: str,
    gemini_service,
) -> list[dict[str, Any]]:
    import json, re
    prompt = _UPDATE_PROMPT_TEMPLATE.format(country_name=country_name)

    try:
        result = await gemini_service.generate_with_grounding(prompt)
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if not json_match:
            return []

        updates_raw = json.loads(json_match.group())
        now = datetime.now(timezone.utc)
        iso_week = now.isocalendar()[1]
        processed = []

        for item in updates_raw:
            if not isinstance(item, dict):
                continue
            if not item.get("title") or not item.get("summary"):
                continue
            processed.append({
                "country_code": country_code,
                "country_name": country_name,
                "category": item.get("category", "advisory"),
                "title": str(item.get("title", ""))[:100],
                "summary": str(item.get("summary", ""))[:500],
                "impact": str(item.get("impact", ""))[:300],
                "effective_date": str(item.get("effective_date", ""))[:50],
                "source_hint": str(item.get("source_hint", ""))[:200],
                "fetched_at": now.isoformat(),
                "week_number": iso_week,
                "year": now.year,
                "is_featured": False,
            })

        return processed

    except Exception as exc:
        logger.error("legal_updates_fetch_failed", country=country_code, error=str(exc))
        return []


class LegalUpdateService:
    def __init__(self, firebase_service, gemini_service):
        self._fb = firebase_service
        self._gemini = gemini_service

    async def refresh_all_countries(self) -> dict[str, int]:
        from core.countries import SUPPORTED_COUNTRIES
        results: dict[str, int] = {}
        for code, data in SUPPORTED_COUNTRIES.items():
            updates = await fetch_legal_updates_for_country(
                country_code=code,
                country_name=data["name"],
                gemini_service=self._gemini,
            )
            for update in updates:
                doc_ref = self._fb.db.collection("legal_updates").document()
                doc_ref.set(update)
            results[code] = len(updates)
        return results

    async def refresh_country(self, country_code: str) -> int:
        from core.countries import SUPPORTED_COUNTRIES
        data = SUPPORTED_COUNTRIES.get(country_code.upper())
        if not data:
            return 0
        updates = await fetch_legal_updates_for_country(
            country_code=country_code.upper(),
            country_name=data["name"],
            gemini_service=self._gemini,
        )
        for update in updates:
            doc_ref = self._fb.db.collection("legal_updates").document()
            doc_ref.set(update)
        return len(updates)

    def get_updates(self, country_code: str | None = None, category: str | None = None, limit: int = 20, days_back: int = 30) -> list[dict]:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
            query = self._fb.db.collection("legal_updates").where("fetched_at", ">=", cutoff)
            if country_code:
                query = query.where("country_code", "==", country_code.upper())
            if category:
                query = query.where("category", "==", category)
            docs = query.order_by("fetched_at", direction="DESCENDING").limit(limit).stream()
            results = []
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                results.append(d)
            return results
        except Exception as exc:
            logger.error("get_legal_updates_failed", error=str(exc))
            return []


_instance: LegalUpdateService | None = None


def get_legal_update_service() -> LegalUpdateService:
    global _instance
    if _instance is None:
        from services.firebase_service import get_firebase_service
        from services.gemini_service import get_gemini_service
        _instance = LegalUpdateService(get_firebase_service(), get_gemini_service())
    return _instance
