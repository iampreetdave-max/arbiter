"""
gemini_service.py — Wrapper around the Google Gemini API.

All Gemini calls in the app go through this service.
Provides:
  - Standard generation (generate)
  - Structured JSON generation (generate_structured)
  - Google Search grounded generation (generate_with_grounding) ← NEW
  - Streaming generation (stream_generate) ← NEW
  - Multi-turn chat with history
"""
from __future__ import annotations

import asyncio
import logging
import queue as stdlib_queue
import threading
from typing import AsyncGenerator, Optional

import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Gemini once at module load
genai.configure(api_key=settings.gemini_api_key)

# Safety settings — relaxed for legal content (laws mention crimes, harassment, etc.)
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.2,       # Low temp = consistent, factual legal output
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
)


class GeminiService:
    """
    Async wrapper around Google Gemini API.

    New capabilities:
      - generate_with_grounding(): Uses Google Search to verify real Indian laws
      - stream_generate(): Yields text chunks progressively (for live document generation)
      - stream_chat(): Streams multi-turn chat responses

    Usage:
        gemini = GeminiService()
        text, sources = await gemini.generate_with_grounding("Research IPC Section 420 India")
        async for chunk in gemini.stream_generate("Draft demand letter for..."):
            print(chunk, end="")
    """

    def __init__(self, system_instruction: Optional[str] = None) -> None:
        self._model_name = settings.gemini_model
        self._system_instruction = system_instruction or self._default_system_instruction()
        self._model = GenerativeModel(
            model_name=self._model_name,
            system_instruction=self._system_instruction,
            safety_settings=SAFETY_SETTINGS,
            generation_config=GENERATION_CONFIG,
        )

    @staticmethod
    def _default_system_instruction() -> str:
        return (
            "You are Arbiter, an expert AI legal assistant specialising in Indian law. "
            "You help everyday people understand their legal rights and draft legal documents. "
            "You are factual, precise, and cite specific sections of Indian law. "
            "You never fabricate laws or case precedents. "
            "You always recommend consulting a qualified lawyer for complex matters. "
            "You communicate clearly in plain English and, when asked, in Hindi."
        )

    # ── Standard generation ─────────────────────────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        chat_history: Optional[list[dict]] = None,
        max_retries: int = 3,
    ) -> str:
        """Generate a text response from Gemini (non-streaming)."""
        for attempt in range(1, max_retries + 1):
            try:
                if chat_history:
                    chat = self._model.start_chat(history=chat_history)
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: chat.send_message(prompt)
                    )
                else:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self._model.generate_content(prompt)
                    )
                text = response.text
                logger.info("gemini_generate_ok", extra={"chars": len(text), "attempt": attempt})

                # ── Cost tracking (non-blocking) ──────────────────────────────────────────────────
                try:
                    usage = getattr(response, "usage_metadata", None)
                    tokens_in = getattr(usage, "prompt_token_count", 0) or 0
                    tokens_out = getattr(usage, "candidates_token_count", 0) or 0
                    from core.monitoring import track_gemini_call
                    await track_gemini_call(
                        user_id="",
                        operation="generate",
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        grounded=False,
                    )
                except Exception:
                    pass  # Never block generation on monitoring failure

                return text

            except ResourceExhausted:
                logger.warning("gemini_quota_exceeded", extra={"attempt": attempt})
                if attempt == max_retries:
                    raise RuntimeError("Gemini API quota exceeded. Please try again later.")
                await asyncio.sleep(2 ** attempt)

            except ServiceUnavailable:
                logger.warning("gemini_unavailable", extra={"attempt": attempt})
                if attempt == max_retries:
                    raise RuntimeError("Gemini API temporarily unavailable.")
                await asyncio.sleep(2 ** attempt)

            except Exception as exc:
                logger.error("gemini_error", extra={"error": str(exc)})
                raise RuntimeError(f"Gemini API error: {exc}") from exc

        raise RuntimeError("Gemini generation failed after all retries.")

    # ── Google Search Grounding ───────────────────────────────────────────────────────────────────────────

    async def generate_with_grounding(
        self,
        prompt: str,
        max_retries: int = 3,
    ) -> tuple[str, list[dict]]:
        """
        Generate with Google Search grounding — verifies legal claims against real web sources.

        Returns:
            tuple of (generated_text, grounding_sources)
            where grounding_sources = [{"title": str, "url": str}, ...]

        Uses Gemini's built-in Google Search tool to ground responses in real Indian law
        databases, court websites, and government publications.
        Falls back to regular generation if grounding is unavailable.
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Create a model instance with Google Search grounding enabled
                # The "google_search_retrieval" tool makes Gemini search the web
                # before generating, grounding its output in real sources
                grounded_model = GenerativeModel(
                    model_name=self._model_name,
                    system_instruction=self._system_instruction,
                    safety_settings=SAFETY_SETTINGS,
                    generation_config=GENERATION_CONFIG,
                    tools=["google_search_retrieval"],
                )

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: grounded_model.generate_content(prompt),
                )

                text = response.text

                # Extract grounding sources from response metadata
                sources: list[dict] = []
                try:
                    candidate = response.candidates[0]
                    metadata = getattr(candidate, "grounding_metadata", None)
                    if metadata:
                        for chunk in getattr(metadata, "grounding_chunks", []):
                            web = getattr(chunk, "web", None)
                            if web:
                                title = getattr(web, "title", "")
                                url = getattr(web, "uri", "")
                                if url:
                                    sources.append({"title": title, "url": url})
                except Exception:
                    pass  # Metadata extraction failure is non-fatal

                logger.info(
                    "gemini_grounded_ok",
                    extra={"sources": len(sources), "chars": len(text), "attempt": attempt},
                )

                # ── Cost tracking (non-blocking) ──────────────────────────────────────────────────
                try:
                    usage = getattr(response, "usage_metadata", None)
                    tokens_in = getattr(usage, "prompt_token_count", 0) or 0
                    tokens_out = getattr(usage, "candidates_token_count", 0) or 0
                    from core.monitoring import track_gemini_call
                    await track_gemini_call(
                        user_id="",
                        operation="generate_with_grounding",
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        grounded=True,
                    )
                except Exception:
                    pass  # Never block generation on monitoring failure

                return text, sources

            except ResourceExhausted:
                if attempt == max_retries:
                    break
                await asyncio.sleep(2 ** attempt)

            except Exception as exc:
                logger.warning(
                    "grounding_unavailable",
                    extra={"error": str(exc), "attempt": attempt},
                )
                break  # Fall through to non-grounded

        # ── Fallback: regular generation ────────────────────────────────────────────────────────────────
        logger.info("grounding_fallback")
        text = await self.generate(prompt)
        return text, []

    # ── Streaming generation ─────────────────────────────────────────────────────────────────────────────

    async def stream_generate(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream text generation — yields chunks as Gemini produces them.

        Ideal for live document generation where the user sees text appearing
        word-by-word instead of waiting for the full response.

        Usage:
            async for chunk in gemini.stream_generate("Draft demand letter..."):
                await websocket.send(chunk)
        """
        chunk_queue: stdlib_queue.Queue = stdlib_queue.Queue()
        loop = asyncio.get_event_loop()

        def _produce() -> None:
            """Background thread: streams from Gemini and puts chunks into queue."""
            try:
                response = self._model.generate_content(prompt, stream=True)
                for chunk in response:
                    text = getattr(chunk, "text", None)
                    if text:
                        chunk_queue.put(text)
            except Exception as exc:
                chunk_queue.put(exc)
            finally:
                chunk_queue.put(None)  # Sentinel — signals end of stream

        thread = threading.Thread(target=_produce, daemon=True)
        thread.start()

        while True:
            # Wait for next chunk without blocking the event loop
            item = await loop.run_in_executor(None, chunk_queue.get)
            if item is None:
                break
            if isinstance(item, Exception):
                logger.error("stream_error", extra={"error": str(item)})
                raise RuntimeError(f"Streaming failed: {item}")
            yield item

    async def stream_chat(
        self,
        history: list[dict],
        message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a multi-turn chat response.

        Args:
            history: Chat history as [{"role": "user"|"model", "parts": [str]}]
            message: Current user message.
        """
        chunk_queue: stdlib_queue.Queue = stdlib_queue.Queue()
        loop = asyncio.get_event_loop()

        def _produce() -> None:
            try:
                chat = self._model.start_chat(history=history)
                response = chat.send_message(message, stream=True)
                for chunk in response:
                    text = getattr(chunk, "text", None)
                    if text:
                        chunk_queue.put(text)
            except Exception as exc:
                chunk_queue.put(exc)
            finally:
                chunk_queue.put(None)

        thread = threading.Thread(target=_produce, daemon=True)
        thread.start()

        while True:
            item = await loop.run_in_executor(None, chunk_queue.get)
            if item is None:
                break
            if isinstance(item, Exception):
                raise RuntimeError(f"Chat streaming failed: {item}")
            yield item

    # ── Structured JSON generation ────────────────────────────────────────────────────────────────────────

    async def generate_structured(
        self,
        prompt: str,
        expected_keys: list[str],
        chat_history: Optional[list[dict]] = None,
        use_grounding: bool = False,
    ) -> dict:
        """
        Generate a response and parse it as JSON.

        Args:
            prompt: The instruction prompt.
            expected_keys: Keys that must be present in the response JSON.
            chat_history: Prior conversation context.
            use_grounding: If True, use Google Search grounding (better accuracy).

        Returns:
            Parsed dict. Falls back to {"raw": text} if JSON parsing fails.
        """
        import json
        import re

        json_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON containing these keys: {expected_keys}. "
            "No markdown, no explanation, just the JSON object."
        )

        if use_grounding:
            text, _ = await self.generate_with_grounding(json_prompt)
        else:
            text = await self.generate(json_prompt, chat_history=chat_history)

        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()

        try:
            data = json.loads(text)
            return data
        except json.JSONDecodeError:
            logger.warning("gemini_json_parse_failed", extra={"raw": text[:200]})
            return {"raw": text}

    # ── Multi-turn chat ────────────────────────────────────────────────────────────────────────────────

    async def chat(
        self,
        conversation: list[dict],
        max_retries: int = 3,
    ) -> str:
        """
        Send a multi-turn conversation to Gemini and return the response.

        Args:
            conversation: List of {"role": "user"|"model", "parts": [str]} dicts.
                          The LAST item is the current user message.
                          All prior items are the history.

        Returns:
            Model's text response.
        """
        if not conversation:
            raise ValueError("Conversation cannot be empty.")

        # Split into history and current message
        history = conversation[:-1]
        current = conversation[-1]

        if current.get("role") != "user":
            raise ValueError("Last message must be from 'user'.")

        current_message = current["parts"][0] if current.get("parts") else ""

        for attempt in range(1, max_retries + 1):
            try:
                chat = self._model.start_chat(history=history)
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: chat.send_message(current_message)
                )
                return response.text

            except ResourceExhausted:
                if attempt == max_retries:
                    raise RuntimeError("Gemini API quota exceeded.")
                await asyncio.sleep(2 ** attempt)

            except ServiceUnavailable:
                if attempt == max_retries:
                    raise RuntimeError("Gemini API temporarily unavailable.")
                await asyncio.sleep(2 ** attempt)

            except Exception as exc:
                raise RuntimeError(f"Chat failed: {exc}") from exc

        raise RuntimeError("Chat failed after all retries.")


# ── Module-level singleton ───────────────────────────────────────────────────────────────────────────

_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Return module-level GeminiService singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
