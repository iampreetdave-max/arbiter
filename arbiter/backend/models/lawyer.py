"""
lawyer.py — Pydantic models for lawyer profiles and case matching.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class LawyerSpecialty(str, Enum):
    CONSUMER = "consumer"
    EMPLOYMENT = "employment"
    TENANT = "tenant"
    CRIMINAL = "criminal"
    FAMILY = "family"
    CORPORATE = "corporate"
    IMMIGRATION = "immigration"
    PROPERTY = "property"
    CIVIL = "civil"
    CYBER = "cyber"
    RTI = "rti"
    DEBT_RECOVERY = "debt_recovery"
    OTHER = "other"


class LawyerStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class LawyerProfile(BaseModel):
    id: str = Field(..., description="Firestore document ID")
    user_id: str = Field(..., description="Firebase Auth UID")
    full_name: str = Field(..., description="Full legal name as on bar registration")
    bar_registration_number: str = Field(..., description="Bar Council registration number")
    country_code: str = Field(..., description="ISO 3166 country code (IN, US, GB, CA, AU)")
    jurisdiction: str = Field(..., description="State/province/jurisdiction of practice")
    specialties: list[LawyerSpecialty] = Field(..., min_length=1, max_length=5)
    years_of_experience: int = Field(..., ge=0, le=70)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    available_for_pro_bono: bool = Field(default=False)
    status: LawyerStatus = Field(default=LawyerStatus.PENDING)
    bio: str = Field(..., min_length=50, max_length=1000)
    contact_email: str
    contact_phone: Optional[str] = Field(default=None)
    website_url: Optional[str] = Field(default=None)
    profile_photo_url: Optional[str] = Field(default=None)
    cases_received: int = Field(default=0)
    cases_accepted: int = Field(default=0)
    cases_resolved: int = Field(default=0)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    rating_count: int = Field(default=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None


class LawyerCaseMatch(BaseModel):
    id: str = Field(..., description="Match document ID")
    lawyer_id: str
    case_id: str
    user_id: str
    case_title: str
    case_problem_type: str
    case_country_code: str
    case_jurisdiction: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    status: str = Field(default="pending")
    lawyer_notes: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None


class LawyerRegisterRequest(BaseModel):
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
    specialties: Optional[list[LawyerSpecialty]] = None
    available_for_pro_bono: Optional[bool] = None
    bio: Optional[str] = Field(default=None, min_length=50, max_length=1000)
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    languages: Optional[list[str]] = None


class LawyerResponse(BaseModel):
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
    matched: bool
    lawyer: Optional[LawyerResponse] = None
    match_id: Optional[str] = None
    message: str


class CaseMatchUpdateRequest(BaseModel):
    action: str = Field(..., description="accept | decline")
    notes: Optional[str] = Field(default=None, max_length=500)
