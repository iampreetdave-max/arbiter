"""
payments.py — Razorpay webhook handler.

Razorpay calls this endpoint when a payment event occurs.
We verify the signature and update document payment status accordingly.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request, status

from models.document import PaymentStatus
from services.firebase_service import get_firebase_service
from services.razorpay_service import get_razorpay_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhook")
async def razorpay_webhook(request: Request) -> dict:
    """
    Razorpay webhook endpoint.

    Razorpay sends payment.captured and payment.failed events here.
    We verify the signature and update document status accordingly.

    Configure in Razorpay Dashboard → Webhooks → Add URL:
        https://your-api-domain.com/payments/webhook
    """
    payload_bytes = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    razorpay = get_razorpay_service()
    firebase = get_firebase_service()

    if not razorpay.verify_webhook_signature(payload_bytes, signature):
        logger.warning("webhook_signature_invalid", extra={"sig": signature[:20]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature.",
        )

    try:
        event = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    event_type = event.get("event", "")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id", "")
    order_id = payment_entity.get("order_id", "")
    notes = payment_entity.get("notes", {})
    document_id = notes.get("document_id", "")

    logger.info("webhook_received", extra={"event": event_type, "payment_id": payment_id})

    if not document_id:
        return {"status": "ignored"}

    if event_type == "payment.captured":
        firebase.update_document(
            document_id,
            {
                "payment_status": PaymentStatus.PAID.value,
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
            },
        )
        logger.info("payment_captured", extra={"doc_id": document_id, "payment_id": payment_id})

    elif event_type == "payment.failed":
        firebase.update_document(document_id, {"payment_status": PaymentStatus.FAILED.value})
        logger.warning("payment_failed", extra={"doc_id": document_id})

    return {"status": "ok", "event": event_type}
