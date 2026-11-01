"""AgriVibe's Gradio frontend. It runs as its own process and only talks to the backend over HTTP.

Start FieldSat and the backend first (see README.md), then, in this repo:
    uv run python app.py        ->  http://127.0.0.1:7860
    uv run gradio app.py        ->  the same, reloading on every save while you edit
"""

import json
import logging
import os

import gradio as gr
from dotenv import load_dotenv

import ui
import view
from client import TIMEOUT_SECONDS, AgriVibeClient, BackendUnavailable, ConversationNotFound, Turn

load_dotenv()  # .env in this folder; variables already set in the environment win
API = os.getenv("AGRIVIBE_API", "http://127.0.0.1:8000")
TIMEOUT = float(os.getenv("AGRIVIBE_TIMEOUT", TIMEOUT_SECONDS))
# Who the backend acts for. The backend decides this from its own .env; this copy, kept in sync by
# hand, is only for the page and the log. It is never sent: the backend would not accept it anyway.
FARMER_ID = os.getenv("FARMER_ID", "frm_7f3a9c2e")
FARMER_NAME = os.getenv("FARMER_NAME", "Nimal Perera")

# One JSON line per chat turn, so a turn can be found and read in the terminal.
logging.basicConfig(format="%(levelname)s:     %(name)s: %(message)s")
logger = logging.getLogger("agrivibe.ui")
logger.setLevel(logging.INFO)

client = AgriVibeClient(API, timeout=TIMEOUT)

# (question, what it shows) for the empty conversation. The last three fail or stall on purpose.
SUGGESTIONS = [
    ("Is my Minneriya paddy field stressed?", "Satellite and weather"),
    ("Should I spray fungicide on my Minneriya field this week?", "All four agents, up to two minutes"),
    ("What is the urea rate for Bg 352?", "The Department of Agriculture's guides"),
    ("Is field SL-PADDY-SAT-FAIL stressed?", "The satellite fails on purpose"),
    ("Has it rained much on field SL-PADDY-WEATHER-FAIL?", "The weather service fails on purpose"),
    ("Should I apply urea on field SL-PADDY-SLOW this week?", "Works, about 20 seconds slower"),
]
EMPTY_STATE = view.empty_state(FARMER_NAME, SUGGESTIONS)


def log_turn(**fields) -> None:
    """Writes one chat turn to the log as a single JSON line."""
    logger.info(json.dumps({"event": "chat_turn", "farmer_id": FARMER_ID, **fields}))


def page(turns: list[Turn], **extra) -> str:
    """The conversation as the page shows it, or the greeting when it is empty."""
    return view.conversation(turns, **extra) or EMPTY_STATE


def header(turns: list[Turn], online: bool | None = True) -> str:
    """The bar above the chat, for a conversation: its first question, and the field last saved in memory."""
    field = next((turn.requirements.get("field_id") for turn in reversed(turns) if turn.requirements), None)
    return view.chat_header(turns[0].message if turns else None, field, online)


def history(active: str | None):
    """The sidebar's conversations, freshly loaded, with the open one highlighted. Unchanged if the backend is down."""
    try:
        return view.thread_list(client.list_threads(), active)
    except BackendUnavailable:
        return gr.skip()


def opened(thread_id: str):
    """Loads one conversation: the page, its id, its turns, the header and the sidebar."""
    thread = client.get_thread(thread_id)
    return page(thread.history), thread_id, thread.history, header(thread.history), history(thread_id)


# What a new, empty conversation looks like, in the same order as `opened` returns.
def fresh():
    return EMPTY_STATE, None, [], header([]), history(None)


def on_load(saved_thread_id: str | None):
    """Fills the page when it opens, reopening the conversation that was open before a refresh."""
    if not client.is_up():
        offline = gr.HTML(view.offline_alert(API), visible=True)
        # Keep the saved thread_id: once the backend is back, a reload reopens the conversation.
        return offline, EMPTY_STATE, gr.skip(), [], header([], online=False), gr.skip()
    if saved_thread_id:
        try:
            return gr.HTML(visible=False), *opened(saved_thread_id)
        except BackendUnavailable:  # deleted elsewhere, or gone: start fresh
            pass
    return gr.HTML(visible=False), *fresh()


def ask(turns: list[Turn], event: gr.EventData):
    """Shows the farmer's question at once, with a thinking message, before the slow backend call starts."""
    question = str(getattr(event, "text", "")).strip()
    if not question:
        raise gr.Error("Type a question first.", duration=3)
    return page(turns, pending=question), question


def answer(question: str, thread_id: str | None, turns: list[Turn]):
    """Sends the question to POST /chat and fills the page, the header and the sidebar."""
    try:
        reply = client.chat(question, thread_id)
    except ConversationNotFound as error:
        log_turn(thread_id=thread_id, status="not_found")
        return page([], failed=(question, str(error))), None, [], header([]), history(None)
    except BackendUnavailable as error:
        log_turn(thread_id=thread_id, status="error", error=repr(error.__cause__))
        return page(turns, failed=(question, str(error))), thread_id, turns, gr.skip(), gr.skip()

    log_turn(
        thread_id=reply.thread_id,
        status="ok",
        seconds=reply.seconds,
        field_id=(reply.requirements or {}).get("field_id"),
        tools_called=reply.tools_called,
        specialists={name: "ok" if finding.ok else "no_data" for name, finding in reply.findings.items()},
    )
    turns = turns + [reply]
    return page(turns), reply.thread_id, turns, header(turns), history(reply.thread_id)


def open_thread(event: gr.EventData):
    """Opens the conversation picked in the sidebar."""
    try:
        return opened(event.id)
    except BackendUnavailable as error:
        gr.Warning(str(error))
        return fresh()


def delete_thread(thread_id: str | None, event: gr.EventData):
    """Deletes a conversation from the sidebar, after the browser asked the farmer to confirm."""
    target = event.id
    try:
        client.delete_thread(target)
    except ConversationNotFound:
        pass  # already gone
    except BackendUnavailable as error:
        gr.Warning(str(error))
        return (gr.skip(),) * 5
    if target == thread_id:  # the open one: start fresh
        return fresh()
    return gr.skip(), gr.skip(), gr.skip(), gr.skip(), history(thread_id)


with gr.Blocks(title="AgriVibe", fill_width=True) as demo:
    # Kept in the browser, so a refresh reopens the same conversation.
    thread_id = gr.BrowserState(None, storage_key="agrivibe-thread")
    turns = gr.State([])  # the open conversation's turns
    question = gr.State("")  # the question being answered

    with gr.Sidebar(width=272, elem_classes="app-sidebar"):
        gr.HTML(view.sidebar_brand(), elem_classes="app-brand", apply_default_css=False)
        new = ui.Button("New chat", icon_name="square-pen", variant="outline", size="sm", elem_classes="app-new")
        threads = ui.ThreadList(elem_classes="app-history")
        gr.HTML(view.user_nav(FARMER_NAME, FARMER_ID), elem_classes="app-user", apply_default_css=False)

    top = gr.HTML(view.chat_header(None, None, None), elem_classes="app-header", apply_default_css=False)
    alert = gr.HTML(visible=False, elem_classes="app-alert", apply_default_css=False)
    chat = ui.Conversation(EMPTY_STATE, elem_classes="app-conversation")
    composer = ui.Composer(
        placeholder="Ask about your paddy field…",
        hint_html=view.composer_hint(),
        disclaimer="AgriVibe can make mistakes. Check important decisions with your agricultural instructor.",
        elem_classes="app-composer",
    )

    conversation = [chat, thread_id, turns, top, threads]
    answer_event = {
        "fn": answer,
        "inputs": [question, thread_id, turns],
        "outputs": conversation,
        "concurrency_limit": 10,  # Gradio's default is 1: a second tab would wait for the first one's answer
        "show_progress": "hidden",  # the thinking message is the progress; Gradio's overlay would hide it
    }
    quiet = {"show_progress": "hidden"}

    demo.load(on_load, inputs=thread_id, outputs=[alert, *conversation], **quiet)
    composer.send(ask, turns, [chat, question], queue=False, **quiet).success(**answer_event)
    chat.suggest(ask, turns, [chat, question], queue=False, **quiet).success(**answer_event)
    new.click(fresh, outputs=conversation, **quiet)
    threads.open(open_thread, outputs=conversation, **quiet)
    threads.remove(delete_thread, thread_id, conversation, **quiet)


if __name__ == "__main__":
    demo.launch(**ui.LAUNCH)  # reload mode (`uv run gradio app.py`) runs this too, so the theme applies in both
