"""
lawyer_matching_service.py — Match cases to lawyers based on specialty + country.

Scoring: specialty 50% + jurisdiction 20% + rating 15% + pro bono 10% + experience 5%
"""
# Arbiter - Powered by Google Gemini 2.0 Pro - XPRIZE Build with Gemini
from __future__ import annotations

import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()

_PROBLEM_TO_SPECIALTY: dict[str, list[str]] = {
    "tenant_dispute":   ["tenant", "property", "civil"],
    "employment":       ["employment", "civil"],
    "consumer":         ["consumer", "civil"],
    "rti":              ["rti", "civil"],
    "harassment":       ["criminal", "cyber", "civil"],
    "debt_recovery":    ["debt_recovery", "civil"],
    "other":            ["civil", "other"],
}


def _compute_match_score(lawyer_data: dict, case_data: dict) -> float:
    score = 0.0
    problem_type = case_data.get("problem_type", "other")
    preferred_specialties = _PROBLEM_TO_SPECIALTY.get(problem_type, ["civil"])
    lawyer_specialties = [s.lower() for s in lawyer_data.get("specialties", [])]

    if preferred_specialties[0] in lawyer_specialties:
        score += 0.50
    elif any(s in lawyer_specialties for s in preferred_specialties[1:]):
        score += 0.30

    case_jurisdiction = (case_data.get("jurisdiction") or "").lower()
    lawyer_jurisdiction = (lawyer_data.get("jurisdiction") or "").lower()
    if case_jurisdiction and lawyer_jurisdiction:
        if case_jurisdiction == lawyer_jurisdiction:
            score += 0.20
        elif case_jurisdiction in lawyer_jurisdiction or lawyer_jurisdiction in case_jurisdiction:
            score += 0.10

    rating = float(lawyer_data.get("rating", 0.0))
    rating_count = int(lawyer_data.get("rating_count", 0))
    if rating_count > 0:
        score += (rating / 5.0) * 0.15

    if lawyer_data.get("available_for_pro_bono") and case_data.get("pro_bono_requested"):
        score += 0.10

    years = min(int(lawyer_data.get("years_of_experience", 0)), 30)
    score += (years / 30.0) * 0.05

    return round(min(score, 1.0), 4)


class LawyerMatchingService:
    def __init__(self, firebase_service):
        self._fb = firebase_service

    async def find_best_match(self, case_id: str, case_data: dict, country_code: str) -> dict | None:
        try:
            lawyers = self._fb.db.collection("lawyers").where(
                "country_code", "==", country_code
            ).where("status", "==", "verified").stream()

            candidates: list[tuple[float, dict]] = []
            for doc in lawyers:
                lawyer_data = doc.to_dict()
                lawyer_data["id"] = doc.id
                score = _compute_match_score(lawyer_data, case_data)
                if score > 0.2:
                    candidates.append((score, lawyer_data))

            if not candidates:
                return None

            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_lawyer = candidates[0]
            return {**best_lawyer, "match_score": best_score}

        except Exception as exc:
            logger.error("lawyer_matching_failed", case_id=case_id, error=str(exc))
            return None

    async def create_match(self, case_id: str, lawyer_id: str, user_id: str, case_data: dict, match_score: float) -> dict:
        match_data = {
            "lawyer_id": lawyer_id,
            "case_id": case_id,
            "user_id": user_id,
            "case_title": case_data.get("title", "Untitled Case"),
            "case_problem_type": case_data.get("problem_type", "other"),
            "case_country_code": case_data.get("country_code", "IN"),
            "case_jurisdiction": case_data.get("jurisdiction", ""),
            "match_score": match_score,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        doc_ref = self._fb.db.collection("case_matches").document()
        doc_ref.set(match_data)
        return {**match_data, "id": doc_ref.id}

    async def get_lawyer_matches(self, lawyer_id: str, status_filter: str | None = None, limit: int = 20) -> list[dict]:
        try:
            query = self._fb.db.collection("case_matches").where("lawyer_id", "==", lawyer_id)
            if status_filter:
                query = query.where("status", "==", status_filter)
            docs = query.order_by("created_at", direction="DESCENDING").limit(limit).stream()
            results = []
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                results.append(d)
            return results
        except Exception as exc:
            logger.error("get_lawyer_matches_failed", lawyer_id=lawyer_id, error=str(exc))
            return []

    async def respond_to_match(self, match_id: str, lawyer_id: str, action: str, notes: str | None = None) -> dict | None:
        try:
            doc_ref = self._fb.db.collection("case_matches").document(match_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None
            match_data = doc.to_dict()
            if match_data.get("lawyer_id") != lawyer_id:
                return None
            update = {
                "status": "accepted" if action == "accept" else "declined",
                "responded_at": datetime.now(timezone.utc).isoformat(),
            }
            if notes:
                update["lawyer_notes"] = notes
            doc_ref.update(update)
            if action == "accept":
                self._fb.db.collection("lawyers").document(lawyer_id).update(
                    {"cases_accepted": self._fb._firestore.Increment(1)}
                )
            return {**match_data, **update, "id": match_id}
        except Exception as exc:
            logger.error("respond_to_match_failed", match_id=match_id, error=str(exc))
            return None


_instance: LawyerMatchingService | None = None


def get_lawyer_matching_service() -> LawyerMatchingService:
    global _instance
    if _instance is None:
        from services.firebase_service import get_firebase_service
        _instance = LawyerMatchingService(get_firebase_service())
    return _instance
