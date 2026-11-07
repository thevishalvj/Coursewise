"""Redis cache for /ask answers.

Keys combine the normalized question, any course filter, and the Gemini model, so
"What does CS 439 cover?" and "what does cs 439 cover" share an entry. Rebuilding
the index clears the cache, since old answers may cite chunks that changed.

If Redis is unreachable, caching is skipped and the service keeps answering.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from functools import lru_cache

from .config import CACHE_TTL_SECONDS, GEMINI_MODEL, REDIS_URL

log = logging.getLogger(__name__)
PREFIX = "coursewise:answer:"


def normalize(question: str) -> str:
    q = re.sub(r"\s+", " ", question.strip().lower())
    return q.rstrip("?.! ")


def cache_key(question: str, course_codes: list[str] | None = None, model: str = GEMINI_MODEL) -> str:
    codes = ",".join(sorted(c.strip().upper() for c in course_codes or []))
    raw = f"{model}|{codes}|{normalize(question)}"
    return PREFIX + hashlib.sha256(raw.encode()).hexdigest()


class AnswerCache:
    def __init__(self, client, ttl: int = CACHE_TTL_SECONDS):
        self.client = client
        self.ttl = ttl

    def get(self, key: str) -> dict | None:
        try:
            raw = self.client.get(key)
        except Exception as exc:  # Redis down: behave like a miss
            log.warning("cache get failed: %s", exc)
            return None
        return json.loads(raw) if raw else None

    def set(self, key: str, value: dict) -> None:
        try:
            self.client.set(key, json.dumps(value), ex=self.ttl)
        except Exception as exc:
            log.warning("cache set failed: %s", exc)

    def clear(self) -> int:
        try:
            keys = list(self.client.scan_iter(f"{PREFIX}*"))
            return self.client.delete(*keys) if keys else 0
        except Exception as exc:
            log.warning("cache clear failed: %s", exc)
            return 0


class NullCache:
    """Used when REDIS_URL is empty."""

    def get(self, key: str) -> dict | None:
        return None

    def set(self, key: str, value: dict) -> None:
        pass

    def clear(self) -> int:
        return 0


@lru_cache(maxsize=1)
def get_cache() -> AnswerCache | NullCache:
    if not REDIS_URL:
        return NullCache()
    import redis

    # Short timeouts so a missing Redis costs milliseconds, not seconds.
    client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=0.5, socket_timeout=0.5)
    return AnswerCache(client)
