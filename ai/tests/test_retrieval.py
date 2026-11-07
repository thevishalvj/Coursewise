"""Retrieval tests against the real index. Skipped until `python -m coursewise.ingest` has run."""

import pytest

from coursewise.config import CHROMA_DIR
from coursewise.search import build_filter

needs_index = pytest.mark.skipif(not CHROMA_DIR.exists(), reason="index not built; run python -m coursewise.ingest")


def test_build_filter():
    assert build_filter(None, None) is None
    assert build_filter(["CS 439"], None) == {"course_number": {"$in": ["39"]}}
    assert build_filter(["CS 439"], "syllabus") == {
        "$and": [{"course_number": {"$in": ["39"]}}, {"doc_type": "syllabus"}]
    }


@needs_index
def test_course_filter_only_returns_that_course():
    from coursewise.search import search

    hits = search("what is this course about", course_codes=["CS 439"], k=5)
    assert hits
    assert all(h.metadata["course_number"] == "39" for h in hits)


@needs_index
def test_topic_search_finds_expected_course():
    from coursewise.search import search

    hits = search("Which course teaches SQL?", k=5)
    assert "catalog/cs-x27e.md" in [h.metadata["source"] for h in hits]


@needs_index
def test_off_topic_scores_are_low():
    from coursewise.config import MIN_SCORE
    from coursewise.search import search

    assert search("banana bread recipe", k=1)[0].score < MIN_SCORE
