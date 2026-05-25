"""
case.py — Pydantic models for legal cases.

A Case tracks a user's legal problem from intake through document generation.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    """Lifecycle status of a case."""
    INTAKE = "intake"           # Collecting problem details
    RESEARCH = "research"       # AI looking up applicable laws
    DRAFTING = "drafting"       # AI generating document
    DRAFT_READY = "draft_ready" # Document generated, awaiting payment
    COMPLETE = "complete"       # Document ready for download
    PAID = "paid"               # Payment confirmed
    TRACKING = "tracking"       # Following up on sent documents
    ESCALATED = "escalated"     # Escalated to a lawyer
    CLOSED = "closed"           # Case closed


class CaseOutcome(str, Enum):
    """What happened after the user sent their document."""
    PENDING = "pending"             # Document sent, waiting for response
    RESOLVED = "resolved"           # Issue resolved in user's favour
    PARTIAL = "partial"             # Partial resolution
    ESCALATED = "escalated"         # Had to escalate to court/authority
    NO_RESPONSE = "no_response"     # Opposing party didn't respond


class ProblemType(str, Enum):
    """Category of legal problem."""
    TENANT_DISPUTE = "tenant_dispute"       # Deposit not returned, illegal eviction
    EMPLOYMENT = "employment"               # Unpaid wages, wrongful termination
    CONSUMER = "consumer"                   # Product/service fraud, e-commerce scam
    RTI = "rti"                             # Right to Information application
    HARASSMENT = "harassment"               # Workplace or online harassment
    DEBT_RECOVERY = "debt_recovery"         # Money owed by individual/company
    OTHER = "other"                         # Everything else


class Party(BaseModel):
    """A person or entity involved in the legal dispute."""
    name: str = Field(..., description="Full legal name")
    address: Optional[str] = Field(default=None, description="Full postal address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    email: Optional[str] = Field(default=None, description="Contact email address")
    role: str = Field(default="respondent", description="complainant | respondent | witness")


class IntakeData(BaseModel):
    """Structured data extracted by the IntakeAgent from the user's description."""
    problem_type: ProblemType
    country_code: str = Field(
        default="IN",
        description="ISO 3166-1 alpha-2 country code (IN, US, GB, CA, AU)"
    )
    jurisdiction: str = Field(..., description="State/province/city where dispute occurred")
    complainant: Party
    respondent: Party
    incident_date: Optional[str] = Field(default=None, description="When the problem occurred")
    amount_involved: Optional[float] = Field(default=None, description="Money at stake")
    currency: str = Field(default="INR", description="Currency code (INR, USD, GBP, CAD, AUD)")
    desired_outcome: str = Field(..., description="What the user wants to achieve")
    key_facts: list[str] = Field(default_factory=list, description="Bullet points of key facts")
    evidence_available: list[str] = Field(
        default_factory=list, description="Documents/evidence user has"
    )
    previous_attempts: Optional[str] = Field(
        default=None, description="What user has already tried"
    )
    language: str = Field(default="en", description="Detected language: 'en' or 'hi'")


class GroundingSource(BaseModel):
    """A verified source used during AI legal research."""
    title: str = Field(..., description="Title of the source (e.g. 'Consumer Protection Act 2019')")
    url: str = Field(..., description="URL of the verified source")


class ResearchData(BaseModel):
    """Output of the ResearchAgent — applicable laws and precedents."""
    relevant_acts: list[str] = Field(
        default_factory=list,
        description="e.g. ['Consumer Protection Act 2019, Section 35']",
    )
    relevant_sections: list[str] = Field(
        default_factory=list,
        description="Specific sections that apply",
    )
    case_precedents: list[str] = Field(
        default_factory=list,
        description="Relevant court judgements",
    )
    legal_remedies: list[str] = Field(
        default_factory=list,
        description="Available legal options",
    )
    recommended_document_type: str = Field(
        default="demand_letter",
        description="What to draft",
    )
    research_summary: str = Field(default="", description="Plain-English summary of legal position")
    time_limit_days: Optional[int] = Field(
        default=None,
        description="Statutory time limit to file complaint (days)",
    )
    authority_to_approach: Optional[str] = Field(
        default=None,
        description="e.g. 'District Consumer Commission, Delhi'",
    )
    confidence_score: float = Field(
        default=0.0,
        description="0-100 confidence based on verified grounding sources",
    )
    grounding_sources: list[GroundingSource] = Field(
        default_factory=list,
        description="Real-web sources used to ground this research",
    )


class ConversationMessage(BaseModel):
    """A single message in the intake conversation."""
    role: str = Field(..., description="user | assistant")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CaseCreate(BaseModel):
    """Request body to start a new case."""
    initial_message: str = Field(
        ...,
        min_length=10,
        description="User's description of their legal problem",
        examples=["My landlord is refusing to return my security deposit after I vacated the flat 2 months ago."]
    )
    country_code: Optional[str] = Field(
        default=None,
        description="User's country (IN, US, GB, CA, AU). If not provided, AI will ask."
    )


class CaseMessage(BaseModel):
    """Request body to continue intake conversation."""
    message: str = Field(..., min_length=1, description="User's reply to Arbiter's question")


class CaseOutcomeUpdate(BaseModel):
    """Request body to update the outcome of a case."""
    outcome: CaseOutcome
    outcome_notes: Optional[str] = Field(
        default=None,
        description="Optional user notes about what happened",
        max_length=500,
    )


class CaseResponse(BaseModel):
    """API response representing a case."""
    id: str
    user_id: str
    status: CaseStatus
    problem_type: Optional[ProblemType] = None
    country_code: Optional[str] = Field(default=None, description="ISO country code")
    jurisdiction: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    intake_data: Optional[IntakeData] = None
    research_data: Optional[ResearchData] = None
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    intake_complete: bool = False
    outcome: Optional[CaseOutcome] = None
    outcome_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    next_message: Optional[str] = Field(
        default=None, description="Arbiter's next question or status message"
    )


class CaseListResponse(BaseModel):
    """Paginated list of cases."""
    cases: list[CaseResponse]
    total: int
