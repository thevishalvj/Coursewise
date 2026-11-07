import fakeredis
from fastapi.testclient import TestClient

from coursewise.agent import build_graph
from coursewise.api import app, get_agent
from coursewise.cache import AnswerCache, NullCache, get_cache

from .conftest import FakeLLM, FakeSearch, make_hit


def client_with(search, llm=None, cache=None):
    app.dependency_overrides[get_agent] = lambda: build_graph(llm=llm or FakeLLM(), search_fn=search)
    app.dependency_overrides[get_cache] = lambda: cache or NullCache()
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


def test_repeated_question_is_served_from_cache():
    search, llm = FakeSearch(default=[make_hit("CS X39", 0.6)]), FakeLLM()
    client = client_with(search, llm, cache=AnswerCache(fakeredis.FakeRedis()))
    first = client.post("/ask", json={"question": "What does CS 439 cover?"}).json()
    second = client.post("/ask", json={"question": "  what does cs 439 cover  "}).json()
    assert first["cached"] is False
    assert second["cached"] is True
    assert second["answer"] == first["answer"]
    assert second["sources"] == first["sources"]
    assert len(llm.calls) == 1


def test_cache_down_still_answers():
    class BrokenRedis:
        def get(self, key):
            raise ConnectionError("redis down")

        def set(self, *args, **kwargs):
            raise ConnectionError("redis down")

    client = client_with(FakeSearch(default=[make_hit("CS X39", 0.6)]), cache=AnswerCache(BrokenRedis()))
    body = client.post("/ask", json={"question": "What does CS 439 cover?"}).json()
    assert body["answer"] == "Fake answer [1]."
    assert body["cached"] is False


def test_llm_failure_returns_503_and_is_not_cached():
    from coursewise.llm import LLMUnavailable

    class DownLLM:
        def complete(self, system, user):
            raise LLMUnavailable("Gemini is unavailable right now")

    cache = AnswerCache(fakeredis.FakeRedis())
    client = client_with(FakeSearch(default=[make_hit("CS X39", 0.6)]), llm=DownLLM(), cache=cache)
    resp = client.post("/ask", json={"question": "What does CS 439 cover?"})
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"]
    assert cache.client.keys("*") == []
