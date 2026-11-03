from types import SimpleNamespace

import gradio as gr
import pytest

import app
from api import client
from api.client import BackendUnavailable, ConversationNotFound
from api.models import ChatReply, Finding, Source, Thread, ThreadSummary, Turn
from handlers import chat, conversations

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


def opening(url_thread_id=None):
    """A stand-in for the gr.Request of a page opened at /?thread=<id>."""
    return SimpleNamespace(query_params={"thread": url_thread_id} if url_thread_id else {})


def text(messages):
    """All the text in a list of chat messages, titles included, for simple `in` checks."""
    return "\n".join(m["content"] + " " + " ".join(str(v) for v in m.get("metadata", {}).values()) for m in messages)


@pytest.fixture
def fake(monkeypatch):
    def use(**kwargs):
        fake_client = FakeClient(**kwargs)
        monkeypatch.setattr(client, "agrivibe", fake_client)  # handlers look it up when they run
        return fake_client
    return use


def test_asking_shows_the_question_and_a_pending_thought_at_once():
    box, messages, question = chat.ask("  Should I spray?  ", [])

    assert box == "" and question == "Should I spray?"
    assert messages[0] == {"role": "user", "content": "Should I spray?"}
    assert messages[1]["metadata"]["status"] == "pending"


def test_an_empty_question_is_refused():
    with pytest.raises(gr.Error):
        chat.ask("   ", [])


def test_a_suggestion_is_asked_as_if_typed():
    _, messages, question = chat.suggest([], gr.SelectData(None, {"index": 0, "value": {"text": "Is it raining?"}}))
    assert question == "Is it raining?" and messages[0]["content"] == "Is it raining?"


def test_answer_fills_the_chat_the_header_and_the_sidebar(fake, caplog):
    client = fake(reply=REPLY, threads=[SUMMARY])

    messages, thread_id, turns, header, threads = chat.answer("Should I spray?", None, [])

    assert client.calls == [("chat", "Should I spray?", None)]  # no farmer id is ever sent
    assert thread_id == "thread-1" and turns == [REPLY]
    assert messages[0] == {"role": "user", "content": "Should I spray?"}
    assert any(m["content"] == "Wait. Heavy rain is expected. [1]" for m in messages)  # the citation became [1]
    assert "Used 1 source" in text(messages)
    assert "Should I spray?" in header and "SL-PADDY-SAT-FAIL" in header
    assert threads.value == "thread-1" and threads.choices[0] == ("Should I spray?", "thread-1")
    assert '"farmer_id": "frm_7f3a9c2e"' in caplog.text
    assert '"specialists": {"weather": "ok", "farm_context": "no_data", "knowledge": "ok"}' in caplog.text


def test_a_backend_failure_is_shown_in_the_chat_not_a_crash(fake):
    fake(error=BackendUnavailable("AgriVibe took too long to answer."))

    messages, thread_id, turns, *_ = chat.answer("Should I spray again?", "thread-1", [TURN])

    assert "took too long" in messages[-1]["content"] and messages[-2]["content"] == "Should I spray again?"
    assert messages[0]["content"] == "Should I spray?"  # earlier turns stay
    assert thread_id == "thread-1" and turns == [TURN]  # the conversation is kept, so the farmer can try again


def test_a_deleted_conversation_starts_fresh(fake):
    fake(error=ConversationNotFound("That conversation no longer exists. Start a new one."))

    messages, thread_id, turns, *_ = chat.answer("Hi", "deleted-thread", [TURN])

    assert "no longer exists" in messages[-1]["content"]
    assert thread_id is None and turns == []


def test_opening_a_conversation_restores_it(fake):
    fake(thread=THREAD, threads=[SUMMARY])

    messages, thread_id, turns, header, _ = conversations.open_thread("thread-1")

    assert [m["content"] for m in messages if m["role"] == "user"] == ["Should I spray?", "Thanks"]
    assert messages[-1]["content"] == "You're welcome."
    assert thread_id == "thread-1" and turns == [TURN, FOLLOW_UP]
    assert "SL-PADDY-SAT-FAIL" in header  # the last field saved, even though the last turn saved none


def test_the_url_reopens_its_conversation(fake):
    fake(thread=THREAD, threads=[SUMMARY])

    alert, _, thread_id, turns, header, threads = conversations.on_load(opening("thread-1"))

    assert alert.visible is False and thread_id == "thread-1" and len(turns) == 2
    assert "Backend online" in header and threads.value == "thread-1"


def test_a_url_conversation_that_is_gone_starts_fresh(fake):
    fake(thread=None, threads=[])

    _, messages, thread_id, turns, *_ = conversations.on_load(opening("deleted-thread"))

    assert messages == [] and thread_id is None and turns == []


def test_a_plain_url_opens_a_new_conversation(fake):
    fake(threads=[SUMMARY])

    _, messages, thread_id, turns, *_ = conversations.on_load(opening())

    assert messages == [] and thread_id is None and turns == []


def test_an_offline_backend_shows_the_alert_and_keeps_the_url_conversation(fake):
    fake(error=BackendUnavailable("down"))

    alert, _, thread_id, _, header, _ = conversations.on_load(opening("thread-1"))

    assert alert.visible is True and "Backend offline" in header
    assert thread_id == "thread-1"  # the URL keeps it, so a reload reopens it once the backend is back


def test_deleting_clears_the_conversation(fake):
    client = fake(threads=[])

    messages, thread_id, turns, *_ = conversations.delete_thread("thread-1")

    assert ("delete_thread", "thread-1") in client.calls
    assert messages == [] and thread_id is None and turns == []


def test_cancelling_the_delete_does_nothing(fake):
    client = fake()
    conversations.delete_thread(None)  # the browser's confirm returned null
    assert client.calls == []


def test_the_chat_sanitises_html_from_the_backend():
    # The presenters emit Markdown only and rely on this for agent and document text.
    assert app.chat.sanitize_html is True
