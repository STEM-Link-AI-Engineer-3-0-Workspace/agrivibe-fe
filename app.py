"""AgriVibe's Gradio frontend: the page, and which handler runs for each event.

It runs as its own process and only talks to the backend over HTTP. Start FieldSat and the
backend first (see README.md), then, in this repo:
    uv run python app.py        ->  http://127.0.0.1:7860
    uv run gradio app.py        ->  the same, reloading on every save while you edit

    settings.py    .env values and the suggestions
    api/           the backend's contract (models) and the HTTP client
    handlers/      what each event does
    contracts/     backend data → what each component shows
    theme/         the theme, the CSS and the avatar
"""

import logging

import gradio as gr

import settings
from contracts import page
from handlers import chat as chat_handlers
from handlers import conversations
from theme.theme import AVATAR, LAUNCH

logging.basicConfig(format="%(levelname)s:     %(name)s: %(message)s")


def write_url(method: str) -> str:
    """Browser JS that puts the thread id in the URL (`?thread=<id>`), or takes it out for a new chat.

    `replaceState` runs once, when the page has opened, and marks it opened. `pushState` waits
    for that mark: otherwise opening a deleted thread would push `/` over it, and Back would land
    on the dead link again.
    """
    wait = "if (!window.pageOpened) return;" if method == "pushState" else ""
    return f"""(id) => {{
        {wait}
        window.pageOpened = true;
        const url = new URL(location.href);
        if ((url.searchParams.get("thread") ?? "") === (id ?? "")) return;
        id ? url.searchParams.set("thread", id) : url.searchParams.delete("thread");
        history.{method}(null, "", url);
    }}"""


# Back and Forward change the URL without telling Gradio, so reload: on_load reads the URL again.
RELOAD_ON_BACK = "() => { window.addEventListener('popstate', () => location.reload()); }"

with gr.Blocks(title="AgriVibe", fill_height=True) as demo:
    # The open conversation's id. The URL is its source of truth; this copy is a hidden Textbox,
    # not gr.State, because gr.State never reaches the browser, and the JS below needs to read it.
    thread_id = gr.Textbox(visible=False)
    turns = gr.State([])  # the open conversation's turns
    question = gr.State("")  # the question being answered, kept while the textbox is cleared

    with gr.Sidebar(width=280, elem_classes="app-sidebar"):
        gr.Markdown("### AgriVibe")
        new = gr.Button("New chat", variant="primary", size="sm")
        threads = gr.Radio(label="Conversations", choices=[], container=False, elem_classes="app-threads")
        delete = gr.Button("Delete conversation", variant="stop", size="sm")
        gr.Markdown(page.farmer(settings.FARMER_NAME, settings.FARMER_ID), elem_classes="app-farmer")

    with gr.Column(scale=1, elem_classes="app-main"):  # the chat column, centred at a readable width
        top = gr.Markdown(page.header(None, None, None), elem_classes="app-header")
        alert = gr.Markdown(visible=False, elem_classes="app-alert")
        chat = gr.Chatbot(
            show_label=False,
            placeholder=page.greeting(settings.FARMER_NAME),
            examples=[{"text": suggestion} for suggestion in settings.SUGGESTIONS],
            buttons=["copy"],
            feedback_options=None,
            avatar_images=(None, AVATAR),
            scale=1,  # with fill_height, the chat takes the height the other rows leave
            elem_classes="app-chat",
        )
        box = gr.Textbox(
            placeholder="Ask about your paddy field…",
            show_label=False,
            submit_btn=True,
            max_lines=6,
            elem_classes="app-composer",
        )

    # What every handler that changes the open conversation returns, in this order.
    conversation = [chat, thread_id, turns, top, threads]
    answer_event = {
        "fn": chat_handlers.answer,
        "inputs": [question, thread_id, turns],
        "outputs": conversation,
        "concurrency_limit": 10,  # Gradio's default is 1: a second tab would wait for the first one's answer
        "show_progress": "hidden",  # the pending thought in the chat already shows the progress
    }

    # Gradio's default overlay dims every output with "processing | 0.4s". Opening, starting and
    # deleting a conversation take well under a second, so these events show nothing while they run.
    quiet = {"show_progress": "hidden"}

    # Opening the page settles the URL in place (a deleted thread drops out), adding no history.
    demo.load(conversations.on_load, outputs=[alert, *conversation], **quiet).then(None, thread_id, js=write_url("replaceState"))
    # Every later change of conversation is a new history entry, so Back returns to it.
    thread_id.change(None, thread_id, js=write_url("pushState"))
    box.submit(chat_handlers.ask, [box, turns], [box, chat, question], queue=False).success(**answer_event)
    chat.example_select(chat_handlers.suggest, turns, [box, chat, question], queue=False).success(**answer_event)
    new.click(conversations.fresh, outputs=conversation, queue=False, **quiet)
    threads.input(conversations.open_thread, threads, conversation, **quiet)
    delete.click(
        conversations.delete_thread,
        thread_id,
        conversation,
        js="(id) => (id && confirm('Delete this conversation and its evidence?')) ? id : null",
        **quiet,
    )


if __name__ == "__main__":
    demo.launch(**LAUNCH, js=RELOAD_ON_BACK)  # reload mode (`uv run gradio app.py`) runs this too, so the theme applies in both
