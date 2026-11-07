"""Gemini client. Anything with a `complete(system, user) -> str` method can stand in for tests."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Protocol

from .config import GEMINI_BASE_URL, GEMINI_MODEL


class LLMUnavailable(RuntimeError):
    """Gemini failed after retries (overloaded, network error, bad key)."""


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class GeminiLLM:
    def __init__(self, model: str = GEMINI_MODEL):
        from openai import OpenAI

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to ai/.env.")
        # Retries cover Gemini's temporary 429 and 503 "high demand" errors.
        self.client = OpenAI(api_key=api_key, base_url=GEMINI_BASE_URL, max_retries=4, timeout=60)
        self.model = model

    def complete(self, system: str, user: str) -> str:
        from openai import APIError

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
        except APIError as exc:
            raise LLMUnavailable(f"Gemini is unavailable right now ({type(exc).__name__}). Try again shortly.") from exc
        return (response.choices[0].message.content or "").strip()


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    return GeminiLLM()
