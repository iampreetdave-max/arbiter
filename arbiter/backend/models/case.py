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
    COMPLETE = "complete"       # Document ready for download
    TRACKING = "tracking"       # Following up on sent documents


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
    jurisdiction: str = Field(..., description="Indian state where dispute occurred")
    complainant: Party
    respondent: Party
    incident_date: Optional[str] = Field(default=None, description="When the problem occurred")
    amount_involved: Optional[float] = Field(default=None, description="Money at stake in INR")
    desired_outcome: str = Field(..., description="What the user wants to achieve")
    key_facts: list[str] = Field(default_factory=list, description="Bullet points of key facts")
    evidence_available: list[str] = Field(
        default_factory=list, description="Documents/evidence user has"
    )
    previous_attempts: Optional[str] = Field(
        default=None, description="What user has already tried"
    )


class ResearchData(BaseModel):
    """Output of the ResearchAgent — applicable laws and precedents."""
    relevant_acts: list[str] = Field(default_factory=list, description="e.g. ['Consumer Protection Act 2019, Section 35']")
    relevant_sections: list[str] = Field(default_factory=list, description="Specific sections that apply")
    case_precedents: list[str] = Field(default_factory=list, description="Relevant court judgements")
    legal_remedies: list[str] = Field(default_factory=list, description="Available legal options")
    recommended_document_type: str = Field(default="demand_letter", description="What to draft")
    research_summary: str = Field(default="", description="Plain-English summary of legal position")


class ConversationMessage(BaseModel):
    """A single message in the intake conversation."""
    role: str = Field(..., description="user | assistant")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── API Request/Response Models ───────────────────────────────────────────────

class CaseCreate(BaseModel):
    """Request body to start a new case."""
    initial_message: str = Field(
        ...,
        min_length=10,
        description="User's description of their legal problem",
        examples=["My landlord is refusing to return my ₹50,000 security deposit after I vacated the flat 2 months ago."]
    )


class CaseMessage(BaseModel):
    """Request body to continue intake conversation."""
    message: str = Field(..., min_length=1, description="User's reply to Arbiter's question")


class CaseResponse(BaseModel):
    """API response representing a case."""
    id: str
    user_id: str
    status: CaseStatus
    problem_type: Optional[ProblemType] = None
    jurisdiction: Optional[str] = None
    intake_data: Optional[IntakeData] = None
    research_data: Optional[ResearchData] = None
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    intake_complete: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    next_message: Optional[str] = Field(
        default=None, description="Arbiter's next question or status message"
    )


class CaseListResponse(BaseModel):
    """Paginated list of cases."""
    cases: list[CaseResponse]
    total: int
