import json

import httpx
import pytest

from client import AgriVibeClient, BackendUnavailable, ConversationNotFound

TURN = {
    "message": "Is my Minneriya field stressed?",
    "answer": "Your field is less green than two weeks ago.",
    "tools_called": ["list_fields", "save_requirements", "ask_farm_context_agent", "ask_weather_agent"],
    "requirements": {"field_id": "SL-PADDY-MINNERIYA", "crop": "paddy", "problem": "stress", "timeframe": "now"},
    "findings": {
        "farm_context": {"summary": "NDVI fell 15.2%.", "data": {"ndvi_change_percentage": -15.2}, "sources": []},
        "weather": {"summary": "Weather data is unavailable.", "data": {}, "sources": []},
        "knowledge": {
            "summary": "Top dressing is due at two weeks. [cg-06-1]",
            "data": {"found": True, "citations": ["cg-06-1"]},
            "sources": [{
                "id": "cg-06-1", "source": "CG-06.pdf", "page": 3, "category": "cultivation_guide",
                "text": "First top dressing two weeks after establishment.", "rerank_score": 0.99,
            }],
        },
    },
    "started_at": "2026-11-01T10:00:00Z",
    "seconds": 23.6,
    "a_field_added_later": "ignored",
}
SUMMARY = {"thread_id": "thread-1", "title": "Is my Minneriya field stressed?", "turns": 1,
           "created_at": "2026-11-01T10:00:00Z", "updated_at": "2026-11-01T10:00:24Z"}


def client_answering(handler) -> AgriVibeClient:
    return AgriVibeClient("http://agrivibe.test", transport=httpx.MockTransport(handler))


def test_chat_never_sends_who_the_farmer_is():
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["path"], sent["body"] = request.url.path, json.loads(request.read())
        return httpx.Response(200, json={**TURN, "thread_id": "thread-1"})

    reply = client_answering(handler).chat("Is my Minneriya field stressed?")

    assert sent == {"path": "/chat", "body": {"message": "Is my Minneriya field stressed?", "thread_id": None}}
    assert reply.thread_id == "thread-1" and reply.seconds == 23.6
    assert reply.findings["farm_context"].ok
    assert not reply.findings["weather"].ok  # empty data means the specialist failed
    assert reply.findings["knowledge"].sources[0].source == "CG-06.pdf"


def test_threads_are_listed_read_and_deleted():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.url.path == "/threads":
            return httpx.Response(200, json=[SUMMARY])
        return httpx.Response(200, json={**SUMMARY, "history": [TURN]})

    client = client_answering(handler)
    [summary] = client.list_threads()
    thread = client.get_thread("thread-1")
    client.delete_thread("thread-1")

    assert summary.title == "Is my Minneriya field stressed?"
    assert thread.history[0].findings["knowledge"].sources[0].page == 3
    assert calls == [("GET", "/threads"), ("GET", "/threads/thread-1"), ("DELETE", "/threads/thread-1")]


def test_a_missing_conversation_has_its_own_error():
    client = client_answering(lambda request: httpx.Response(404, json={"detail": "Conversation not found."}))
    with pytest.raises(ConversationNotFound):
        client.chat("Hi", "deleted-thread")
    with pytest.raises(ConversationNotFound):
        client.get_thread("deleted-thread")


@pytest.mark.parametrize(
    ("handler", "expected"),
    [
        (lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("slow", request=request)), "took too long"),
        (lambda request: (_ for _ in ()).throw(httpx.ConnectError("refused", request=request)), "not reachable"),
        (lambda request: httpx.Response(500, text="Internal Server Error"), "HTTP 500"),
        (lambda request: httpx.Response(422, json={"detail": []}), "2000 characters"),
        (lambda request: httpx.Response(200, text="<html>not json</html>"), "could not read"),
        (lambda request: httpx.Response(200, json={"answer": "no thread id"}), "could not read"),
    ],
    ids=["timeout", "down", "server-error", "too-long", "not-json", "wrong-shape"],
)
def test_every_failure_becomes_a_message_for_the_farmer(handler, expected):
    with pytest.raises(BackendUnavailable, match=expected):
        client_answering(handler).chat("Is my field stressed?")


def test_is_up_reads_the_health_check():
    assert client_answering(lambda request: httpx.Response(200, json={"status": "ok"})).is_up()
    assert not client_answering(lambda request: httpx.Response(503, text="down")).is_up()
