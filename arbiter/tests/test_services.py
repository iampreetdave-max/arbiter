"""
test_services.py — Unit tests for backend services.

Tests GeminiService, BackupService, and sanitization logic.
All external API calls are mocked.
"""
from __future__ import annotations

import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('GEMINI_API_KEY', 'test-gemini-key')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'test-project')
os.environ.setdefault('FIREBASE_PROJECT_ID', 'test-firebase')
os.environ.setdefault('RAZORPAY_KEY_ID', 'rzp_test_key')
os.environ.setdefault('RAZORPAY_KEY_SECRET', 'test_secret')
os.environ.setdefault('GCS_BUCKET_NAME', 'test-bucket')


class TestGeminiServiceRetry:
    """Test retry logic and error handling in GeminiService."""

    @pytest.mark.asyncio
    async def test_generate_retries_on_quota_exceeded(self):
        """GeminiService should retry on ResourceExhausted up to max_retries."""
        from services.gemini_service import GeminiService
        from google.api_core.exceptions import ResourceExhausted

        with patch('services.gemini_service.genai'):
            svc = GeminiService()
            call_count = 0

            def mock_generate(prompt):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ResourceExhausted("Quota exceeded")
                mock_resp = MagicMock()
                mock_resp.text = "Success after retries"
                return mock_resp

            svc._model.generate_content = mock_generate

            import asyncio
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await svc.generate("test prompt", max_retries=3)

            assert result == "Success after retries"
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_generate_raises_after_max_retries(self):
        """Should raise RuntimeError after exhausting retries."""
        from services.gemini_service import GeminiService
        from google.api_core.exceptions import ResourceExhausted

        with patch('services.gemini_service.genai'):
            svc = GeminiService()
            svc._model.generate_content = MagicMock(side_effect=ResourceExhausted("Quota"))

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="quota"):
                    await svc.generate("test", max_retries=2)

    @pytest.mark.asyncio
    async def test_generate_with_grounding_falls_back(self):
        """generate_with_grounding should fall back to regular generate on error."""
        from services.gemini_service import GeminiService

        with patch('services.gemini_service.genai'):
            svc = GeminiService()
            # Make grounded model fail
            with patch.object(
                GeminiService, 'generate',
                new_callable=AsyncMock,
                return_value="Fallback response"
            ):
                # Patch GenerativeModel to raise
                with patch('services.gemini_service.GenerativeModel') as mock_model_cls:
                    mock_model_cls.return_value.generate_content.side_effect = Exception("grounding unavailable")
                    text, sources = await svc.generate_with_grounding("test prompt")

            assert text == "Fallback response"
            assert sources == []


class TestGeminiServiceStreaming:
    """Test streaming generation."""

    @pytest.mark.asyncio
    async def test_stream_generate_yields_chunks(self):
        """stream_generate should yield text chunks."""
        from services.gemini_service import GeminiService

        with patch('services.gemini_service.genai'):
            svc = GeminiService()

            # Mock stream response
            chunks = [MagicMock(text="Hello "), MagicMock(text="World")]
            svc._model.generate_content = MagicMock(return_value=iter(chunks))

            results = []
            async for chunk in svc.stream_generate("test"):
                results.append(chunk)

            assert results == ["Hello ", "World"]

    @pytest.mark.asyncio
    async def test_stream_generate_handles_empty_chunks(self):
        """Chunks with no text should be skipped."""
        from services.gemini_service import GeminiService

        with patch('services.gemini_service.genai'):
            svc = GeminiService()
            chunks = [
                MagicMock(text="Real text"),
                MagicMock(text=None),
                MagicMock(text="More text"),
            ]
            svc._model.generate_content = MagicMock(return_value=iter(chunks))

            results = []
            async for chunk in svc.stream_generate("test"):
                results.append(chunk)

            assert results == ["Real text", "More text"]


class TestDraftingAgentRevise:
    """Tests for the revision feature."""

    @pytest.mark.asyncio
    async def test_revise_calls_gemini_generate(self):
        from agents.drafting_agent import DraftingAgent

        original = "Dear Ram Sharma, I demand return of ₹50,000."
        instructions = "Make the tone more assertive and add a deadline."

        with patch('services.gemini_service.genai'):
            agent = DraftingAgent()
            agent._gemini = MagicMock()
            agent._gemini.generate = AsyncMock(return_value="Revised: Dear Ram Sharma, DEMAND...")

            result = await agent.revise(original, instructions, revision_count=0)

            assert "Revised" in result
            agent._gemini.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_draft_with_content_override_skips_gemini(self):
        """When content_override is provided, Gemini should NOT be called."""
        from agents.drafting_agent import DraftingAgent
        from models.case import IntakeData, Party, ProblemType, ResearchData

        intake = IntakeData(
            problem_type=ProblemType.TENANT_DISPUTE,
            jurisdiction="Delhi",
            complainant=Party(name="A", role="complainant"),
            respondent=Party(name="B", role="respondent"),
            desired_outcome="Refund",
        )
        research = ResearchData(
            recommended_document_type="demand_letter",
            research_summary="Test",
        )

        with patch('services.gemini_service.genai'):
            agent = DraftingAgent()
            agent._gemini = MagicMock()
            agent._gemini.generate = AsyncMock()

            doc = await agent.draft(
                intake=intake,
                research=research,
                content_override="PRE-WRITTEN CONTENT FROM STREAM",
                user_id="u1",
                case_id="c1",
            )

            agent._gemini.generate.assert_not_called()
            assert doc.content == "PRE-WRITTEN CONTENT FROM STREAM"


class TestResearchAgentConfidence:
    """Tests for confidence score computation."""

    def test_confidence_increases_with_authoritative_sources(self):
        from agents.research_agent import ResearchAgent

        with patch('services.gemini_service.genai'):
            agent = ResearchAgent()

        authoritative_sources = [
            {"title": "Transfer of Property Act", "url": "https://indiankanoon.org/act/123"},
            {"title": "Consumer Protection Act", "url": "https://legislative.gov.in/act/456"},
        ]
        plain_sources = [
            {"title": "Legal blog", "url": "https://example.com/blog"},
        ]

        result_data = {"relevant_sections": ["s1", "s2"], "case_precedents": ["p1"]}

        score_authoritative = agent._compute_confidence(authoritative_sources, result_data)
        score_plain = agent._compute_confidence(plain_sources, result_data)

        assert score_authoritative > score_plain

    def test_confidence_capped_at_100(self):
        from agents.research_agent import ResearchAgent

        with patch('services.gemini_service.genai'):
            agent = ResearchAgent()

        # 10 authoritative sources = would be 150 points without cap
        many_sources = [
            {"title": f"Source {i}", "url": "https://indiankanoon.org/doc/" + str(i)}
            for i in range(10)
        ]
        result_data = {"relevant_sections": ["s"] * 10, "case_precedents": ["p"] * 10}
        score = agent._compute_confidence(many_sources, result_data)
        assert score <= 100.0

    def test_confidence_zero_with_no_sources(self):
        from agents.research_agent import ResearchAgent

        with patch('services.gemini_service.genai'):
            agent = ResearchAgent()

        score = agent._compute_confidence([], {"relevant_sections": [], "case_precedents": []})
        assert score == 0.0


class TestSuspiciousDetection:
    """Tests for suspicious pattern detection in middleware."""

    def test_detects_sql_injection(self):
        from core.middleware import is_suspicious
        text = "My landlord DROP TABLE cases; SELECT * FROM users"
        sus, _ = is_suspicious(text)
        assert sus is True

    def test_detects_xss(self):
        from core.middleware import is_suspicious
        sus, _ = is_suspicious('<script>alert("xss")</script>')
        assert sus is True

    def test_detects_path_traversal(self):
        from core.middleware import is_suspicious
        sus, _ = is_suspicious("../../etc/passwd")
        assert sus is True

    def test_clean_legal_message_not_suspicious(self):
        from core.middleware import is_suspicious
        text = "My landlord refused to return my ₹50,000 security deposit after 60 days."
        sus, _ = is_suspicious(text)
        assert sus is False

    def test_off_topic_detection(self):
        from core.middleware import is_off_topic
        assert is_off_topic("Tell me the weather in Mumbai tomorrow") is True

    def test_legal_text_not_off_topic(self):
        from core.middleware import is_off_topic
        assert is_off_topic("My landlord has not returned my deposit") is False
