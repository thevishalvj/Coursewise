"""Build the ChromaDB index from data/markdown.

Usage:
    python -m coursewise.ingest          # from the ai/ folder
"""

from __future__ import annotations

import hashlib

from .chunking import chunk_directory
from .config import MARKDOWN_DIR
from .store import embed, get_collection

BATCH = 64


def chunk_id(source: str, index: int) -> str:
    return hashlib.sha1(f"{source}:{index}".encode()).hexdigest()


def ingest(reset: bool = True) -> int:
    chunks = chunk_directory(MARKDOWN_DIR)
    collection = get_collection()
    if reset and collection.count():
        collection.delete(ids=collection.get(include=[])["ids"])
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        collection.upsert(
            ids=[chunk_id(c.metadata["source"], c.metadata["chunk_index"]) for c in batch],
            documents=[c.text for c in batch],
            embeddings=embed([c.text for c in batch]),
            # Chroma metadata values must be str, int, float, or bool.
            metadatas=[{k: v for k, v in c.metadata.items() if v is not None} for c in batch],
        )
    return len(chunks)


if __name__ == "__main__":
    from .cache import get_cache

    print(f"Indexed {ingest()} chunks from {MARKDOWN_DIR}")
    # Cached answers may cite chunks that just changed.
    print(f"Cleared {get_cache().clear()} cached answers")
