from api.models import Finding, Source, Turn
from presenters import messages

TURN = Turn(
    message="Is my field stressed?",
    answer="Yes. [cg-06-fert-3]",
    tools_called=["list_fields", "save_requirements", "ask_weather_agent", "ask_farm_context_agent", "ask_knowledge_agent"],
    requirements={"field_id": "SL-PADDY-SAT-FAIL", "crop": "paddy", "problem": "stress", "timeframe": "now"},
    findings={
        "weather": Finding(summary="**46 mm** forecast.", data={"rainfall_last_7_days_mm": 112.0, "heavy_rain_expected": True}),
        "farm_context": Finding(summary="Satellite data timed out.", data={}),
        "knowledge": Finding(
            summary="Wait. [cg-06-fert-3]",
            data={"found": True, "citations": ["cg-06-fert-3"]},
            sources=[Source(id="cg-06-fert-3", source="CG-06.pdf", page=3, text="Avoid spraying before rain.", rerank_score=0.991)],
        ),
    },
    seconds=44.9,
)


def test_a_turn_is_question_then_trace_then_answer_then_sources():
    turn = messages.turn_messages(TURN, 0)
    titles = [m.get("metadata", {}).get("title") for m in turn]

    assert turn[0] == {"role": "user", "content": "Is my field stressed?"}
    assert titles[1:7] == [
        "Worked with 3 agents",
        "Looked up your registered fields",
        "Saved what you need to memory",
        "Weather agent",
        "Farm context agent",
        "Knowledge agent",
    ]
    assert turn[7] == {"role": "assistant", "content": "Yes. [1]"}
    assert titles[8] == "Used 1 source"


def test_the_trace_nests_every_step_and_flags_the_specialist_that_had_no_data():
    parent, *steps = messages.trace(TURN, 4)

    assert parent["metadata"] == {"title": "Worked with 3 agents", "id": "turn-4", "status": "done", "duration": 45,
                                  "log": "No data from Farm context"}
    assert all(step["metadata"]["parent_id"] == "turn-4" for step in steps)
    weather, satellite = steps[2], steps[3]
    assert weather["metadata"]["log"] == "Done" and "Rainfall last 7 days **112 mm**" in weather["content"]
    assert satellite["metadata"]["log"] == "No data"
    assert steps[1]["content"] == "SL-PADDY-SAT-FAIL · paddy · stress · now"


def test_a_turn_with_no_tools_has_no_trace():
    assert messages.trace(Turn(message="Thanks", answer="You're welcome.", tools_called=[]), 0) == []


def test_sources_list_the_passages_with_their_page_score_and_a_quote():
    (sources,) = messages.source_list(TURN)
    assert sources["metadata"] == {"title": "Used 1 source", "status": "done"}
    assert sources["content"] == "1. **CG-06.pdf**, page 3 · relevance 0.99\n\n   > Avoid spraying before rain."


def test_pending_and_failed_questions_are_shown_after_the_conversation():
    pending = messages.chat_messages([TURN], pending="And tomorrow?")
    assert pending[-2] == {"role": "user", "content": "And tomorrow?"}
    assert pending[-1]["metadata"] == {"title": "Asking the agents", "status": "pending"}

    failed = messages.chat_messages([], failed=("Hi", "AgriVibe took too long."))
    assert failed[-1]["content"] == "⚠️ **No answer this time.** AgriVibe took too long."
