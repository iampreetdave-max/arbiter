"""
storage_service.py — Google Cloud Storage for PDF documents.

Handles uploading generated PDFs and creating signed download URLs.
"""
from __future__ import annotations

import io
import logging
from datetime import timedelta
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """
    Uploads legal documents as PDFs to Google Cloud Storage
    and generates time-limited signed download URLs.
    """

    def __init__(self) -> None:
        self._client = storage.Client(project=settings.google_cloud_project)
        self._bucket_name = settings.gcs_bucket_name

    def _get_bucket(self):
        """Return the GCS bucket, creating it if it doesn't exist."""
        try:
            return self._client.get_bucket(self._bucket_name)
        except NotFound:
            bucket = self._client.create_bucket(
                self._bucket_name,
                location=settings.google_cloud_region,
            )
            logger.info("gcs_bucket_created", extra={"bucket": self._bucket_name})
            return bucket

    def _generate_pdf(self, title: str, content: str, disclaimer: str, citations: list[dict]) -> bytes:
        """
        Generate a professional PDF from document content.

        Returns raw PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # Header
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=12,
        )
        story.append(Paragraph("ARBITER", header_style))
        story.append(Paragraph("AI Legal Document Service | arbiter.in", styles["Normal"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a90d9")))
        story.append(Spacer(1, 0.5 * cm))

        # Title
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(Spacer(1, 0.3 * cm))

        # Content
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=11,
            leading=16,
            spaceAfter=8,
        )
        for paragraph in content.split("\n\n"):
            if paragraph.strip():
                story.append(Paragraph(paragraph.replace("\n", "<br/>"), body_style))
                story.append(Spacer(1, 0.2 * cm))

        # Citations
        if citations:
            story.append(Spacer(1, 0.5 * cm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
            story.append(Paragraph("Legal Citations", styles["Heading3"]))
            for cite in citations:
                cite_text = f"- <b>{cite.get('act', '')}</b>, {cite.get('section', '')} - {cite.get('description', '')}"
                story.append(Paragraph(cite_text, styles["Normal"]))
                story.append(Spacer(1, 0.1 * cm))

        # Disclaimer
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            leading=11,
        )
        story.append(Paragraph(disclaimer, disclaimer_style))

        doc.build(story)
        return buffer.getvalue()

    def upload_document(
        self,
        document_id: str,
        title: str,
        content: str,
        disclaimer: str,
        citations: list[dict],
    ) -> str:
        """
        Generate a PDF from document content and upload to GCS.

        Returns the GCS object path (gs://bucket/path).
        """
        pdf_bytes = self._generate_pdf(title, content, disclaimer, citations)
        blob_name = f"documents/{document_id}.pdf"
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")

        gcs_url = f"gs://{self._bucket_name}/{blob_name}"
        logger.info("document_uploaded", extra={"doc_id": document_id, "gcs_url": gcs_url})
        return gcs_url

    def get_signed_url(self, document_id: str, expiry_minutes: int = 60) -> str:
        """
        Generate a signed URL for downloading a document PDF.

        Args:
            document_id: Document ID (used as blob name).
            expiry_minutes: How long the URL is valid.

        Returns:
            HTTPS signed URL.
        """
        blob_name = f"documents/{document_id}.pdf"
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiry_minutes),
            method="GET",
            response_disposition=f'attachment; filename="arbiter-document-{document_id[:8]}.pdf"',
        )
        logger.info("signed_url_generated", extra={"doc_id": document_id})
        return url


# Singleton
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Return module-level StorageService singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
