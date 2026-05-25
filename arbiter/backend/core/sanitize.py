"""
sanitize.py — Input sanitization and AI scope enforcement.

Two responsibilities:
  1. Sanitize user text — strip null bytes, control chars, excessive whitespace
  2. Enforce legal scope — reject non-legal questions before sending to Gemini
"""
from __future__ import annotations

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000

LEGAL_POSITIVE_PATTERNS = [
    r"\b(law|legal|court|judge|lawyer|advocate|attorney|barrister)\b",
    r"\b(case|complaint|petition|appeal|suit|claim|dispute|grievance)\b",
    r"\b(rights|right|entitled|entitlement|violation|breach)\b",
    r"\b(rent|deposit|landlord|tenant|eviction|lease|property)\b",
    r"\b(salary|wages|employment|employer|employee|termination|layoff)\b",
    r"\b(consumer|product|service|refund|defective|fraud|scam)\b",
    r"\b(rti|information|government|authority|officer|public)\b",
    r"\b(harassment|threat|intimidation|stalking|abuse)\b",
    r"\b(cheque|bounce|debt|loan|recovery|payment|amount)\b",
    r"\b(police|fir|complaint|section|ipc|crpc|act|rule)\b",
    r"\b(kanoon|adalat|mukadma|vakil|shikayat|nyaya|kiraya|zameen)\b",
]

OFF_TOPIC_PATTERNS = [
    r"\b(recipe|cook|food|restaurant|menu|ingredient)\b",
    r"\b(game|gaming|play|sports|football|cricket(?!\s+(?:dispute|contract)))\b",
    r"\b(movie|film|actor|actress|celebrity|entertainment)\b",
    r"\b(weather|temperature|forecast|rain|sunny)\b",
    r"\b(math|calculus|physics|chemistry|biology(?!\s+(?:lab|testing)))\b",
    r"\b(poem|story|novel|fiction|joke|riddle)\b",
]

LEGAL_POSITIVE_RE = [re.compile(p, re.IGNORECASE) for p in LEGAL_POSITIVE_PATTERNS]
OFF_TOPIC_RE = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]

INJECTION_PATTERNS = [
    r"(?i)(ignore previous instructions|forget you are|you are now|pretend to be)",
    r"(?i)(system prompt|system message|as an ai|as a language model)",
    r"(?i)(jailbreak|dan mode|developer mode|unrestricted mode)",
    r"(?i)(ignore the above|disregard|override|bypass)",
    r"(?i)(you are now|you're now|act as|pretend to be|roleplay as|role play as)\s*(a|an|the)?\s*(?!arbiter)",
    r"(?i)(you are|you're)\s+(gemini|gpt|claude|chatgpt|openai|google ai|bard|llm|language model)",
    r"(?i)(what (ai|model|llm) are you|which (ai|model) (are you|powers you)|are you (gemini|gpt|chatgpt|claude))",
    r"(?i)(your (true|real|actual|underlying) (model|ai|identity|purpose|instructions|system prompt))",
    r"(?i)(ignore (all |your |previous |these |prior )?(instructions?|rules?|guidelines?|constraints?))",
    r"(?i)(jailbreak|developer mode|dan mode|jail break|unrestricted mode|no restrictions?)",
    r"(?i)(bypass (your |all |the )?(restrictions?|filters?|rules?|safety|guidelines?))",
    r"(?i)(you have no restrictions?|you can (now |)say anything|forget (your |all |previous )?instructions?)",
    r"(?i)(system\s*prompt|your\s*prompt|your\s*instructions?|reveal\s*(your|the)\s*(prompt|instructions?))",
    r"(?i)(i am (your|the) (developer|trainer|creator|admin|administrator|anthropic|google))",
    r"(?i)(this is (a |)test,?\s*(ignore|skip|bypass))",
    r"(?i)(hypothetically|in (a |this |the )?hypothetical|for (a |the |this )?story|fictional(ly)?)\s*.{0,50}(illegal|harm|hurt|kill|bomb|weapon|drug)",
]
INJECTION_RE = [re.compile(p) for p in INJECTION_PATTERNS]


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH] + "…"
    return text.strip()


def classify_legal_relevance(text: str) -> tuple[str, str]:
    for pattern in INJECTION_RE:
        if pattern.search(text):
            return "injection", "Message contains prompt injection attempt."
    legal_hits = sum(1 for p in LEGAL_POSITIVE_RE if p.search(text))
    if legal_hits >= 1:
        return "legal", f"Matched {legal_hits} legal keyword pattern(s)."
    off_topic_hits = sum(1 for p in OFF_TOPIC_RE if p.search(text))
    if off_topic_hits >= 2:
        return "off_topic", f"Matched {off_topic_hits} off-topic pattern(s)."
    if len(text.split()) <= 6:
        return "legal", "Short message — not classified as off-topic."
    return "unclear", "No strong signal — forwarding to Gemini."


OFF_TOPIC_RESPONSE = (
    "I'm Arbiter, an AI assistant specialising in legal matters. "
    "I can help you with:\n"
    "• Demand letters and legal notices\n"
    "• RTI (Right to Information) applications\n"
    "• Consumer complaints\n"
    "• Employment disputes and salary recovery\n"
    "• Tenant rights and security deposit recovery\n\n"
    "Please describe your legal issue and I'll guide you."
)

INJECTION_RESPONSE = (
    "I can only help with legal matters. "
    "Please describe your legal situation."
)


def get_scope_rejection_message(classification: str) -> str:
    if classification == "injection":
        return INJECTION_RESPONSE
    return OFF_TOPIC_RESPONSE
