"""
conftest.py — Shared pytest fixtures for all Arbiter tests.

Run tests with:
    cd HACKATHON
    pytest arbiter/tests/ -v --cov=arbiter/backend --cov-report=term-missing
"""
from __future__ import annotations

import json
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Python path setup ────────────────────────────────────────────────────────────────────────────
sy s.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# ── Environment variables required before importing app ────────────────────────────────────────────
os.environ.setdefault('GEMINI_API_KEY', 'test-gemini-key-xxx')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'test-project')
os.environ.setdefault('FIREBASE_PROJECT_ID', 'test-firebase')
os.environ.setdefault('RAZORPAY_KEY_ID', 'rzp_test_testkey')
os.environ.setdefault('RAZORPAY_KEY_SECRET', 'test_razorpay_secret')
os.environ.setdefault('GCS_BUCKET_NAME', 'test-arbiter-bucket')
os.environ.setdefault('ENVIRONMENT', 'test')


# ── Model factories ────────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_party():
    """A sample Party (complainant or respondent)."""
    from models.case import Party
    return Party(
        name="Preet Singh",
        address="123 Main Street, Delhi 110001",
        phone="9876543210",
        email="preet@example.com",
        role="complainant",
    )


@pytest.fixture
def sample_respondent():
    from models.case import Party
    return Party(
        name="Ram Sharma",
        address="456 Park Avenue, Delhi 110002",
        phone="9123456789",
        role="respondent",
    )


@pytest.fixture
def sample_intake(sample_party, sample_respondent):
    """Standard IntakeData fixture for tenant dispute."""
    from models.case import IntakeData, ProblemType
    return IntakeData(
        problem_type=ProblemType.TENANT_DISPUTE,
        jurisdiction="Delhi",
        complainant=sample_party,
        respondent=sample_respondent,
        incident_date="2026-02-01",
        amount_involved=50000.0,
        desired_outcome="Return of security deposit of ₹50,000",
        key_facts=[
            "Security deposit of ₹50,000 paid in January 2025",
            "Flat vacated on 1st February 2026",
            "No refund received after 60 days",
            "Multiple phone calls ignored by landlord",
        ],
        evidence_available=["Rent agreement", "Bank transfer receipt", "WhatsApp messages"],
        previous_attempts="Called landlord 5 times, sent WhatsApp messages, no response",
        language="en",
    )


@pytest.fixture
def sample_research():
    """Standard ResearchData fixture."""
    from models.case import ResearchData, GroundingSource
    return ResearchData(
        relevant_acts=[
            "Transfer of Property Act, 1882",
            "Indian Contract Act, 1872",
        ],
        relevant_sections=[
            "Transfer of Property Act — Section 108: Rights and liabilities of lessor and lessee",
            "Indian Contract Act — Section 74: Compensation for breach of contract",
        ],
        case_precedents=[],
        legal_remedies=[
            "Send formal demand notice with 30-day deadline",
            "File suit in civil court for money recovery",
        ],
        recommended_document_type="demand_letter",
        research_summary="Strong case for deposit recovery under contract law and Transfer of Property Act.",
        time_limit_days=180,
        authority_to_approach="Civil Court, Delhi",
        confidence_score=75.0,
        grounding_sources=[
            GroundingSource(title="Transfer of Property Act 1882", url="https://indiankanoon.org/doc/123"),
            GroundingSource(title="Indian Contract Act 1872", url="https://legislative.gov.in/act/123"),
        ],
    )


@pytest.fixture
def mock_gemini_service():
    """Mock GeminiService with all methods as AsyncMocks."""
    mock = MagicMock()
    mock.generate = AsyncMock(return_value="Mocked Gemini response")
    mock.generate_with_grounding = AsyncMock(return_value=("Mocked grounded response", []))
    mock.generate_structured = AsyncMock(return_value={"result": "mocked"})
    mock.stream_generate = AsyncMock()
    mock.chat = AsyncMock(return_value="Mocked chat response")
    return mock


@pytest.fixture
def mock_firebase_service():
    """Mock FirebaseService."""
    mock = MagicMock()
    mock.create_case = MagicMock(return_value="case-test-123")
    mock.get_case = MagicMock(return_value={
        "id": "case-test-123",
        "user_id": "user-test-456",
        "status": "intake",
        "conversation_history": [],
        "intake_complete": False,
    })
    mock.update_case = MagicMock()
    mock.get_user_cases = MagicMock(return_value=[])
    mock.create_document = MagicMock(return_value="doc-test-789")
    mock.get_document = MagicMock(return_value={
        "id": "doc-test-789",
        "case_id": "case-test-123",
        "user_id": "user-test-456",
        "type": "demand_letter",
        "title": "Legal Demand Notice",
        "content": "Dear Ram Sharma, I demand return of ₹50,000 deposit.",
        "payment_status": "pending",
        "amount_paise": 29900,
        "confidence_score": 75.0,
        "grounding_sources": [],
        "verified_citations": 0,
        "revision_count": 0,
        "language": "en",
        "citations": [],
    })
    mock.update_document = MagicMock()
    mock.append_conversation_message = MagicMock()
    return mock


@pytest.fixture
def authenticated_user():
    """Mock AuthenticatedUser."""
    from core.security import AuthenticatedUser
    return AuthenticatedUser(
        uid="user-test-456",
        email="test@example.com",
        email_verified=True,
        name="Preet Singh",
    )
