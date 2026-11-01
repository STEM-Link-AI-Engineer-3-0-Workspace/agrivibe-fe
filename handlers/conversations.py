"""The conversation list: opening the page, opening, starting and deleting conversations.

Every handler that changes the open conversation returns the same five values, in the order of
`conversation` in app.py: the chat, the thread id, the turns, the header and the sidebar list.
"""

import gradio as gr

import settings
from api import client
from api.client import BackendUnavailable, ConversationNotFound
from api.models import Turn
from presenters import messages, page


def header_for(turns: list[Turn], online: bool | None = True) -> str:
    """The line above the chat: the first question, and the field last saved in memory."""
    field = next((turn.field_id for turn in reversed(turns) if turn.field_id), None)
    return page.header(turns[0].message if turns else None, field, online)


def thread_list(selected: str | None):
    """The sidebar's conversations, freshly loaded, with one selected. Unchanged if the backend is down."""
    try:
        return gr.Radio(choices=page.thread_choices(client.agrivibe.list_threads()), value=selected)
    except BackendUnavailable:
        return gr.skip()


def opened(thread_id: str):
    """One saved conversation, loaded from the backend."""
    thread = client.agrivibe.get_thread(thread_id)
    return messages.chat_messages(thread.history), thread_id, thread.history, header_for(thread.history), thread_list(thread_id)


def fresh():
    """A new, empty conversation. The backend still remembers the farmer's field from earlier ones."""
    return [], None, [], header_for([]), thread_list(None)


def on_load(saved_thread_id: str | None):
    """Fills the page when it opens, reopening the conversation that was open before a refresh.

    Returns the offline alert first, then the five conversation values.
    """
    if not client.agrivibe.is_up():
        offline = gr.Markdown(page.offline_alert(settings.API), visible=True)
        # Keep the saved thread_id: once the backend is back, a reload reopens the conversation.
        return offline, [], gr.skip(), [], header_for([], online=False), gr.skip()
    if saved_thread_id:
        try:
            return gr.Markdown(visible=False), *opened(saved_thread_id)
        except BackendUnavailable:  # deleted elsewhere, or gone: start fresh
            pass
    return gr.Markdown(visible=False), *fresh()


def open_thread(thread_id: str | None):
    """Opens the conversation picked in the sidebar."""
    if not thread_id:
        return (gr.skip(),) * 5
    try:
        return opened(thread_id)
    except BackendUnavailable as error:
        gr.Warning(str(error))
        return fresh()


def delete_thread(thread_id: str | None):
    """Deletes the open conversation, after the browser asked the farmer to confirm."""
    if not thread_id:
        return (gr.skip(),) * 5
    try:
        client.agrivibe.delete_thread(thread_id)
    except ConversationNotFound:
        pass  # already gone
    except BackendUnavailable as error:
        gr.Warning(str(error))
        return (gr.skip(),) * 5
    gr.Info("Conversation deleted.")
    return fresh()
