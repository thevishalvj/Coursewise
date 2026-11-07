"""FastAPI service.

Run (from ai/):
    uvicorn coursewise.api:app --reload --port 8000
"""

from __future__ import annotations

import time
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

from .agent import build_graph, sources_from_hits  # noqa: E402

app = FastAPI(title="Coursewise AI", version="0.1.0")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    course_codes: list[str] | None = Field(default=None, description='Optional filter, e.g. ["CS 439"]')


class Source(BaseModel):
    id: int
    course_code: str | None
    title: str | None
    doc_type: str | None
    heading: str | None
    source: str | None
    url: str | None
    score: float
    snippet: str


class AskResponse(BaseModel):
    answer: str
    route: str
    sources: list[Source]
    latency_ms: int


@lru_cache(maxsize=1)
def get_agent():
    return build_graph()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, agent=Depends(get_agent)) -> AskResponse:
    start = time.perf_counter()
    try:
        state = agent.invoke({"question": req.question.strip(), "course_codes": req.course_codes or []})
    except RuntimeError as exc:  # e.g. missing API key
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AskResponse(
        answer=state["answer"],
        route=state["route"],
        sources=sources_from_hits(state.get("hits", [])),
        latency_ms=int((time.perf_counter() - start) * 1000),
    )
