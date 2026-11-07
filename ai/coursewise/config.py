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
