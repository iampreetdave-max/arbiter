"""
case_showcase_service.py — Curates interesting public legal cases by country.

Educational content: famous/interesting public cases that teach citizens about their rights.
Uses Gemini + grounding to find noteworthy cases. Refreshed weekly.
"""
# Arbiter - Powered by Google Gemini 2.0 Pro - XPRIZE Build with Gemini
from __future__ import annotations

import json
import re
import structlog
from datetime import datetime, timezone
from typing import Any

logger = structlog.get_logger()

_SHOWCASE_PROMPT = """You are a legal educator. Find 3-5 interesting, newsworthy, or landmark public legal cases from {country_name} that are:
- From the past 2 years (2024-2026) OR landmark cases from history that are widely discussed today
- Educational - they teach ordinary people about their legal rights
- Publicly reported cases (not private matters)

For each case, provide EXACTLY this JSON structure (return an array):
[
  {{
    "title": "Catchy descriptive title for the case (not just 'X vs Y')",
    "parties": "Plaintiff/Applicant name vs Defendant/Respondent name",
    "court": "Court or tribunal name",
    "year": 2025,
    "category": "consumer" | "employment" | "tenant" | "civil_rights" | "landmark" | "cyber" | "corporate",
    "summary": "3-4 sentences: what happened, what was decided, what remedies were ordered",
    "legal_lesson": "The key legal principle or right this case demonstrates",
    "citizen_impact": "How knowing about this case helps ordinary people assert their rights",
    "is_landmark": true or false,
    "source_hint": "Court, news publication, or official source where this is documented"
  }}
]

CRITICAL:
- Only include REAL cases that are publicly documented
- Include at least 1 landmark/famous case that citizens should know about
- Focus on cases that empower ordinary people (consumers, employees, tenants)

Return ONLY the JSON array. No explanation."""


async def fetch_showcase_cases_for_country(
    country_code: str,
    country_name: str,
    gemini_service,
) -> list[dict[str, Any]]:
    prompt = _SHOWCASE_PROMPT.format(country_name=country_name)

    try:
        result = await gemini_service.generate_with_grounding(prompt)
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if not json_match:
            return []

        cases_raw = json.loads(json_match.group())
        now = datetime.now(timezone.utc)
        processed = []

        for item in cases_raw:
            if not isinstance(item, dict):
                continue
            if not item.get("title") or not item.get("summary"):
                continue
            processed.append({
                "country_code": country_code,
                "country_name": country_name,
                "title": str(item.get("title", ""))[:120],
                "parties": str(item.get("parties", ""))[:150],
                "court": str(item.get("court", ""))[:100],
                "year": int(item.get("year", now.year)),
                "category": str(item.get("category", "landmark")),
                "summary": str(item.get("summary", ""))[:600],
                "legal_lesson": str(item.get("legal_lesson", ""))[:300],
                "citizen_impact": str(item.get("citizen_impact", ""))[:300],
                "is_landmark": bool(item.get("is_landmark", False)),
                "source_hint": str(item.get("source_hint", ""))[:200],
                "fetched_at": now.isoformat(),
                "view_count": 0,
                "is_active": True,
            })

        return processed

    except Exception as exc:
        logger.error("showcase_cases_fetch_failed", country=country_code, error=str(exc))
        return []


class CaseShowcaseService:
    def __init__(self, firebase_service, gemini_service):
        self._fb = firebase_service
        self._gemini = gemini_service

    async def refresh_all_countries(self) -> dict[str, int]:
        from core.countries import SUPPORTED_COUNTRIES
        results: dict[str, int] = {}
        for code, data in SUPPORTED_COUNTRIES.items():
            cases = await fetch_showcase_cases_for_country(
                country_code=code,
                country_name=data["name"],
                gemini_service=self._gemini,
            )
            for case in cases:
                doc_ref = self._fb.db.collection("public_cases").document()
                doc_ref.set(case)
            results[code] = len(cases)
        return results

    def get_cases(self, country_code: str | None = None, category: str | None = None, landmark_only: bool = False, limit: int = 12) -> list[dict]:
        try:
            query = self._fb.db.collection("public_cases").where("is_active", "==", True)
            if country_code:
                query = query.where("country_code", "==", country_code.upper())
            if landmark_only:
                query = query.where("is_landmark", "==", True)
            docs = query.order_by("fetched_at", direction="DESCENDING").limit(limit).stream()
            results = []
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                if category and d.get("category") != category:
                    continue
                results.append(d)
            return results
        except Exception as exc:
            logger.error("get_showcase_cases_failed", error=str(exc))
            return []

    def increment_view(self, case_id: str) -> None:
        try:
            from google.cloud.firestore import Increment
            self._fb.db.collection("public_cases").document(case_id).update(
                {"view_count": Increment(1)}
            )
        except Exception:
            pass


_instance: CaseShowcaseService | None = None


def get_case_showcase_service() -> CaseShowcaseService:
    global _instance
    if _instance is None:
        from services.firebase_service import get_firebase_service
        from services.gemini_service import get_gemini_service
        _instance = CaseShowcaseService(get_firebase_service(), get_gemini_service())
    return _instance
