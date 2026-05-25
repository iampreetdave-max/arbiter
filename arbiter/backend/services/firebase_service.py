"""
firebase_service.py — Firebase Firestore database operations.

All Firestore reads and writes go through this service.
Collections: users, cases, documents, reminders.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import AsyncClient

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _init_firebase() -> None:
    """Initialise Firebase Admin SDK (idempotent)."""
    if firebase_admin._apps:
        return

    if settings.firebase_service_account_path:
        cred = credentials.Certificate(settings.firebase_service_account_path)
    else:
        # Use Application Default Credentials (works on Cloud Run automatically)
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
    logger.info("firebase_initialised", extra={"project": settings.firebase_project_id})


# Initialise on module load
_init_firebase()


def get_db() -> Any:
    """Return synchronous Firestore client."""
    return firestore.client()


class FirebaseService:
    """
    CRUD operations for all Arbiter Firestore collections.

    Collections:
        /users/{user_id}
        /cases/{case_id}
        /documents/{document_id}
        /reminders/{reminder_id}
    """

    def __init__(self) -> None:
        self._db = get_db()

    # ── Users ──────────────────────────────────────────────────────────────────

    def get_user(self, user_id: str) -> Optional[dict]:
        """Fetch a user document by UID."""
        doc = self._db.collection("users").document(user_id).get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None

    def create_or_update_user(self, user_id: str, data: dict) -> dict:
        """Create or merge-update a user document."""
        data["updated_at"] = datetime.utcnow()
        self._db.collection("users").document(user_id).set(data, merge=True)
        logger.info("user_upserted", extra={"user_id": user_id})
        return {"id": user_id, **data}

    # ── Cases ──────────────────────────────────────────────────────────────────

    def create_case(self, case_data: dict) -> str:
        """Create a new case and return its generated ID."""
        case_data["created_at"] = datetime.utcnow()
        case_data["updated_at"] = datetime.utcnow()
        _, ref = self._db.collection("cases").add(case_data)
        logger.info("case_created", extra={"case_id": ref.id, "user_id": case_data.get("user_id")})
        return ref.id

    def get_case(self, case_id: str) -> Optional[dict]:
        """Fetch a case by ID."""
        doc = self._db.collection("cases").document(case_id).get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None

    def update_case(self, case_id: str, updates: dict) -> None:
        """Partial update a case document."""
        updates["updated_at"] = datetime.utcnow()
        self._db.collection("cases").document(case_id).update(updates)
        logger.info("case_updated", extra={"case_id": case_id, "fields": list(updates.keys())})

    def get_user_cases(self, user_id: str, limit: int = 20) -> list[dict]:
        """Return all cases for a user, newest first."""
        docs = (
            self._db.collection("cases")
            .where("user_id", "==", user_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def append_conversation_message(
        self, case_id: str, role: str, content: str
    ) -> None:
        """Append a message to a case's conversation_history array."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
        }
        self._db.collection("cases").document(case_id).update(
            {
                "conversation_history": firestore.ArrayUnion([message]),
                "updated_at": datetime.utcnow(),
            }
        )

    # ── Documents ──────────────────────────────────────────────────────────────

    def create_document(self, document_data: dict) -> str:
        """Store a generated legal document and return its ID."""
        document_data["created_at"] = datetime.utcnow()
        _, ref = self._db.collection("documents").add(document_data)
        logger.info(
            "document_created",
            extra={"doc_id": ref.id, "case_id": document_data.get("case_id")},
        )
        return ref.id

    def get_document(self, document_id: str) -> Optional[dict]:
        """Fetch a document by ID."""
        doc = self._db.collection("documents").document(document_id).get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None

    def update_document(self, document_id: str, updates: dict) -> None:
        """Partial update a document (e.g. set payment_status = paid)."""
        self._db.collection("documents").document(document_id).update(updates)
        logger.info("document_updated", extra={"doc_id": document_id})

    def get_case_documents(self, case_id: str) -> list[dict]:
        """Return all documents generated for a case."""
        docs = (
            self._db.collection("documents")
            .where("case_id", "==", case_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    # ── Reminders ──────────────────────────────────────────────────────────────

    def create_reminder(self, reminder_data: dict) -> str:
        """Schedule a reminder for deadline follow-up."""
        reminder_data["created_at"] = datetime.utcnow()
        reminder_data["sent"] = False
        _, ref = self._db.collection("reminders").add(reminder_data)
        logger.info("reminder_created", extra={"reminder_id": ref.id})
        return ref.id

    def get_pending_reminders(self, before: datetime) -> list[dict]:
        """Return unsent reminders due before a given datetime."""
        docs = (
            self._db.collection("reminders")
            .where("sent", "==", False)
            .where("remind_at", "<=", before)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def mark_reminder_sent(self, reminder_id: str) -> None:
        """Mark a reminder as sent."""
        self._db.collection("reminders").document(reminder_id).update({"sent": True})


# Module-level singleton
_firebase_service: Optional[FirebaseService] = None


def get_firebase_service() -> FirebaseService:
    """Return module-level FirebaseService singleton."""
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseService()
    return _firebase_service
