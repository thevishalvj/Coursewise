from fastapi.testclient import TestClient

from coursewise.agent import build_graph
from coursewise.api import app, get_agent

from .conftest import FakeLLM, FakeSearch, make_hit


def client_with(search, llm=None):
    app.dependency_overrides[get_agent] = lambda: build_graph(llm=llm or FakeLLM(), search_fn=search)
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_ask_returns_answer_and_sources():
    client = client_with(FakeSearch(default=[make_hit("CS X39", 0.6)]))
    body = client.post("/ask", json={"question": "What does CS 439 cover?"}).json()
    assert body["answer"] == "Fake answer [1]."
    assert body["route"] == "course_info"
    assert body["sources"][0]["course_code"] == "CS X39"
    assert body["sources"][0]["id"] == 1
    assert isinstance(body["latency_ms"], int)


def test_ask_off_topic_has_no_sources():
    client = client_with(FakeSearch(default=[make_hit("CS X99", 0.1)]))
    body = client.post("/ask", json={"question": "Who won the Super Bowl?"}).json()
    assert body["route"] == "off_topic"
    assert body["sources"] == []


def test_ask_rejects_empty_question():
    client = client_with(FakeSearch())
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_accepts_course_filter():
    search = FakeSearch(default=[make_hit("CS X39", 0.6)])
    client_with(search).post("/ask", json={"question": "What is covered?", "course_codes": ["CS 439"]})
    assert search.calls[0]["course_codes"] == ["CS 439"]
