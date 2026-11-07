"""ChromaDB collection and embedding model, loaded once per process."""

from __future__ import annotations

from functools import lru_cache

from .config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    vectors = get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


@lru_cache(maxsize=1)
def get_collection():
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Cosine distance, since embeddings are normalized.
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
