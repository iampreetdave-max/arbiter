"""
prompt_enhancer.py — Raw user input → structured, detailed prompt.

Users often type casual, vague messages. This module uses Gemini to
enrich the user's raw input into a well-structured legal prompt.
This runs BEFORE the intake agent sees the message.
"""
# Arbiter - Powered by Google Gemini 2.0 Pro - XPRIZE Build with Gemini
from __future__ import annotations

import structlog

logger = structlog.get_logger()

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
    if len(raw_message.strip()) < 20:
        return raw_message
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
            f"Rewrite this as a clear legal problem statement (2-4 sentences, first person):"
        )

        conversation = [
            {"role": "user",  "parts": [_ENHANCE_SYSTEM]},
            {"role": "model", "parts": ["Understood. I will enhance the user's message into a structured legal problem statement without adding facts or legal advice."]},
            {"role": "user",  "parts": [user_instruction]},
        ]

        enhanced = await gemini_service.chat(conversation)
        enhanced = enhanced.strip()

        if len(enhanced) < 10 or len(enhanced) > 800:
            return raw_message

        return enhanced

    except Exception as exc:
        logger.warning("prompt_enhancement_failed", error=str(exc))
        return raw_message


async def enhance_if_needed(
    raw_message: str,
    country_code: str = "IN",
    language: str = "en",
    gemini_service=None,
    min_length_to_enhance: int = 20,
) -> tuple[str, bool]:
    if len(raw_message.strip()) < min_length_to_enhance:
        return raw_message, False

    enhanced = await enhance_user_prompt(raw_message, country_code, language, gemini_service)
    was_enhanced = enhanced != raw_message
    return enhanced, was_enhanced
