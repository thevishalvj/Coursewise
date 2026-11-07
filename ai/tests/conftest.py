import pytest

from coursewise.search import Hit


class FakeLLM:
    """Records prompts and returns a canned answer."""

    def __init__(self, answer: str = "Fake answer [1]."):
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.answer


def make_hit(course: str, score: float, doc_type: str = "catalog", text: str = "text") -> Hit:
    number = course.split("X")[-1]
    return Hit(
        text=f"[{course}] {text}",
        metadata={
            "course_code": course,
            "course_number": number,
            "doc_type": doc_type,
            "source": f"{doc_type}/{course.lower().replace(' ', '-')}.md",
            "title": "T",
        },
        score=score,
    )


class FakeSearch:
    """Returns preset hits and records how it was called."""

    def __init__(self, hits_by_course=None, default=None):
        self.hits_by_course = hits_by_course or {}
        self.default = default or []
        self.calls: list[dict] = []

    def __call__(self, query, course_codes=None, doc_type=None, k=5):
        self.calls.append({"query": query, "course_codes": course_codes, "doc_type": doc_type, "k": k})
        if course_codes and len(course_codes) == 1 and course_codes[0] in self.hits_by_course:
            hits = self.hits_by_course[course_codes[0]]
        else:
            hits = self.default
        if doc_type:
            hits = [h for h in hits if h.metadata["doc_type"] == doc_type]
        return hits[:k]


@pytest.fixture
def fake_llm():
    return FakeLLM()
