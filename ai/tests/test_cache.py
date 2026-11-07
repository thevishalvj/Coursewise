import fakeredis

from coursewise.cache import PREFIX, AnswerCache, cache_key, normalize


def test_normalize_ignores_case_spacing_and_trailing_punctuation():
    assert normalize("  What does CS 439   cover?? ") == "what does cs 439 cover"


def test_key_depends_on_question_courses_and_model():
    base = cache_key("What does CS 439 cover?")
    assert base == cache_key("what does cs 439 cover")
    assert base != cache_key("What does CS 314 cover?")
    assert base != cache_key("What does CS 439 cover?", ["CS 439"])
    assert base != cache_key("What does CS 439 cover?", model="other-model")
    assert cache_key("q", ["cs 439", "CS 314"]) == cache_key("q", ["CS 314", "CS 439"])
    assert base.startswith(PREFIX)


def test_set_get_and_ttl():
    redis = fakeredis.FakeRedis()
    cache = AnswerCache(redis, ttl=60)
    cache.set("k", {"answer": "a"})
    assert cache.get("k") == {"answer": "a"}
    assert 0 < redis.ttl("k") <= 60
    assert cache.get("missing") is None


def test_clear_only_removes_answer_keys():
    redis = fakeredis.FakeRedis()
    cache = AnswerCache(redis)
    cache.set(cache_key("q1"), {"a": 1})
    cache.set(cache_key("q2"), {"a": 2})
    redis.set("other:key", "keep")
    assert cache.clear() == 2
    assert redis.get("other:key") == b"keep"
