"""
documents.py — FastAPI routes for legal document access and payments.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import CurrentUser
from models.document import DocumentResponse, PaymentOrderRequest, PaymentOrderResponse, PaymentStatus
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


@router.post("/{document_id}/create-order", response_model=PaymentOrderResponse)
async def create_payment_order(
    document_id: str,
    user: CurrentUser,
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
    razorpay: Annotated[RazorpayService, Depends(get_razorpay_service)],
) -> PaymentOrderResponse:
    """
    Create a Razorpay payment order for a document.

    Returns order details needed by the Razorpay checkout widget.
    """
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
    """
    Verify Razorpay payment signature after checkout completes.

    Call this from the frontend after successful payment to unlock the document.
    """
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _assert_doc_access(doc: dict | None, doc_id: str, user_id: str) -> None:
    """Raise 404/403 if document doesn't exist or doesn't belong to user."""
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")


def _raw_to_doc_response(raw: dict) -> DocumentResponse:
    """Convert raw Firestore dict to DocumentResponse."""
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
    )
