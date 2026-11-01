import gradio as gr
import pytest

import app
from client import BackendUnavailable, ChatReply, ConversationNotFound, Finding, Source, Thread, ThreadSummary, Turn

UPDATED = "2026-11-01T10:00:24Z"


class FakeClient:
    """Stands in for AgriVibeClient: canned replies, optional errors, and a record of each call."""

    def __init__(self, reply=None, error=None, threads=(), thread=None):
        self.reply, self.error, self.threads, self.thread, self.calls = reply, error, list(threads), thread, []

    def is_up(self):
        return self.error is None

    def chat(self, message, thread_id=None):
        self.calls.append(("chat", message, thread_id))
        if self.error:
            raise self.error
        return self.reply

    def list_threads(self):
        return self.threads

    def get_thread(self, thread_id):
        self.calls.append(("get_thread", thread_id))
        if self.thread is None:
            raise ConversationNotFound("That conversation no longer exists. Start a new one.")
        return self.thread

    def delete_thread(self, thread_id):
        self.calls.append(("delete_thread", thread_id))


TURN = Turn(
    message="Should I spray?",
    answer="Wait. Heavy rain is expected. [cg-06-fertiliser-3]",
    tools_called=["list_fields", "save_requirements", "ask_weather_agent", "ask_farm_context_agent",
                  "ask_knowledge_agent", "ask_advisory_agent"],
    requirements={"field_id": "SL-PADDY-SAT-FAIL", "crop": "paddy", "problem": "spraying", "timeframe": "this week"},
    findings={
        "weather": Finding(summary="**46 mm** forecast.", data={"rainfall_forecast_next_48_hours_mm": 46.0, "heavy_rain_expected": True}),
        "farm_context": Finding(summary="Satellite data timed out.", data={}),
        "knowledge": Finding(
            summary="Do not spray before rain. [cg-06-fertiliser-3]",
            data={"found": True, "citations": ["cg-06-fertiliser-3"]},
            sources=[Source(id="cg-06-fertiliser-3", source="CG-06.pdf", page=3, text="Avoid spraying…", rerank_score=0.991)],
        ),
    },
    seconds=44.9,
)
REPLY = ChatReply(**TURN.model_dump(), thread_id="thread-1")
SUMMARY = ThreadSummary(thread_id="thread-1", title="Should I spray?", updated_at=UPDATED, turns=1)
FOLLOW_UP = Turn(message="Thanks", answer="You're welcome.", tools_called=[], seconds=2.0)
THREAD = Thread(**SUMMARY.model_dump(), history=[TURN, FOLLOW_UP])


def event(**data):
    """What a component's data-event click sends: its data-* attributes."""
    return gr.EventData(None, data)


@pytest.fixture
def fake(monkeypatch):
    def use(**kwargs):
        client = FakeClient(**kwargs)
        monkeypatch.setattr(app, "client", client)
        return client
    return use


def test_asking_shows_the_question_and_a_thinking_message_at_once():
    page, question = app.ask([], event(text="  Should I spray?  "))

    assert question == "Should I spray?"
    assert '<div class="bubble">Should I spray?</div>' in page
    assert "data-pending" in page and "Asking the agents" in page


def test_an_empty_question_is_refused():
    with pytest.raises(gr.Error):
        app.ask([], event(text="   "))


def test_answer_fills_the_page_the_header_and_the_sidebar(fake, caplog):
    client = fake(reply=REPLY, threads=[SUMMARY])

    page, thread_id, turns, header, history = app.answer("Should I spray?", None, [])

    assert client.calls == [("chat", "Should I spray?", None)]  # no farmer id is ever sent
    assert thread_id == "thread-1" and turns == [REPLY]
    assert "data-pending" not in page and "Heavy rain is expected." in page
    # The trace: every tool in order, the failed specialist flagged without opening it.
    assert page.index("Looked up your registered fields") < page.index("Weather agent") < page.index("Advisory agent")
    assert "Worked with 4 agents" in page and "· 45s" in page and "No data from Farm context" in page
    # The answer's citation became a numbered chip that matches the sources list.
    assert '<span class="citation" title="CG-06.pdf · p. 3">1</span>' in page and "[cg-06" not in page
    assert "Used 1 source" in page and "0.99" in page
    assert "Should I spray?" in header and "SL-PADDY-SAT-FAIL" in header
    assert 'data-active' in history and "Should I spray?" in history
    assert '"farmer_id": "frm_7f3a9c2e"' in caplog.text
    assert '"specialists": {"weather": "ok", "farm_context": "no_data", "knowledge": "ok"}' in caplog.text


def test_a_backend_failure_is_shown_in_the_conversation_not_a_crash(fake):
    fake(error=BackendUnavailable("AgriVibe took too long to answer."))

    page, thread_id, turns, *_ = app.answer("Should I spray again?", "thread-1", [TURN])

    assert "No answer this time" in page and "took too long" in page
    assert "Should I spray again?" in page and "Heavy rain is expected." in page  # earlier turns stay
    assert thread_id == "thread-1" and turns == [TURN]  # the conversation is kept, so the farmer can try again


def test_a_deleted_conversation_starts_fresh(fake):
    fake(error=ConversationNotFound("That conversation no longer exists. Start a new one."))

    page, thread_id, turns, *_ = app.answer("Hi", "deleted-thread", [TURN])

    assert "no longer exists" in page
    assert thread_id is None and turns == []


def test_opening_a_conversation_restores_it(fake):
    fake(thread=THREAD, threads=[SUMMARY])

    page, thread_id, turns, header, _ = app.open_thread(event(id="thread-1"))

    assert page.count('data-role="user"') == 2 and "You're welcome." in page
    assert thread_id == "thread-1" and turns == [TURN, FOLLOW_UP]
    assert "SL-PADDY-SAT-FAIL" in header  # the last field saved, even though the last turn saved none


def test_a_refresh_reopens_the_saved_conversation(fake):
    fake(thread=THREAD, threads=[SUMMARY])

    alert, _, thread_id, turns, header, _ = app.on_load("thread-1")

    assert alert.visible is False and thread_id == "thread-1" and len(turns) == 2
    assert "Online" in header


def test_a_saved_conversation_that_is_gone_starts_fresh(fake):
    fake(thread=None, threads=[])

    _, page, thread_id, turns, *_ = app.on_load("deleted-thread")

    assert page == app.EMPTY_STATE and thread_id is None and turns == []


def test_an_offline_backend_shows_the_alert_and_keeps_the_saved_conversation(fake):
    fake(error=BackendUnavailable("down"))

    alert, _, thread_id, _, header, _ = app.on_load("thread-1")

    assert alert.visible is True and "Offline" in header
    assert thread_id is not None  # gr.skip(): the browser keeps its saved thread for the next reload


def test_deleting_the_open_conversation_starts_fresh(fake):
    client = fake(threads=[])

    page, thread_id, turns, *_ = app.delete_thread("thread-1", event(id="thread-1"))

    assert ("delete_thread", "thread-1") in client.calls
    assert page == app.EMPTY_STATE and thread_id is None and turns == []


def test_deleting_another_conversation_keeps_the_open_one(fake):
    client = fake(threads=[SUMMARY])

    page, *_, history = app.delete_thread("thread-1", event(id="thread-2"))

    assert ("delete_thread", "thread-2") in client.calls
    assert "data-active" in history  # thread-1 is still open and highlighted
    assert page.__class__ is not str  # gr.skip(): the open conversation is left alone
