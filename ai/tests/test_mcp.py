"""MCP server tests through an in-memory MCP client."""

import asyncio

import pytest
from mcp import Client

from coursewise.config import CHROMA_DIR
from coursewise.mcp_server import server


def call(tool: str, args: dict) -> dict:
    async def run():
        async with Client(server) as client:
            result = await client.call_tool(tool, args)
            assert not result.is_error
            return result.structured_content

    return asyncio.run(run())


def test_tools_are_listed_and_read_only():
    async def run():
        async with Client(server) as client:
            return (await client.list_tools()).tools

    tools = {t.name: t for t in asyncio.run(run())}
    assert set(tools) == {"search_courses", "get_course", "list_courses"}
    assert all(t.annotations.read_only_hint for t in tools.values())


def test_get_course_returns_catalog_text():
    data = call("get_course", {"course_code": "CS 439"})
    doc = data["documents"][0]
    assert doc["course_code"] == "CS X39"
    assert "virtual memory" in doc["text"]


def test_get_course_rejects_non_cs_code():
    assert "error" in call("get_course", {"course_code": "Math 408"})


def test_list_courses_filters_by_level():
    data = call("list_courses", {"level": "Upper-Division"})
    assert data["count"] > 10
    assert all(c["level"] == "Upper-Division" for c in data["courses"])


@pytest.mark.skipif(not CHROMA_DIR.exists(), reason="index not built")
def test_search_courses_finds_sql_course():
    data = call("search_courses", {"query": "which class teaches SQL", "k": 3})
    assert "catalog/cs-x27e.md" in [r["source"] for r in data["results"]]
