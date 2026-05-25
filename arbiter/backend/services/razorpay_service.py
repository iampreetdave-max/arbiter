"""
razorpay_service.py — Razorpay payment integration.

Handles creating payment orders, verifying webhook signatures,
and confirming payment success for document unlocking.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

import razorpay

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RazorpayService:
    """
    Wrapper around the Razorpay Python SDK.

    Handles order creation and webhook signature verification.
    All amounts are in paise (1 INR = 100 paise).
    """

    def __init__(self) -> None:
        self._client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )

    def create_order(
        self,
        amount_paise: int,
        receipt: str,
        notes: Optional[dict] = None,
    ) -> dict:
        """
        Create a Razorpay order for a document payment.

        Args:
            amount_paise: Amount in paise (e.g. 29900 for ₹299).
            receipt: Unique receipt ID (document_id works well).
            notes: Optional metadata.

        Returns:
            Razorpay order dict with id, amount, currency, status.
        """
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt[:40],  # Razorpay: max 40 chars
            "notes": notes or {},
            "payment_capture": 1,  # Auto-capture on payment
        }
        try:
            order = self._client.order.create(data=order_data)
            logger.info(
                "razorpay_order_created",
                extra={"order_id": order["id"], "amount_paise": amount_paise},
            )
            return order
        except Exception as exc:
            logger.error("razorpay_order_failed", extra={"error": str(exc)})
            raise RuntimeError(f"Failed to create payment order: {exc}") from exc

    def verify_webhook_signature(
        self, payload_body: bytes, signature: str
    ) -> bool:
        """
        Verify that a webhook request genuinely came from Razorpay.

        Args:
            payload_body: Raw request body bytes.
            signature: Value of the X-Razorpay-Signature header.

        Returns:
            True if signature is valid, False otherwise.
        """
        if not settings.razorpay_webhook_secret:
            logger.warning("razorpay_webhook_secret_not_set")
            return False

        expected = hmac.new(
            settings.razorpay_webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verify the payment signature returned by Razorpay checkout.

        Args:
            order_id: Razorpay order ID.
            payment_id: Razorpay payment ID.
            signature: Razorpay signature from checkout callback.

        Returns:
            True if payment is genuine.
        """
        try:
            self._client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                }
            )
            return True
        except Exception:
            return False

    def fetch_payment(self, payment_id: str) -> dict:
        """Fetch payment details by payment ID."""
        return self._client.payment.fetch(payment_id)


# Singleton
_razorpay_service: Optional[RazorpayService] = None


def get_razorpay_service() -> RazorpayService:
    """Return module-level RazorpayService singleton."""
    global _razorpay_service
    if _razorpay_service is None:
        _razorpay_service = RazorpayService()
    return _razorpay_service
