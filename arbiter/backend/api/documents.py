"""
documents.py — FastAPI routes for legal document access, revisions, and payments.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import CurrentUser
from models.document import (
    DocumentResponse,
    DocumentReviseRequest,
    PaymentOrderRequest,
    PaymentOrderResponse,
    PaymentStatus,
)
from services.firebase_service import FirebaseService, get_firebase_service
from services.razorpay_service import RazorpayService, get_razorpay_service
from services.storage_service import StorageService, get_storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> DocumentResponse:
    """
    Get a legal document.

    Returns full content if paid, preview only if pending payment.
    Includes confidence_score, verified_citations, and grounding_sources
    so the frontend can display the accuracy badge.
    """
    doc = firebase.get_document(document_id)
    _assert_doc_access(doc, document_id, user.uid)
    return _raw_to_doc_response(doc)


@router.get("/{document_id}/download-url")
async def get_download_url(
    document_id: str,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> dict:
    """
    Get a signed URL to download the document PDF.
    Only available after payment.
    """
    doc = firebase.get_document(document_id)
    _assert_doc_access(doc, document_id, user.uid)

    if doc.get("payment_status") != PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment required to download this document.",
        )

    if not doc.get("gcs_url"):
        from models.document import Citation
        citations = [Citation(**c) for c in doc.get("citations", [])]
        gcs_url = storage.upload_document(
            document_id=document_id,
            title=doc.get("title", "Legal Document"),
            content=doc.get("content", ""),
            disclaimer=doc.get("disclaimer", ""),
            citations=[c.model_dump() for c in citations],
        )
        firebase.update_document(document_id, {"gcs_url": gcs_url})

    signed_url = storage.get_signed_url(document_id, expiry_minutes=60)
    return {"download_url": signed_url, "expires_in_minutes": 60}


@router.post("/{document_id}/revise", response_model=DocumentResponse)
async def revise_document(
    document_id: str,
    body: DocumentReviseRequest,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> DocumentResponse:
    """
    Revise an existing legal document based on user instructions.

    The user can request changes like:
    - "Make the tone more assertive"
    - "Increase the compensation demand to ₹75,000"
    - "Add a paragraph about the mental harassment suffered"
    - "Translate the document to Hindi"

    Each revision increments revision_count.
    Only available on paid documents.
    """
    from agents.drafting_agent import get_drafting_agent

    doc = firebase.get_document(document_id)
    _assert_doc_access(doc, document_id, user.uid)

    if doc.get("payment_status") != PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Pay for the document first before requesting revisions.",
        )

    current_content = doc.get("content", "")
    if not current_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content not available for revision.",
        )

    revision_count = doc.get("revision_count", 0)
    if revision_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 3 revisions allowed per document. Contact support for additional changes.",
        )

    # ── Save version snapshot BEFORE overwriting ────────────────────────────────────────────────────
    try:
        from services.backup_service import BackupService
        backup_svc = BackupService()
        backup_svc.save_document_version(
            document_id=document_id,
            content=current_content,
            revision_count=revision_count,
            change_description=f"Auto-snapshot before revision {revision_count + 1}: {body.instructions[:80]}",
        )
    except Exception as backup_exc:
        # Never block revision on backup failure — log and continue
        logger.warning(
            "version_snapshot_failed",
            extra={"doc_id": document_id, "error": str(backup_exc)},
        )

    drafting_agent = get_drafting_agent()
    revised_content = await drafting_agent.revise(
        original_content=current_content,
        instructions=body.instructions,
        revision_count=revision_count,
    )

    new_revision_count = revision_count + 1
    firebase.update_document(
        document_id,
        {
            "content": revised_content,
            "revision_count": new_revision_count,
        },
    )

    logger.info(
        "document_revised",
        extra={
            "doc_id": document_id,
            "revision": new_revision_count,
            "instructions_preview": body.instructions[:60],
        },
    )

    refreshed = firebase.get_document(document_id)
    return _raw_to_doc_response(refreshed)


@router.post("/{document_id}/create-order", response_model=PaymentOrderResponse)
async def create_payment_order(
    document_id: str,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
    razorpay: Annotated[RazorpayService, Depends(get_razorpay_service)],
) -> PaymentOrderResponse:
    """Create a Razorpay payment order for a document."""
    from core.config import get_settings
    settings = get_settings()

    doc = firebase.get_document(document_id)
    _assert_doc_access(doc, document_id, user.uid)

    if doc.get("payment_status") == PaymentStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already paid.",
        )

    amount_paise = doc.get("amount_paise", settings.doc_price_paise)
    order = razorpay.create_order(
        amount_paise=amount_paise,
        receipt=document_id,
        notes={"document_id": document_id, "user_id": user.uid},
    )

    firebase.update_document(document_id, {"razorpay_order_id": order["id"]})

    return PaymentOrderResponse(
        order_id=order["id"],
        amount_paise=amount_paise,
        currency="INR",
        razorpay_key_id=settings.razorpay_key_id,
        document_id=document_id,
    )


@router.post("/{document_id}/verify-payment")
async def verify_payment(
    document_id: str,
    payload: dict,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
    razorpay: Annotated[RazorpayService, Depends(get_razorpay_service)],
) -> dict:
    """Verify Razorpay payment signature after checkout completes."""
    doc = firebase.get_document(document_id)
    _assert_doc_access(doc, document_id, user.uid)

    order_id = payload.get("razorpay_order_id", "")
    payment_id = payload.get("razorpay_payment_id", "")
    signature = payload.get("razorpay_signature", "")

    if not all([order_id, payment_id, signature]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment verification fields.",
        )

    is_valid = razorpay.verify_payment_signature(order_id, payment_id, signature)
    if not is_valid:
        firebase.update_document(document_id, {"payment_status": PaymentStatus.FAILED.value})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed. Please contact support.",
        )

    firebase.update_document(
        document_id,
        {
            "payment_status": PaymentStatus.PAID.value,
            "razorpay_payment_id": payment_id,
        },
    )

    logger.info("payment_verified", extra={"doc_id": document_id, "payment_id": payment_id})
    return {"status": "paid", "document_id": document_id}


# ── Helpers ─────────────────────────────────────────────────────────────────────────────────

def _assert_doc_access(doc: dict | None, doc_id: str, user_id: str) -> None:
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")


def _raw_to_doc_response(raw: dict) -> DocumentResponse:
    from models.document import Citation, LEGAL_DISCLAIMER
    payment_status = PaymentStatus(raw.get("payment_status", PaymentStatus.PENDING.value))
    content = raw.get("content", "")
    citations = [Citation(**c) for c in raw.get("citations", [])]

    return DocumentResponse(
        id=raw.get("id", ""),
        case_id=raw.get("case_id", ""),
        type=raw.get("type", "demand_letter"),
        title=raw.get("title", "Legal Document"),
        content=content if payment_status == PaymentStatus.PAID else None,
        preview=content[:300] + "..." if content and payment_status != PaymentStatus.PAID else None,
        citations=citations,
        disclaimer=raw.get("disclaimer", LEGAL_DISCLAIMER),
        payment_status=payment_status,
        gcs_url=raw.get("gcs_url"),
        created_at=raw.get("created_at"),
        amount_paise=raw.get("amount_paise", 29900),
        confidence_score=raw.get("confidence_score", 0.0),
        grounding_sources=raw.get("grounding_sources", []),
        verified_citations=raw.get("verified_citations", 0),
        revision_count=raw.get("revision_count", 0),
        language=raw.get("language", "en"),
    )
