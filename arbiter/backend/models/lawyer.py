"""
lawyer.py — Pydantic models for lawyer profiles and case matching.

Lawyers register on Arbiter as verified service providers.
They select specialties and receive matched cases from users who need escalation.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class LawyerSpecialty(str, Enum):
    """Legal practice areas a lawyer can specialise in."""
    CONSUMER = "consumer"               # Consumer disputes, product liability
    EMPLOYMENT = "employment"           # Labour law, wrongful termination, wages
    TENANT = "tenant"                   # Landlord disputes, eviction, deposits
    CRIMINAL = "criminal"               # Criminal defence
    FAMILY = "family"                   # Divorce, custody, domestic violence
    CORPORATE = "corporate"             # Business law, contracts, company disputes
    IMMIGRATION = "immigration"         # Visa, citizenship, deportation
    PROPERTY = "property"               # Real estate, land disputes, RERA
    CIVIL = "civil"                     # General civil litigation
    CYBER = "cyber"                     # Cyber crime, online fraud, defamation
    RTI = "rti"                         # Right to Information (India)
    DEBT_RECOVERY = "debt_recovery"     # Loan recovery, cheque bounce
    OTHER = "other"                     # Other specialties


class LawyerStatus(str, Enum):
    """Status of a lawyer's registration."""
    PENDING = "pending"         # Submitted, awaiting admin verification
    VERIFIED = "verified"       # Approved and active
    SUSPENDED = "suspended"     # Temporarily disabled
    REJECTED = "rejected"       # Application rejected


# ── Core lawyer profile ──────────────────────────────────────────────────────

class LawyerProfile(BaseModel):
    """Full lawyer profile as stored in Firestore."""
    id: str = Field(..., description="Firestore document ID")
    user_id: str = Field(..., description="Firebase Auth UID")
    full_name: str = Field(..., description="Full legal name as on bar registration")
    bar_registration_number: str = Field(..., description="Bar Council registration number")
    country_code: str = Field(..., description="ISO 3166 country code (IN, US, GB, CA, AU)")
    jurisdiction: str = Field(..., description="State/province/jurisdiction of practice")
    specialties: list[LawyerSpecialty] = Field(
        ..., min_length=1, max_length=5,
        description="Legal specialties (1–5)"
    )
    years_of_experience: int = Field(..., ge=0, le=70, description="Years practising law")
    languages: list[str] = Field(
        default_factory=lambda: ["en"],
        description="Languages spoken (e.g. ['en', 'hi'])"
    )
    available_for_pro_bono: bool = Field(
        default=False,
        description="Whether lawyer accepts pro bono cases"
    )
    status: LawyerStatus = Field(default=LawyerStatus.PENDING)
    bio: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="Professional bio (50–1000 chars)"
    )
    contact_email: str = Field(..., description="Professional contact email")
    contact_phone: Optional[str] = Field(default=None, description="Optional contact phone")
    website_url: Optional[str] = Field(default=None, description="Firm or personal website")
    profile_photo_url: Optional[str] = Field(default=None, description="GCS URL for profile photo")
    # Metrics (updated automatically)
    cases_received: int = Field(default=0, description="Total cases matched to this lawyer")
    cases_accepted: int = Field(default=0, description="Cases the lawyer accepted")
    cases_resolved: int = Field(default=0, description="Cases marked resolved")
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average user rating (0–5)")
    rating_count: int = Field(default=0, description="Number of ratings received")
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None


class LawyerCaseMatch(BaseModel):
    """A case that has been matched to a lawyer."""
    id: str = Field(..., description="Match document ID")
    lawyer_id: str
    case_id: str
    user_id: str
    case_title: str
    case_problem_type: str
    case_country_code: str
    case_jurisdiction: str
    match_score: float = Field(..., ge=0.0, le=1.0, description="Match quality score")
    status: str = Field(default="pending", description="pending | accepted | declined | completed")
    lawyer_notes: Optional[str] = Field(default=None, description="Lawyer's notes on the case")
    created_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None


# ── API request/response models ──────────────────────────────────────────────

class LawyerRegisterRequest(BaseModel):
    """Request body to register as a lawyer."""
    full_name: str = Field(..., min_length=2, max_length=100)
    bar_registration_number: str = Field(..., min_length=3, max_length=50)
    country_code: str = Field(..., min_length=2, max_length=2)
    jurisdiction: str = Field(..., min_length=2, max_length=100)
    specialties: list[LawyerSpecialty] = Field(..., min_length=1, max_length=5)
    years_of_experience: int = Field(..., ge=0, le=70)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    available_for_pro_bono: bool = False
    bio: str = Field(..., min_length=50, max_length=1000)
    contact_email: str
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None


class LawyerUpdateRequest(BaseModel):
    """Request body to update lawyer profile."""
    specialties: Optional[list[LawyerSpecialty]] = None
    available_for_pro_bono: Optional[bool] = None
    bio: Optional[str] = Field(default=None, min_length=50, max_length=1000)
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    languages: Optional[list[str]] = None


class LawyerResponse(BaseModel):
    """Lawyer profile returned by the API (safe for public view)."""
    id: str
    full_name: str
    country_code: str
    jurisdiction: str
    specialties: list[LawyerSpecialty]
    years_of_experience: int
    languages: list[str]
    available_for_pro_bono: bool
    status: LawyerStatus
    bio: str
    cases_resolved: int
    rating: float
    rating_count: int
    created_at: Optional[datetime] = None


class LawyerMatchResponse(BaseModel):
    """Response when a user requests lawyer escalation."""
    matched: bool
    lawyer: Optional[LawyerResponse] = None
    match_id: Optional[str] = None
    message: str


class CaseMatchUpdateRequest(BaseModel):
    """Lawyer accepts or declines a case match."""
    action: str = Field(..., description="accept | decline")
    notes: Optional[str] = Field(default=None, max_length=500)
