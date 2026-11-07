"""MCP server that exposes Coursewise course search to Claude, Cursor, or any MCP client.

The tools return course text with sources. The client's own model does the reasoning,
so this server does not call Gemini.

Run over stdio (from ai/):
    python -m coursewise.mcp_server

See the root README for Claude Code, Claude Desktop, and Cursor config.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .chunking import parse_front_matter
from .config import MARKDOWN_DIR
from .courses import course_number

server = MCPServer(
    name="coursewise",
    title="Coursewise",
    instructions=(
        "Search UT Austin computer science course catalog entries and syllabi. "
        "Catalog codes use X for the credit-hour digit, so CS X39 is CS 339 or CS 439. "
        "Cite the `source` field when you use a result."
    ),
)

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def _documents() -> list[tuple[dict, str]]:
    docs = []
    for path in sorted(MARKDOWN_DIR.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        meta["source"] = str(path.relative_to(MARKDOWN_DIR))
        docs.append((meta, body.strip()))
    return docs


def search_courses(
    query: str, course_codes: list[str] | None = None, doc_type: str | None = None, k: int = 5
) -> dict[str, Any]:
    from .search import search

    k = max(1, min(k, 20))
    hits = search(query, course_codes=course_codes or None, doc_type=doc_type, k=k)
    return {
        "results": [
            {
                "course_code": h.metadata.get("course_code"),
                "title": h.metadata.get("title"),
                "doc_type": h.metadata.get("doc_type"),
                "source": h.metadata.get("source"),
                "score": round(h.score, 3),
                "text": h.text,
            }
            for h in hits
        ]
    }


def get_course(course_code: str) -> dict[str, Any]:
    number = course_number(course_code)
    if not number:
        return {"error": f"Could not read a course number from {course_code!r}. Try a code like 'CS 439'."}
    docs = [
        {
            "course_code": m.get("course_code"),
            "title": m.get("title"),
            "doc_type": m.get("doc_type"),
            "source": m["source"],
            "text": body,
        }
        for m, body in _documents()
        if m.get("course_number") == number
    ]
    if not docs:
        return {"error": f"No documents found for {course_code}."}
    return {"documents": docs}


def list_courses(level: str | None = None) -> dict[str, Any]:
    courses = [
        {"course_code": m.get("course_code"), "title": m.get("title"), "level": m.get("level")}
        for m, _ in _documents()
        if m.get("doc_type") == "catalog" and (not level or (m.get("level") or "").lower() == level.lower())
    ]
    return {"count": len(courses), "courses": courses}


@server.tool(name="search_courses", title="Search courses", annotations=READ_ONLY, structured_output=True)
def search_courses_tool(
    query: str, course_codes: list[str] | None = None, doc_type: str | None = None, k: int = 5
) -> dict[str, Any]:
    """Semantic search over UT CS course catalog entries and syllabi.

    Args:
        query: What to look for, e.g. "operating systems with multithreaded programming".
        course_codes: Optional filter like ["CS 439", "CS 314"].
        doc_type: Optional filter: "catalog" or "syllabus".
        k: Number of results, 1 to 20.
    """
    return search_courses(query, course_codes, doc_type, k)


@server.tool(name="get_course", title="Get course", annotations=READ_ONLY, structured_output=True)
def get_course_tool(course_code: str) -> dict[str, Any]:
    """Full catalog entry and any syllabi for one course, e.g. "CS 439"."""
    return get_course(course_code)


@server.tool(name="list_courses", title="List courses", annotations=READ_ONLY, structured_output=True)
def list_courses_tool(level: str | None = None) -> dict[str, Any]:
    """List CS courses in the catalog.

    Args:
        level: Optional filter: "Lower-Division", "Upper-Division", "Graduate", or "Professional".
    """
    return list_courses(level)


if __name__ == "__main__":
    server.run("stdio")
