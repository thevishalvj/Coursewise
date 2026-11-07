"""LangGraph agent: classify -> retrieve -> filter -> generate.

Routes:
    course_info  what a course covers (default)
    grading      grading and policy questions; searches syllabi only
    compare      two or more courses; retrieves for each course separately
    off_topic    not about courses; answered without calling the LLM
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypedDict

from langgraph.graph import END, StateGraph

from .config import MIN_SCORE
from .courses import find_course_numbers
from .llm import LLM, get_llm
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .search import Hit, search

GRADING_RE = re.compile(
    r"\b(grad(e|ed|es|ing)|exam|midterm|final|quiz|homework|late|curve|attendance|policy|policies|weight|percent|%)",
    re.I,
)

NO_INFO = "I don't have information about that in my sources yet."
OFF_TOPIC = (
    "I can only help with questions about UT CS courses, like what a course covers, "
    "how it's graded, or how two courses compare."
)


class AgentState(TypedDict, total=False):
    question: str
    course_codes: list[str]
    route: str
    hits: list[Hit]
    answer: str


SearchFn = Callable[..., list[Hit]]


def classify(question: str, course_codes: list[str] | None = None) -> str:
    """Pick a route from the question text.

    Off-topic is decided in the retrieve step: a question that names no course and
    matches nothing above MIN_SCORE is off-topic.
    """
    courses = find_course_numbers(question) or list(course_codes or [])
    if len(courses) >= 2:
        return "compare"
    if GRADING_RE.search(question):
        return "grading"
    return "course_info"


def format_context(hits: list[Hit]) -> str:
    return "\n\n".join(f"[{i}] ({h.metadata.get('doc_type', '')}) {h.text}" for i, h in enumerate(hits, 1))


def build_graph(llm: LLM | None = None, search_fn: SearchFn = search, min_score: float = MIN_SCORE):
    def classify_node(state: AgentState) -> AgentState:
        return {"route": classify(state["question"], state.get("course_codes"))}

    def retrieve_node(state: AgentState) -> AgentState:
        q, route = state["question"], state["route"]
        codes = state.get("course_codes") or [f"CS X{n}" for n in find_course_numbers(q)]
        if route == "compare":
            hits: list[Hit] = []
            for code in codes:
                hits.extend(search_fn(q, course_codes=[code], k=3))
        elif route == "grading":
            hits = search_fn(q, course_codes=codes or None, doc_type="syllabus", k=5)
        else:
            hits = search_fn(q, course_codes=codes or None, k=5)
        # No course named and nothing relevant at all: treat as off-topic.
        if not codes and (not hits or max(h.score for h in hits) < min_score):
            return {"hits": [], "route": "off_topic"}
        return {"hits": hits}

    def filter_node(state: AgentState) -> AgentState:
        # When the question names a course, the course filter already guarantees the hits
        # are about that course, and phrasing like "compare X and Y" scores low against a
        # course description. So the score cutoff only applies to unfiltered searches.
        if state.get("course_codes") or find_course_numbers(state["question"]):
            return {}
        return {"hits": [h for h in state["hits"] if h.score >= min_score]}

    def generate_node(state: AgentState) -> AgentState:
        if state["route"] == "off_topic":
            return {"answer": OFF_TOPIC}
        if not state["hits"]:
            return {"answer": NO_INFO}
        model = llm or get_llm()
        prompt = build_user_prompt(state["question"], state["route"], format_context(state["hits"]))
        return {"answer": model.complete(SYSTEM_PROMPT, prompt)}

    def after_retrieve(state: AgentState) -> str:
        return "generate" if state["route"] == "off_topic" else "filter"

    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("filter", filter_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve")
    graph.add_conditional_edges("retrieve", after_retrieve, {"filter": "filter", "generate": "generate"})
    graph.add_edge("filter", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def sources_from_hits(hits: list[Hit]) -> list[dict]:
    return [
        {
            "id": i,
            "course_code": h.metadata.get("course_code"),
            "title": h.metadata.get("title"),
            "doc_type": h.metadata.get("doc_type"),
            "heading": h.metadata.get("heading"),
            "source": h.metadata.get("source"),
            "url": h.metadata.get("source_url"),
            "score": round(h.score, 3),
            "snippet": h.text[:300],
        }
        for i, h in enumerate(hits, 1)
    ]
