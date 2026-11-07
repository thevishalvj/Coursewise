"""Split markdown documents into chunks: first by heading, then by size."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import CHUNK_OVERLAP, CHUNK_SIZE

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.M)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Read simple `key: value` front matter. Returns (metadata, body)."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, text[match.end():]


def split_by_heading(body: str) -> list[tuple[str, str]]:
    """Return (heading path, section text) pairs. Text before any heading gets ''."""
    sections, stack = [], []
    matches = list(HEADING_RE.finditer(body))
    if not matches or matches[0].start() > 0:
        lead = body[: matches[0].start() if matches else len(body)].strip()
        if lead:
            sections.append(("", lead))
    for i, m in enumerate(matches):
        level, title = len(m.group(1)), m.group(2).strip()
        stack = [s for s in stack if s[0] < level] + [(level, title)]
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[m.end():end].strip()
        if content:
            sections.append((" > ".join(t for _, t in stack), content))
    return sections


def split_by_size(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into pieces of at most `size` characters with `overlap` shared.

    Prefers to break at paragraph, then sentence, then word boundaries.
    """
    if len(text) <= size:
        return [text]
    pieces, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            for sep in ("\n\n", ". ", "\n", " "):
                cut = window.rfind(sep)
                if cut > size // 2:
                    end = start + cut + len(sep)
                    break
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        # do not start in the middle of a word
        while start < end and not text[start - 1].isspace():
            start += 1
    return [p for p in pieces if p]


def chunk_document(text: str, source: str = "") -> list[Chunk]:
    meta, body = parse_front_matter(text)
    meta["source"] = source
    chunks = []
    for heading, section in split_by_heading(body):
        for piece in split_by_size(section):
            # Prefix the heading so each chunk makes sense on its own.
            label = f"{meta.get('course_code', '')} {meta.get('title', '')}".strip()
            prefix = f"[{label}] {heading}\n" if heading else f"[{label}]\n"
            chunks.append(Chunk(text=prefix + piece, metadata={**meta, "heading": heading}))
    for i, c in enumerate(chunks):
        c.metadata["chunk_index"] = i
    return chunks


def chunk_directory(root: Path) -> list[Chunk]:
    chunks = []
    for path in sorted(root.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        chunks.extend(chunk_document(path.read_text(encoding="utf-8"), str(path.relative_to(root))))
    return chunks
