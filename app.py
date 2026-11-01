"""AgriVibe's Gradio frontend: the page, and which handler runs for each event.

It runs as its own process and only talks to the backend over HTTP. Start FieldSat and the
backend first (see README.md), then, in this repo:
    uv run python app.py        ->  http://127.0.0.1:7860
    uv run gradio app.py        ->  the same, reloading on every save while you edit

    settings.py    .env values and the suggestions
    api/           the backend's contract (models) and the HTTP client
    handlers/      what each event does
    presenters/    backend data → what each component shows
    theme/         the theme, the CSS and the avatar
"""

import logging

import gradio as gr

import settings
from handlers import chat as chat_handlers
from handlers import conversations
from presenters import page
from theme.theme import AVATAR, LAUNCH

logging.basicConfig(format="%(levelname)s:     %(name)s: %(message)s")

with gr.Blocks(title="AgriVibe", fill_height=True) as demo:
    thread_id = gr.BrowserState(None, storage_key="agrivibe-thread")  # survives a refresh
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

    demo.load(conversations.on_load, inputs=thread_id, outputs=[alert, *conversation])
    box.submit(chat_handlers.ask, [box, turns], [box, chat, question], queue=False).success(**answer_event)
    chat.example_select(chat_handlers.suggest, turns, [box, chat, question], queue=False).success(**answer_event)
    new.click(conversations.fresh, outputs=conversation, queue=False)
    chat.clear(conversations.fresh, outputs=conversation, queue=False)  # the chat's trash button: start fresh
    threads.input(conversations.open_thread, threads, conversation)
    delete.click(
        conversations.delete_thread,
        thread_id,
        conversation,
        js="(id) => (id && confirm('Delete this conversation and its evidence?')) ? id : null",
    )


if __name__ == "__main__":
    demo.launch(**LAUNCH)  # reload mode (`uv run gradio app.py`) runs this too, so the theme applies in both
