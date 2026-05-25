"""
prompt_enhancer.py — Raw user input → structured, detailed prompt.

Users often type casual, vague messages. This module uses Gemini to
enrich the user's raw input into a well-structured legal prompt that:
  1. Preserves the user's intent
  2. Adds structure Arbiter's intake agent can parse better
  3. Is country-aware (uses the user's selected jurisdiction)
  4. Does NOT alter facts — only adds structure

This runs BEFORE the intake agent sees the message.
The enhancement is transparent to the user — they see the original message
while the AI processes the enriched version.

Example:
  Raw:      "my landlord wont give back deposit"
  Enhanced: "I am a tenant in India. My landlord has refused to return my
             security deposit despite the tenancy having ended. I am seeking
             the return of my deposit and any applicable penalties or interest
             under Indian tenancy law."
"""
from __future__ import annotations

import structlog

logger = structlog.get_logger()

# ── Enhancement prompt ──────────────────────────────────────────────

_ENHANCE_SYSTEM = """You are a legal intake specialist. Your job is to take a user's raw, casual description of a legal problem and rewrite it into a clear, structured statement that:

1. Preserves ALL facts the user mentioned — never add facts they did not state
2. Uses proper legal terminology where appropriate
3. Makes the jurisdiction and problem type clear
4. States what remedy or outcome the user is seeking
5. Is 2–4 sentences maximum
6. Stays in first person ("I am...", "My...")

DO NOT:
- Add facts not mentioned by the user
- Give legal conclusions
- Add legal advice
- Change the meaning of what the user said
- Make the message longer than 4 sentences

Just output the enhanced prompt text. No preamble, no explanation."""


async def enhance_user_prompt(
    raw_message: str,
    country_code: str = "IN",
    language: str = "en",
    gemini_service=None,
) -> str:
    """
    Enhance a raw user message into a well-structured legal prompt.

    Args:
        raw_message: The user's original casual description
        country_code: ISO country code (e.g. "IN", "US") — used for context
        language: Message language ("en" | "hi")
        gemini_service: Injected GeminiService instance (avoids circular imports)

    Returns:
        Enhanced prompt string. Falls back to original message on any error.
    """
    # Short messages don't need enhancement — already clear enough
    if len(raw_message.strip()) < 20:
        return raw_message

    # Very long messages also skip enhancement — user already gave detail
    if len(raw_message.strip()) > 500:
        return raw_message

    if gemini_service is None:
        return raw_message

    try:
        from core.countries import get_country_name
        country_name = get_country_name(country_code)

        user_instruction = (
            f"Country context: {country_name}\n"
            f"Language: {language}\n\n"
            f"User's original message:\n{raw_message}\n\n"
            f"Rewrite this as a clear legal problem statement (2–4 sentences, first person):"
        )

        conversation = [
            {"role": "user",  "parts": [_ENHANCE_SYSTEM]},
            {"role": "model", "parts": ["Understood. I will enhance the user's message into a structured legal problem statement without adding facts or legal advice."]},
            {"role": "user",  "parts": [user_instruction]},
        ]

        enhanced = await gemini_service.chat(conversation)
        enhanced = enhanced.strip()

        # Sanity check — if the response is too different in length or seems weird, use original
        if len(enhanced) < 10 or len(enhanced) > 800:
            logger.warning("prompt_enhancement_suspicious",
                         original_len=len(raw_message),
                         enhanced_len=len(enhanced))
            return raw_message

        logger.info(
            "prompt_enhanced",
            original_len=len(raw_message),
            enhanced_len=len(enhanced),
            country=country_code,
        )
        return enhanced

    except Exception as exc:
        # NEVER let enhancement break the main flow — graceful fallback
        logger.warning("prompt_enhancement_failed", error=str(exc))
        return raw_message


async def enhance_if_needed(
    raw_message: str,
    country_code: str = "IN",
    language: str = "en",
    gemini_service=None,
    min_length_to_enhance: int = 20,
) -> tuple[str, bool]:
    """
    Conditionally enhance a message.

    Returns:
        Tuple of (message_to_use, was_enhanced)
    """
    if len(raw_message.strip()) < min_length_to_enhance:
        return raw_message, False

    enhanced = await enhance_user_prompt(raw_message, country_code, language, gemini_service)
    was_enhanced = enhanced != raw_message
    return enhanced, was_enhanced
