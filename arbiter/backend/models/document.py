"""
document.py — Pydantic models for generated legal documents.

A LegalDocument is the output produced by the DraftingAgent.
It must always carry citations and a disclaimer.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

LEGAL_DISCLAIMER = (
    "DISCLAIMER: This document is AI-generated for informational and "
    "self-help purposes only. It does not constitute legal advice and does "
    "not create an attorney-client relationship. Laws vary by jurisdiction "
    "and change over time. For advice specific to your situation, consult a "
    "qualified legal professional. Arbiter (the service) and its operators "
    "accept no liability for outcomes resulting from use of this document."
)


class DocumentType(str, Enum):
    """Type of legal document Arbiter can generate."""
    DEMAND_LETTER = "demand_letter"              # Most common — pay up or face legal action
    RTI_APPLICATION = "rti_application"          # Right to Information request
    CONSUMER_COMPLAINT = "consumer_complaint"    # NCDRC / district forum complaint
    CEASE_DESIST = "cease_desist"                # Stop doing X or face legal action
    EMPLOYMENT_COMPLAINT = "employment_complaint"  # Labour commissioner complaint
    LEGAL_NOTICE = "legal_notice"                # Formal notice before filing suit


class PaymentStatus(str, Enum):
    """Payment state for document access."""
    PENDING = "pending"     # Document generated, payment not yet made
    PAID = "paid"           # Payment confirmed, full access granted
    FAILED = "failed"       # Payment attempt failed
    REFUNDED = "refunded"   # Payment reversed


class Citation(BaseModel):
    """A specific legal citation backing a claim in the document."""
    act: str = Field(..., description="e.g. 'Consumer Protection Act, 2019'")
    section: str = Field(..., description="e.g. 'Section 35(1)(a)'")
    description: str = Field(..., description="Plain-English explanation of how it applies")
    verified: bool = Field(default=False, description="True if citation was grounded via web search")
    source_url: Optional[str] = Field(default=None, description="URL of verified source")


class LegalDocument(BaseModel):
    """A generated legal document with mandatory citations and disclaimer."""
    id: Optional[str] = None
    case_id: str
    user_id: str
    type: DocumentType
    title: str = Field(..., description="e.g. 'Demand Letter — Security Deposit Recovery'")
    content: str = Field(..., description="Full text of the legal document")
    citations: list[Citation] = Field(
        default_factory=list,
        description="All legal citations supporting claims in the document",
    )
    disclaimer: str = Field(default=LEGAL_DISCLAIMER)
    word_count: int = Field(default=0)
    gcs_url: Optional[str] = Field(default=None, description="GCS URL of stored PDF")
    payment_status: PaymentStatus = PaymentStatus.PENDING
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: Optional[datetime] = None
    amount_paise: int = Field(default=29900, description="Price in paise (₹299 default)")
    # ── Confidence & grounding ──────────────────────────────────────────────────
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="0–100 confidence score based on verified sources",
    )
    grounding_sources: list[str] = Field(
        default_factory=list,
        description="URLs of real sources used to verify legal claims",
    )
    verified_citations: int = Field(
        default=0,
        description="Number of citations confirmed via web grounding",
    )
    # ── Revision tracking ──────────────────────────────────────────────────────
    revision_count: int = Field(default=0, description="Number of times document was revised")
    language: str = Field(default="en", description="Document language: 'en' or 'hi'")

    def has_citations(self) -> bool:
        """Returns True if document has at least one citation."""
        return len(self.citations) > 0

    def is_accessible(self) -> bool:
        """Returns True if user can access full document content."""
        return self.payment_status == PaymentStatus.PAID

    def preview(self, chars: int = 200) -> str:
        """Returns a truncated preview of the document (shown before payment)."""
        if len(self.content) <= chars:
            return self.content
        return self.content[:chars] + "...\n\n[Pay ₹299 to access full document]"

    def confidence_label(self) -> str:
        """Human-readable confidence label."""
        if self.confidence_score >= 80:
            return "High confidence"
        elif self.confidence_score >= 50:
            return "Medium confidence"
        else:
            return "Low confidence"


# ── API Models ────────────────────────────────────────────────────────────────

class DocumentGenerateRequest(BaseModel):
    """Request body to trigger document generation for a case."""
    document_type: DocumentType = Field(
        default=DocumentType.DEMAND_LETTER,
        description="Type of legal document to generate",
    )


class DocumentReviseRequest(BaseModel):
    """Request body to revise an existing document."""
    instructions: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Natural language revision instructions",
        examples=[
            "Make the tone more assertive and increase the compensation demand to ₹75,000.",
            "Add a paragraph about the mental harassment suffered. Reference Section 14 of Consumer Protection Act.",
        ],
    )


class DocumentResponse(BaseModel):
    """API response for a legal document."""
    id: str
    case_id: str
    type: DocumentType
    title: str
    content: Optional[str] = Field(
        default=None,
        description="Full content — only present if payment_status is PAID",
    )
    preview: Optional[str] = Field(
        default=None,
        description="First 300 chars — shown before payment",
    )
    citations: list[Citation] = Field(default_factory=list)
    disclaimer: str
    payment_status: PaymentStatus
    gcs_url: Optional[str] = None
    created_at: Optional[datetime] = None
    amount_paise: int
    # ── Confidence & grounding ──────────────────────────────────────────────────
    confidence_score: float = 0.0
    grounding_sources: list[str] = Field(default_factory=list)
    verified_citations: int = 0
    revision_count: int = 0
    language: str = "en"


class PaymentOrderRequest(BaseModel):
    """Request to create a Razorpay payment order for a document."""
    document_id: str


class PaymentOrderResponse(BaseModel):
    """Razorpay order details returned to frontend for payment."""
    order_id: str
    amount_paise: int
    currency: str = "INR"
    razorpay_key_id: str
    document_id: str
