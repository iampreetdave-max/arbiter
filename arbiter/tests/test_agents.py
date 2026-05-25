"""
test_agents.py — Unit tests for Arbiter's AI agent pipeline.

Tests use mocked GeminiService to avoid real API calls.
Run with: pytest arbiter/tests/ -v
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.case import IntakeData, Party, ProblemType, ResearchData
from models.document import DocumentType


# ── IntakeAgent Tests ─────────────────────────────────────────────────────────────────

class TestIntakeAgent:
    """Tests for IntakeAgent conversational intake flow."""

    @pytest.fixture
    def mock_gemini(self):
        """Mock GeminiService."""
        mock = MagicMock()
        mock.generate = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_first_message_returns_question(self, mock_gemini):
        """IntakeAgent should ask a follow-up question on first message."""
        from agents.intake_agent import IntakeAgent
        mock_gemini.generate.return_value = (
            "I'm sorry to hear that. Could you tell me which state this happened in, "
            "and what was the deposit amount?"
        )
        agent = IntakeAgent(gemini_service=mock_gemini)
        response, complete, data = await agent.process_message(
            user_message="My landlord won't return my deposit",
            conversation_history=[],
        )
        assert isinstance(response, str)
        assert len(response) > 0
        assert complete is False
        assert data is None

    @pytest.mark.asyncio
    async def test_intake_complete_signal(self, mock_gemini):
        """IntakeAgent should detect INTAKE_COMPLETE signal."""
        from agents.intake_agent import IntakeAgent

        extracted = {
            "problem_type": "tenant_dispute",
            "jurisdiction": "Delhi",
            "complainant": {"name": "Preet Singh", "address": "Delhi", "phone": None, "email": None, "role": "complainant"},
            "respondent": {"name": "Ram Sharma", "address": "Delhi", "phone": None, "email": None, "role": "respondent"},
            "incident_date": "2026-03-01",
            "amount_involved": 50000,
            "desired_outcome": "Return of security deposit",
            "key_facts": ["Deposit of Rs.50,000 paid", "Vacated flat 2 months ago", "No refund received"],
            "evidence_available": ["Rent agreement", "Bank transfer receipt"],
            "previous_attempts": "Called landlord twice, no response",
        }

        mock_gemini.generate = AsyncMock(side_effect=[
            f"INTAKE_COMPLETE\nThank you, I have all I need.\n```json\n{json.dumps(extracted)}\n```",
            json.dumps(extracted),  # Second call for extraction
        ])

        agent = IntakeAgent(gemini_service=mock_gemini)
        history = [
            {"role": "user", "content": "My landlord won't return my Rs.50,000 deposit"},
            {"role": "assistant", "content": "Which state? How long ago?"},
        ]
        response, complete, data = await agent.process_message(
            user_message="It's in Delhi, I vacated 2 months ago",
            conversation_history=history,
        )
        assert complete is True

    def test_build_chat_history_conversion(self):
        """Chat history should convert 'assistant' role to 'model' for Gemini."""
        from agents.intake_agent import IntakeAgent
        agent = IntakeAgent(gemini_service=MagicMock())
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        gemini_history = agent._build_chat_history(history)
        assert gemini_history[0]["role"] == "user"
        assert gemini_history[1]["role"] == "model"


# ── ResearchAgent Tests ────────────────────────────────────────────────────────────────

class TestResearchAgent:
    """Tests for ResearchAgent legal research."""

    def _make_intake(self, problem_type: str = "tenant_dispute") -> IntakeData:
        return IntakeData(
            problem_type=ProblemType(problem_type),
            jurisdiction="Delhi",
            complainant=Party(name="Preet Singh", role="complainant"),
            respondent=Party(name="Ram Sharma", role="respondent"),
            desired_outcome="Return of deposit",
            key_facts=["Deposit not returned after 2 months"],
        )

    @pytest.mark.asyncio
    async def test_research_returns_data(self):
        """ResearchAgent should return valid ResearchData."""
        from agents.research_agent import ResearchAgent

        research_output = {
            "relevant_acts": ["Transfer of Property Act, 1882", "Indian Contract Act, 1872"],
            "relevant_sections": ["Transfer of Property Act -- Section 108: Rights of lessee"],
            "case_precedents": [],
            "legal_remedies": ["File complaint in District Court", "Send demand notice"],
            "recommended_document_type": "demand_letter",
            "research_summary": "User has strong claim for deposit recovery under contract law.",
        }

        mock_gemini = MagicMock()
        mock_gemini.generate = AsyncMock(return_value=json.dumps(research_output))

        agent = ResearchAgent(gemini_service=mock_gemini)
        intake = self._make_intake()
        result = await agent.research(intake)

        assert isinstance(result, ResearchData)
        assert len(result.relevant_acts) > 0
        assert result.recommended_document_type == "demand_letter"

    @pytest.mark.asyncio
    async def test_research_handles_malformed_json(self):
        """ResearchAgent should return fallback data on JSON parse failure."""
        from agents.research_agent import ResearchAgent

        mock_gemini = MagicMock()
        mock_gemini.generate = AsyncMock(return_value="not valid json at all")

        agent = ResearchAgent(gemini_service=mock_gemini)
        result = await agent.research(self._make_intake())

        assert isinstance(result, ResearchData)
        assert result.recommended_document_type == "demand_letter"


# ── DraftingAgent Tests ────────────────────────────────────────────────────────────────

class TestDraftingAgent:
    """Tests for DraftingAgent document generation."""

    def _make_intake(self) -> IntakeData:
        return IntakeData(
            problem_type=ProblemType.TENANT_DISPUTE,
            jurisdiction="Delhi",
            complainant=Party(name="Preet Singh", address="123 Main St, Delhi", role="complainant"),
            respondent=Party(name="Ram Sharma", address="456 Park St, Delhi", role="respondent"),
            desired_outcome="Return security deposit of Rs.50,000",
            amount_involved=50000,
            key_facts=["Deposit of Rs.50,000 paid in January 2025", "Vacated April 2025", "No refund"],
        )

    def _make_research(self) -> ResearchData:
        return ResearchData(
            relevant_acts=["Transfer of Property Act, 1882"],
            relevant_sections=["Section 108 -- Rights and liabilities of lessor and lessee"],
            legal_remedies=["Send demand notice", "File suit for recovery"],
            recommended_document_type="demand_letter",
            research_summary="Strong case for deposit recovery.",
        )

    @pytest.mark.asyncio
    async def test_draft_returns_legal_document(self):
        """DraftingAgent should return a LegalDocument with content and disclaimer."""
        from agents.drafting_agent import DraftingAgent
        from models.document import LegalDocument

        mock_gemini = MagicMock()
        mock_gemini.generate = AsyncMock(
            return_value=(
                "Dear Ram Sharma,\n\nI, Preet Singh, hereby demand the return of my security deposit "
                "of Rs.50,000 as per [Transfer of Property Act, Section 108].\n\n"
                "Failure to comply within 30 days will result in legal action.\n\nYours faithfully,\nPreet Singh"
            )
        )

        agent = DraftingAgent()
        agent._gemini = mock_gemini

        doc = await agent.draft(
            intake=self._make_intake(),
            research=self._make_research(),
            user_id="user123",
            case_id="case456",
        )

        assert isinstance(doc, LegalDocument)
        assert len(doc.content) > 50
        assert doc.disclaimer != ""
        assert doc.case_id == "case456"
        assert doc.user_id == "user123"
        assert doc.word_count > 0

    def test_citation_extraction(self):
        """DraftingAgent should extract [Act, Section X] citations from text."""
        from agents.drafting_agent import DraftingAgent
        agent = DraftingAgent()
        agent._gemini = MagicMock()

        text = (
            "As per [Consumer Protection Act, Section 35], you may file a complaint. "
            "Additionally, [Indian Contract Act, Section 74] allows liquidated damages."
        )
        citations = agent._extract_citations(text)
        assert len(citations) == 2
        assert any("Consumer Protection Act" in c.act for c in citations)
