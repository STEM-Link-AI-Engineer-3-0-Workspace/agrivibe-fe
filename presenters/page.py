"""The text around the chat: the header, the greeting, the farmer, the offline alert, the thread list."""

import re

from api.models import ThreadSummary


def header(title: str | None, field_id: str | None, online: bool | None) -> str:
    """The line above the chat: the conversation, the field in memory, and the backend's status."""
    meta = []
    if field_id:
        meta.append(f"Field `{field_id}`")
    if online is not None:
        meta.append("Backend online" if online else "Backend offline")
    heading = f"**{escape_markdown(title)}**" if title else "**New conversation**"
    return heading + ("  \n" + " · ".join(meta) if meta else "")


def greeting(name: str) -> str:
    """What the empty chat shows above the suggestions."""
    first = name.split()[0] if name.split() else "there"
    return (
        f"## Hello, {escape_markdown(first)}\n"
        "Ask about your paddy field. The agents check satellite data, the weather and the "
        "Department of Agriculture's guides before they answer."
    )


def farmer(name: str, farmer_id: str) -> str:
    """Who the app is acting for, in the sidebar."""
    return f"**{escape_markdown(name)}**  \n`{farmer_id}`"


def offline_alert(api: str) -> str:
    return f"⚠️ **The AgriVibe backend is not reachable** at `{api}`. Start it, then reload this page."


def thread_choices(threads: list[ThreadSummary]) -> list[tuple[str, str]]:
    """The conversation list as (title, thread_id) pairs, most recent first."""
    return [(thread.title, thread.thread_id) for thread in threads]


def escape_markdown(text: str) -> str:
    """Text shown inside our own Markdown, with the characters that would format it escaped."""
    return re.sub(r"([\\`*_\[\]#<>])", r"\\\1", text)
