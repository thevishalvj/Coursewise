from coursewise.chunking import chunk_document, parse_front_matter, split_by_heading, split_by_size
from coursewise.courses import course_number, find_course_numbers

DOC = """---
course_code: CS 439
course_number: "39"
title: "Principles of Computer Systems"
doc_type: syllabus
---

# CS 439

## Grading

Exams 60%. Projects 40%.

## Late policy

No late work.
"""


def test_front_matter_parsed():
    meta, body = parse_front_matter(DOC)
    assert meta["course_code"] == "CS 439"
    assert meta["course_number"] == "39"
    assert body.lstrip().startswith("# CS 439")


def test_split_by_heading_keeps_path():
    _, body = parse_front_matter(DOC)
    headings = [h for h, _ in split_by_heading(body)]
    assert headings == ["CS 439 > Grading", "CS 439 > Late policy"]


def test_split_by_size_limits_and_overlaps():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    pieces = split_by_size(text, size=800, overlap=120)
    assert len(pieces) > 1
    assert all(len(p) <= 800 for p in pieces)
    # consecutive pieces share some text
    assert pieces[0][-40:].split()[-1] in pieces[1]


def test_short_text_is_one_chunk():
    assert split_by_size("short", size=800) == ["short"]


def test_chunks_carry_metadata():
    chunks = chunk_document(DOC, source="syllabi/cs-439.md")
    assert len(chunks) == 2
    assert all(c.metadata["course_number"] == "39" for c in chunks)
    assert chunks[0].text.startswith("[CS 439 Principles of Computer Systems] CS 439 > Grading")
    assert [c.metadata["chunk_index"] for c in chunks] == [0, 1]


def test_course_number_parsing():
    assert course_number("CS 439") == "39"
    assert course_number("cs314h") == "14H"
    assert course_number("C S X39") == "39"
    assert course_number("Math 408C") is None
    assert find_course_numbers("Compare CS 439 and CS 314 vs cs 439") == ["39", "14"]
