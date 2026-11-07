"""Semantic search over the course index, optionally limited to some courses."""

from __future__ import annotations

from dataclasses import dataclass

from .courses import course_number
from .store import embed, get_collection


@dataclass
class Hit:
    text: str
    metadata: dict
    score: float  # cosine similarity, higher is better


def build_filter(course_codes: list[str] | None, doc_type: str | None) -> dict | None:
    clauses = []
    if course_codes:
        numbers = sorted({n for c in course_codes if (n := course_number(c) or c.upper())})
        clauses.append({"course_number": {"$in": numbers}})
    if doc_type:
        clauses.append({"doc_type": doc_type})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def search(
    query: str,
    course_codes: list[str] | None = None,
    doc_type: str | None = None,
    k: int = 5,
) -> list[Hit]:
    """Return the top k chunks for query.

    course_codes accepts "CS 439", "cs439", or a bare course number like "39".
    """
    result = get_collection().query(
        query_embeddings=embed([query]),
        n_results=k,
        where=build_filter(course_codes, doc_type),
        include=["documents", "metadatas", "distances"],
    )
    return [
        Hit(text=doc, metadata=meta, score=1 - dist)
        for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0], strict=True)
    ]
