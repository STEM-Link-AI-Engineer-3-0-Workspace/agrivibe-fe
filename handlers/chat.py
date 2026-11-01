"""Asking and answering: the two events behind every question.

`ask` shows the question at once, with a pending thought, without the queue. Its `.success`
then runs `answer`, which waits for the backend (up to two minutes) and fills the page.
"""

import json
import logging

import gradio as gr

import settings
from api import client
from api.client import BackendUnavailable, ConversationNotFound
from api.models import Turn
from handlers.conversations import header_for, thread_list
from presenters import messages

# One JSON line per chat turn, so a turn can be found and read in the terminal.
logger = logging.getLogger("agrivibe.ui")
logger.setLevel(logging.INFO)


def log_turn(**fields) -> None:
    """Writes one chat turn to the log as a single JSON line."""
    logger.info(json.dumps({"event": "chat_turn", "farmer_id": settings.FARMER_ID, **fields}))


def ask(text: str, turns: list[Turn]):
    """Shows the question at once, with a pending thought, before the slow backend call starts."""
    question = text.strip()
    if not question:
        raise gr.Error("Type a question first.", duration=3)
    return "", messages.chat_messages(turns, pending=question), question


def suggest(turns: list[Turn], event: gr.SelectData):
    """A suggestion was clicked: ask it as if typed."""
    return ask(event.value["text"], turns)


def answer(question: str, thread_id: str | None, turns: list[Turn]):
    """Sends the question to POST /chat and fills the chat, the header and the sidebar."""
    try:
        reply = client.agrivibe.chat(question, thread_id)
    except ConversationNotFound as error:
        log_turn(thread_id=thread_id, status="not_found")
        return messages.chat_messages([], failed=(question, str(error))), None, [], header_for([]), thread_list(None)
    except BackendUnavailable as error:
        log_turn(thread_id=thread_id, status="error", error=repr(error.__cause__))
        return messages.chat_messages(turns, failed=(question, str(error))), thread_id, turns, gr.skip(), gr.skip()

    log_turn(
        thread_id=reply.thread_id,
        status="ok",
        seconds=reply.seconds,
        field_id=reply.field_id,
        tools_called=reply.tools_called,
        specialists={name: "ok" if finding.ok else "no_data" for name, finding in reply.findings.items()},
    )
    turns = turns + [reply]
    return messages.chat_messages(turns), reply.thread_id, turns, header_for(turns), thread_list(reply.thread_id)
