"""Parse course codes out of user text."""

from __future__ import annotations

import re

# Matches "CS 439", "C S 439", "cs439", "CS 439H", "CS X39".
COURSE_RE = re.compile(r"\bC\s?S\s*([X0-9])(\d{2}[A-Z]?)\b", re.I)


def course_number(code: str) -> str | None:
    """'CS 439' -> '39'. The first digit is credit hours, which the catalog writes as X."""
    match = COURSE_RE.search(code)
    return match.group(2).upper() if match else None


def find_course_numbers(text: str) -> list[str]:
    """All course numbers mentioned in text, in order, without duplicates."""
    seen: list[str] = []
    for m in COURSE_RE.finditer(text):
        num = m.group(2).upper()
        if num not in seen:
            seen.append(num)
    return seen
