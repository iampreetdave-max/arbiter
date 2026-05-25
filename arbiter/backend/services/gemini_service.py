"""
gemini_service.py — Wrapper around the Google Gemini API.

All Gemini calls in the app go through this service.
This centralises model configuration, retry logic, logging, and error handling.
"""
from __future__ import annotations

import logging
import asyncio
from typing import Optional

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

    Usage:
        gemini = GeminiService()
        response = await gemini.generate("Explain Section 35 of Consumer Protection Act 2019")
    """

    def __init__(self, system_instruction: Optional[str] = None) -> None:
        """
        Initialise GeminiService with an optional system instruction.

        Args:
            system_instruction: System prompt that sets model behaviour for all calls.
        """
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
        """Default system instruction for the legal assistant."""
        return (
            "You are Arbiter, an expert AI legal assistant specialising in Indian law. "
            "You help everyday people understand their legal rights and draft legal documents. "
            "You are factual, precise, and cite specific sections of Indian law. "
            "You never fabricate laws or case precedents. "
            "You always recommend consulting a qualified lawyer for complex matters. "
            "You communicate clearly in plain English and, when asked, in Hindi."
        )

    async def generate(
        self,
        prompt: str,
        chat_history: Optional[list[dict]] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: The user's message or instruction.
            chat_history: Prior conversation turns as [{"role": "user"|"model", "parts": [str]}]
            max_retries: Number of retry attempts on transient errors.

        Returns:
            Generated text response.

        Raises:
            RuntimeError: If all retries fail.
        """
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
                logger.info(
                    "gemini_generate_ok",
                    extra={"model": self._model_name, "chars": len(text), "attempt": attempt},
                )
                return text

            except ResourceExhausted as exc:
                logger.warning("gemini_quota_exceeded", extra={"attempt": attempt})
                if attempt == max_retries:
                    raise RuntimeError("Gemini API quota exceeded. Please try again later.") from exc
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except ServiceUnavailable as exc:
                logger.warning("gemini_unavailable", extra={"attempt": attempt})
                if attempt == max_retries:
                    raise RuntimeError("Gemini API temporarily unavailable.") from exc
                await asyncio.sleep(2 ** attempt)

            except Exception as exc:
                logger.error("gemini_error", extra={"error": str(exc), "attempt": attempt})
                raise RuntimeError(f"Gemini API error: {exc}") from exc

        raise RuntimeError("Gemini generation failed after all retries.")

    async def generate_structured(
        self,
        prompt: str,
        expected_keys: list[str],
        chat_history: Optional[list[dict]] = None,
    ) -> dict:
        """
        Generate a response and parse it as a dict with expected keys.
        Instructs Gemini to respond in JSON format.

        Args:
            prompt: The instruction prompt.
            expected_keys: Keys that must be present in the response JSON.
            chat_history: Prior conversation context.

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
        text = await self.generate(json_prompt, chat_history=chat_history)

        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()

        try:
            data = json.loads(text)
            return data
        except json.JSONDecodeError:
            logger.warning("gemini_json_parse_failed", extra={"raw": text[:200]})
            return {"raw": text}


# Module-level singleton
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Return module-level GeminiService singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
