"""
backup_service.py — Document versioning and Firestore backup.

1. DOCUMENT VERSIONING: Saves previous version before every revision. Max 10 per doc.
2. FIRESTORE BACKUP: Exports entire DB to GCS (gs://{bucket}/firestore-backups/{date}/)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

MAX_VERSIONS_PER_DOCUMENT = 10


class BackupService:
    """Handles document version history and Firestore database backups."""

    def __init__(self) -> None:
        from services.firebase_service import get_firebase_service
        self._fb = get_firebase_service()

    def save_document_version(
        self,
        document_id: str,
        content: str,
        revision_count: int,
        change_description: str = "",
    ) -> str:
        """
        Save the current document content as a version snapshot.
        Called BEFORE applying a revision so the old version is preserved.
        """
        version_data = {
            "document_id": document_id,
            "content": content,
            "revision_number": revision_count,
            "change_description": change_description or f"Snapshot before revision {revision_count + 1}",
            "created_at": datetime.utcnow().isoformat(),
            "word_count": len(content.split()),
        }
        version_ref = self._fb._db.collection("document_versions").add(version_data)
        version_id = version_ref[1].id
        logger.info("version_saved", extra={"document_id": document_id, "version_id": version_id})
        self._prune_old_versions(document_id)
        return version_id

    def get_document_versions(self, document_id: str) -> list[dict]:
        """Return all version snapshots for a document, newest first."""
        query = (
            self._fb._db.collection("document_versions")
            .where("document_id", "==", document_id)
            .order_by("revision_number", direction="DESCENDING")
            .limit(MAX_VERSIONS_PER_DOCUMENT)
        )
        docs = query.stream()
        versions = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["preview"] = data.get("content", "")[:200] + "..."
            data.pop("content", None)
            versions.append(data)
        return versions

    def restore_document_version(self, document_id: str, version_id: str) -> Optional[str]:
        """Restore a document to a specific version."""
        version_ref = self._fb._db.collection("document_versions").document(version_id)
        version_doc = version_ref.get()
        if not version_doc.exists:
            return None
        data = version_doc.to_dict()
        if data.get("document_id") != document_id:
            return None
        restored_content = data["content"]
        self._fb.update_document(document_id, {
            "content": restored_content,
            "restored_from_version": version_id,
            "restored_at": datetime.utcnow().isoformat(),
        })
        return restored_content

    def _prune_old_versions(self, document_id: str) -> None:
        """Delete versions beyond MAX_VERSIONS_PER_DOCUMENT."""
        query = (
            self._fb._db.collection("document_versions")
            .where("document_id", "==", document_id)
            .order_by("revision_number", direction="DESCENDING")
        )
        all_versions = list(query.stream())
        if len(all_versions) > MAX_VERSIONS_PER_DOCUMENT:
            for old_version in all_versions[MAX_VERSIONS_PER_DOCUMENT:]:
                old_version.reference.delete()

    async def trigger_firestore_backup(self, backup_bucket: str) -> dict:
        """Trigger a Firestore managed export to GCS."""
        import asyncio
        from datetime import date as date_cls
        backup_path = f"gs://{backup_bucket}/firestore-backups/{date_cls.today().isoformat()}"
        try:
            from google.cloud import firestore_admin_v1
            project_id = self._fb._db.project
            client = firestore_admin_v1.FirestoreAdminAsyncClient()
            database_name = f"projects/{project_id}/databases/(default)"
            request = firestore_admin_v1.ExportDocumentsRequest(
                name=database_name,
                output_uri_prefix=backup_path,
            )
            loop = asyncio.get_event_loop()
            operation = await loop.run_in_executor(None, lambda: client.export_documents(request=request))
            return {
                "status": "started",
                "backup_path": backup_path,
                "operation_name": operation.operation.name,
                "initiated_at": datetime.utcnow().isoformat(),
            }
        except ImportError:
            return {"status": "unavailable", "message": "Install google-cloud-firestore to enable backups", "backup_path": backup_path}
        except Exception as exc:
            logger.error("firestore_backup_failed", extra={"error": str(exc)})
            return {"status": "error", "error": str(exc), "backup_path": backup_path}


_backup_service: Optional[BackupService] = None


def get_backup_service() -> BackupService:
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service
