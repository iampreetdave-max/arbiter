"""
lawyer_matching_service.py — Match cases to lawyers based on specialty + country.

When a user escalates a case to a lawyer:
1. Find all verified lawyers in the same country
2. Filter by specialty matching the case problem type
3. Rank by: (a) specialty match, (b) jurisdiction match, (c) rating, (d) pro bono preference
4. Return the best match

Also handles: lawyer dashboard case feed, accept/decline case flows.
"""
from __future__ import annotations

import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()

# ── Specialty → ProblemType mapping ──────────────────────────────────────────────

_PROBLEM_TO_SPECIALTY: dict[str, list[str]] = {
    "tenant_dispute":   ["tenant", "property", "civil"],
    "employment":       ["employment", "civil"],
    "consumer":         ["consumer", "civil"],
    "rti":              ["rti", "civil"],
    "harassment":       ["criminal", "cyber", "civil"],
    "debt_recovery":    ["debt_recovery", "civil"],
    "other":            ["civil", "other"],
}


def _compute_match_score(
    lawyer_data: dict,
    case_data: dict,
) -> float:
    """
    Compute a match score between a lawyer and a case (0.0–1.0).

    Scoring:
    - Specialty match: 0.50
    - Jurisdiction match (state/province): 0.20
    - Rating (normalised 0–5 → 0–0.15): 0.15
    - Pro bono preference when case has no payment: 0.10
    - Years experience (normalised): 0.05
    """
    score = 0.0

    # Specialty match (most important)
    problem_type = case_data.get("problem_type", "other")
    preferred_specialties = _PROBLEM_TO_SPECIALTY.get(problem_type, ["civil"])
    lawyer_specialties = [s.lower() for s in lawyer_data.get("specialties", [])]

    if preferred_specialties[0] in lawyer_specialties:
        score += 0.50  # Primary specialty match
    elif any(s in lawyer_specialties for s in preferred_specialties[1:]):
        score += 0.30  # Secondary specialty match

    # Jurisdiction match
    case_jurisdiction = (case_data.get("jurisdiction") or "").lower()
    lawyer_jurisdiction = (lawyer_data.get("jurisdiction") or "").lower()
    if case_jurisdiction and lawyer_jurisdiction:
        if case_jurisdiction == lawyer_jurisdiction:
            score += 0.20
        elif case_jurisdiction in lawyer_jurisdiction or lawyer_jurisdiction in case_jurisdiction:
            score += 0.10

    # Rating contribution
    rating = float(lawyer_data.get("rating", 0.0))
    rating_count = int(lawyer_data.get("rating_count", 0))
    if rating_count > 0:
        score += (rating / 5.0) * 0.15

    # Pro bono match
    if lawyer_data.get("available_for_pro_bono") and case_data.get("pro_bono_requested"):
        score += 0.10

    # Experience contribution
    years = min(int(lawyer_data.get("years_of_experience", 0)), 30)
    score += (years / 30.0) * 0.05

    return round(min(score, 1.0), 4)


class LawyerMatchingService:
    """
    Handles matching cases to lawyers and managing the match lifecycle.

    Injected with firebase_service at runtime to avoid circular imports.
    """

    def __init__(self, firebase_service):
        self._fb = firebase_service

    async def find_best_match(
        self,
        case_id: str,
        case_data: dict,
        country_code: str,
    ) -> dict | None:
        """
        Find the best matching lawyer for a case.

        Returns the lawyer document dict + match_score, or None if no match found.
        """
        try:
            # Get all verified lawyers in the same country
            lawyers = self._fb.db.collection("lawyers").where(
                "country_code", "==", country_code
            ).where(
                "status", "==", "verified"
            ).stream()

            candidates: list[tuple[float, dict]] = []

            for doc in lawyers:
                lawyer_data = doc.to_dict()
                lawyer_data["id"] = doc.id
                score = _compute_match_score(lawyer_data, case_data)
                if score > 0.2:  # Minimum threshold
                    candidates.append((score, lawyer_data))

            if not candidates:
                logger.warning("no_lawyers_matched", case_id=case_id, country=country_code)
                return None

            # Sort by score descending
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_lawyer = candidates[0]

            logger.info(
                "lawyer_matched",
                case_id=case_id,
                lawyer_id=best_lawyer["id"],
                score=best_score,
                candidates_count=len(candidates),
            )
            return {**best_lawyer, "match_score": best_score}

        except Exception as exc:
            logger.error("lawyer_matching_failed", case_id=case_id, error=str(exc))
            return None

    async def create_match(
        self,
        case_id: str,
        lawyer_id: str,
        user_id: str,
        case_data: dict,
        match_score: float,
    ) -> dict:
        """Create a case match record in Firestore."""
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

    async def get_lawyer_matches(
        self,
        lawyer_id: str,
        status_filter: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get all case matches for a lawyer."""
        try:
            query = self._fb.db.collection("case_matches").where(
                "lawyer_id", "==", lawyer_id
            )
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

    async def respond_to_match(
        self,
        match_id: str,
        lawyer_id: str,
        action: str,  # "accept" | "decline"
        notes: str | None = None,
    ) -> dict | None:
        """Lawyer accepts or declines a case match."""
        try:
            doc_ref = self._fb.db.collection("case_matches").document(match_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None

            match_data = doc.to_dict()
            if match_data.get("lawyer_id") != lawyer_id:
                return None  # Security check

            update = {
                "status": "accepted" if action == "accept" else "declined",
                "responded_at": datetime.now(timezone.utc).isoformat(),
            }
            if notes:
                update["lawyer_notes"] = notes

            doc_ref.update(update)

            # Update lawyer stats
            if action == "accept":
                self._fb.db.collection("lawyers").document(lawyer_id).update(
                    {"cases_accepted": self._fb._firestore.Increment(1)}
                )

            return {**match_data, **update, "id": match_id}
        except Exception as exc:
            logger.error("respond_to_match_failed", match_id=match_id, error=str(exc))
            return None


# ── Module-level factory ───────────────────────────────────────────────────────

_instance: LawyerMatchingService | None = None


def get_lawyer_matching_service() -> LawyerMatchingService:
    """Return a singleton LawyerMatchingService."""
    global _instance
    if _instance is None:
        from services.firebase_service import get_firebase_service
        _instance = LawyerMatchingService(get_firebase_service())
    return _instance
