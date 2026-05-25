"""LearnFast AI module — Groq LLM wrappers.

Provides three learning tools powered by the Groq LLM (Llama 3.3 70B):

- ``generate_flashcards`` — create 5 question/answer cards from study text
- ``generate_quiz``       — create a 5-question multiple-choice quiz
- ``simplify_text``       — rewrite text so a 12-year-old can understand it

All functions return a dict. On success the dict contains the expected data
keys. On failure it contains a single ``"error"`` key with a human-readable
message.

The Groq client is initialised lazily from ``config.settings`` — no API key
needs to be passed as a function argument.
"""
from __future__ import annotations

import logging

from groq import Groq

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy Groq client singleton
# ---------------------------------------------------------------------------
_client: Groq | None = None


def _get_client() -> Groq:
    """Return the shared Groq client, creating it on first call."""
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


# ---------------------------------------------------------------------------
# Core LLM helper
# ---------------------------------------------------------------------------
def _ask_groq(prompt: str, system_instruction: str) -> dict:
    """Send a prompt to the Groq LLM and return the parsed JSON response.

    Args:
        prompt:             The user-facing message (the study text).
        system_instruction: The system message that shapes the output format.

    Returns:
        A parsed dict on success, or ``{"error": "<message>"}`` on failure.
    """
    try:
        response = _get_client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        import json
        return json.loads(content.strip())

    except Exception as exc:
        logger.exception("Groq LLM request failed")
        return {"error": f"AI request failed: {exc}"}


# ---------------------------------------------------------------------------
# Language helper
# ---------------------------------------------------------------------------
def _lang_instruction(lang: str) -> str:
    """Return a language instruction appended to system prompts.

    Currently supports English (default) and Bulgarian (``'bg'``).
    """
    if lang == "bg":
        return (
            " IMPORTANT: All content values MUST be in BULGARIAN language. "
            "Keep JSON keys in English, but all values in Bulgarian."
        )
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_flashcards(text: str, lang: str = "en") -> dict:
    """Generate 5 flashcards from study text.

    Args:
        text: The study material to turn into flashcards.
        lang: Output language — ``'en'`` (default) or ``'bg'``.

    Returns:
        ``{"flashcards": [{"question": ..., "answer": ..., "funny_note": ...}]}``
        or ``{"error": ...}`` on failure.
    """
    system = (
        "You are a study assistant. Create exactly 5 flashcards from the given text. "
        "Return ONLY valid JSON in this exact format: "
        '{ "flashcards": [ {"question": "...", "answer": "...", "funny_note": "..."} ] }'
        + _lang_instruction(lang)
    )
    return _ask_groq(f"Create flashcards for this text:\n\n{text}", system)


def generate_quiz(text: str, lang: str = "en") -> dict:
    """Generate a 5-question multiple-choice quiz from study text.

    Args:
        text: The study material to quiz on.
        lang: Output language — ``'en'`` (default) or ``'bg'``.

    Returns:
        ``{"quiz": [{"question": ..., "options": [...], "correct_answer": ..., "explanation": ...}]}``
        or ``{"error": ...}`` on failure.
    """
    system = (
        "You are a quiz generator. Create exactly 5 multiple choice questions from the given text. "
        "Each question must have exactly 4 options and one correct answer. "
        "Return ONLY valid JSON in this exact format: "
        '{ "quiz": [ {"question": "...", "options": ["A", "B", "C", "D"], '
        '"correct_answer": "exact text of correct option", "explanation": "..."} ] }'
        + _lang_instruction(lang)
    )
    return _ask_groq(f"Create a quiz based on this text:\n\n{text}", system)


def simplify_text(text: str, lang: str = "en") -> dict:
    """Simplify study text so a 12-year-old can understand it.

    Args:
        text: The text to simplify.
        lang: Output language — ``'en'`` (default) or ``'bg'``.

    Returns:
        ``{"summary_title": ..., "simplified_content": ..., "key_points": [...]}``
        or ``{"error": ...}`` on failure.
    """
    system = (
        "You are a study assistant. Simplify the given text so a 12-year-old can understand it. "
        "Make it clear, engaging, and slightly fun. "
        "Return ONLY valid JSON in this exact format: "
        '{ "summary_title": "...", "simplified_content": "...", "key_points": ["point 1", "point 2", "point 3"] }'
        + _lang_instruction(lang)
    )
    return _ask_groq(f"Simplify this text:\n\n{text}", system)
