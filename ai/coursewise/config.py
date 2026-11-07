"""Paths and settings shared by the AI service."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_DIR = Path(os.getenv("COURSEWISE_MARKDOWN_DIR", REPO_ROOT / "data" / "markdown"))
CHROMA_DIR = Path(os.getenv("COURSEWISE_CHROMA_DIR", REPO_ROOT / "data" / "chroma"))
COLLECTION_NAME = os.getenv("COURSEWISE_COLLECTION", "courses")
EMBEDDING_MODEL = os.getenv("COURSEWISE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Gemini, through its OpenAI-compatible endpoint.
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Chunks scoring below this cosine similarity are dropped as weak matches.
# Measured on the catalog: off-topic questions top out near 0.17, real ones start near 0.38.
MIN_SCORE = float(os.getenv("COURSEWISE_MIN_SCORE", "0.25"))

# Redis answer cache. Leave REDIS_URL empty to turn caching off.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("COURSEWISE_CACHE_TTL", str(7 * 24 * 3600)))
