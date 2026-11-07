from coursewise.agent import NO_INFO, OFF_TOPIC, build_graph, classify

from .conftest import FakeLLM, FakeSearch, make_hit


def test_classify_routes():
    assert classify("What does CS 439 cover?") == "course_info"
    assert classify("How is CS 439 graded?") == "grading"
    assert classify("What's the late policy for CS 314?") == "grading"
    assert classify("Compare CS 439 and CS 350F") == "compare"
    assert classify("CS 312 or CS 314 first?") == "compare"
    assert classify("Which course teaches SQL?") == "course_info"


def test_classify_uses_explicit_course_codes():
    assert classify("Which is harder?", course_codes=["CS 439", "CS 429"]) == "compare"


def test_course_info_filters_by_course_and_calls_llm():
    search = FakeSearch(default=[make_hit("CS X39", 0.6)])
    llm = FakeLLM()
    state = build_graph(llm=llm, search_fn=search).invoke({"question": "What does CS 439 cover?"})
    assert state["route"] == "course_info"
    assert search.calls[0]["course_codes"] == ["CS X39"]
    assert state["answer"] == llm.answer
    assert "[1]" in llm.calls[0][1]  # numbered sources in the prompt


def test_off_topic_skips_llm():
    search = FakeSearch(default=[make_hit("CS X99", 0.12)])
    llm = FakeLLM()
    state = build_graph(llm=llm, search_fn=search).invoke({"question": "banana bread recipe"})
    assert state["route"] == "off_topic"
    assert state["answer"] == OFF_TOPIC
    assert state["hits"] == []
    assert llm.calls == []


def test_weak_matches_filtered_out_without_course():
    search = FakeSearch(default=[make_hit("CS X27E", 0.4), make_hit("CS X99", 0.1, text="weak")])
    llm = FakeLLM()
    state = build_graph(llm=llm, search_fn=search).invoke({"question": "Which course teaches SQL?"})
    assert [h.score for h in state["hits"]] == [0.4]
    assert "weak" not in llm.calls[0][1]


def test_named_course_keeps_low_scoring_hits():
    search = FakeSearch(hits_by_course={"CS X12": [make_hit("CS X12", 0.19)], "CS X14": [make_hit("CS X14", 0.24)]})
    state = build_graph(llm=FakeLLM(), search_fn=search).invoke({"question": "Compare CS 312 and CS 314."})
    assert len(state["hits"]) == 2


def test_grading_searches_syllabi_only_and_admits_no_info():
    search = FakeSearch(default=[make_hit("CS X39", 0.6, doc_type="catalog")])
    llm = FakeLLM()
    state = build_graph(llm=llm, search_fn=search).invoke({"question": "How is CS 439 graded?"})
    assert state["route"] == "grading"
    assert search.calls[0]["doc_type"] == "syllabus"
    assert state["answer"] == NO_INFO
    assert llm.calls == []


def test_grading_answers_from_syllabus():
    search = FakeSearch(default=[make_hit("CS X39", 0.7, doc_type="syllabus", text="Exams 60%")])
    llm = FakeLLM()
    state = build_graph(llm=llm, search_fn=search).invoke({"question": "How is CS 439 graded?"})
    assert state["answer"] == llm.answer
    assert "Exams 60%" in llm.calls[0][1]


def test_compare_retrieves_each_course():
    search = FakeSearch(hits_by_course={"CS X39": [make_hit("CS X39", 0.6)], "CS X14": [make_hit("CS X14", 0.5)]})
    llm = FakeLLM()
    state = build_graph(llm=llm, search_fn=search).invoke({"question": "Compare CS 439 and CS 314"})
    assert state["route"] == "compare"
    assert [c["course_codes"] for c in search.calls] == [["CS X39"], ["CS X14"]]
    assert {h.metadata["course_code"] for h in state["hits"]} == {"CS X39", "CS X14"}
