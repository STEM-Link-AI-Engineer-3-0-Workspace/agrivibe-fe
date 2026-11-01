"""Turns the backend's replies into what the page shows. Plain functions, no Gradio.

The markup is built from the primitives in ui/ and styled by the components it is shown in.
Every piece of text from the backend (answers, agent summaries, document names, the farmer's own
words) is escaped or rendered as Markdown with raw HTML turned off before it reaches the page.
"""

import re
from datetime import datetime
from html import escape

from markdown_it import MarkdownIt

from client import Finding, Source, ThreadSummary, Turn
from ui.icons import icon
from ui.primitives import alert, attributes, avatar, badge, button, collapsible

# CommonMark with "html": False, so raw HTML in an answer is shown as text, never run.
MARKDOWN = MarkdownIt("commonmark", {"html": False, "breaks": True}).enable("table")

# The orchestrator's tools: what the farmer sees for each, and its icon.
STEPS = {
    "list_fields": ("Looked up your registered fields", "list"),
    "save_requirements": ("Saved what you need to memory", "bookmark"),
    "ask_weather_agent": ("Weather agent", "cloud-rain"),
    "ask_farm_context_agent": ("Farm context agent", "satellite"),
    "ask_knowledge_agent": ("Knowledge agent", "book-open"),
    "ask_advisory_agent": ("Advisory agent", "scale"),
}
# Which finding each specialist leaves behind. Advisory leaves none: its work is the answer.
FINDING_OF = {"ask_weather_agent": "weather", "ask_farm_context_agent": "farm_context", "ask_knowledge_agent": "knowledge"}
FINDING_TITLES = {"weather": "Weather", "farm_context": "Farm context", "knowledge": "Knowledge"}

# A citation the knowledge agent leaves in its text: [cg-06-fertiliser-…-5] or [cg-06-…-5, cg-07-…-2].
CITATION = re.compile(r"\s*\[([a-z]+-\d+[\w-]*(?:,\s*[a-z]+-\d+[\w-]*)*)\]")

# Data keys that are shown elsewhere (the sources list) or say nothing to a farmer.
HIDDEN_KEYS = {"field_id", "citations", "found"}


def markdown(text: str) -> str:
    """An agent's Markdown as HTML. Raw HTML in it is escaped."""
    return MARKDOWN.render(text)


def guide(identifier: str) -> str:
    """The guide a passage or file belongs to: 'cg-06-fertiliser-…-5' and 'CG-06_fertiliser….pdf' → 'cg-06'."""
    return "-".join(re.split(r"[-_]", identifier.lower())[:2])


def cited(findings: dict[str, Finding]) -> list[Source]:
    """Every document passage the turn's specialists cited, in order. Their numbers start at 1."""
    return [source for finding in findings.values() for source in finding.sources]


def cite(html: str, sources: list[Source]) -> str:
    """Replaces citation ids in rendered text with small chips: the source's number when it is in the
    sources list, otherwise the guide's code (CG-06), with the full id on hover.
    """
    numbers: dict[str, int] = {}
    for number, source in enumerate(sources, 1):
        numbers.setdefault(source.id, number)
        numbers.setdefault(guide(source.source), number)

    def chips(match: re.Match) -> str:
        labels: dict[str, str] = {}  # chip text → its tooltip, in order, without repeats
        for citation in re.split(r",\s*", match.group(1)):
            number = numbers.get(citation) or numbers.get(guide(citation))
            if number:
                source = sources[number - 1]
                labels.setdefault(str(number), f"{source.source} · p. {source.page}")
            else:
                labels.setdefault(guide(citation).upper(), citation)
        return "".join(f'<span class="citation" title="{escape(title)}">{escape(label)}</span>' for label, title in labels.items())

    return CITATION.sub(chips, html)


def initials(name: str) -> str:
    """'Nimal Perera' → 'NP'."""
    return "".join(part[0] for part in name.split()[:2]).upper() or "?"


def metric(key: str, value) -> tuple[str, str]:
    """A data key and value, readable: rainfall_last_7_days_mm, 112.0 → 'Rainfall last 7 days', '112 mm'."""
    unit = ""
    if key.endswith("_mm"):
        key, unit = key[:-3], " mm"
    elif key.endswith("_percentage"):
        key, unit = key[: -len("_percentage")], "%"
    label = re.sub(r"\bndvi\b", "NDVI", key.replace("_", " ").capitalize(), flags=re.IGNORECASE)
    if isinstance(value, bool):
        text = "Yes" if value else "No"
    elif isinstance(value, float):
        text = f"{value:g}{unit}"
    else:
        text = f"{value}{unit}".replace("_", " ")
    return label, text


# The page shell


def sidebar_brand() -> str:
    """The logo and name at the top of the sidebar."""
    return (
        f'<div class="sidebar-brand">{avatar(icon_name="sprout", variant="primary")}'
        "<span>AgriVibe</span></div>"
    )


def user_nav(name: str, farmer_id: str) -> str:
    """Who the app is acting for, at the foot of the sidebar."""
    return (
        f'<div class="sidebar-user">{avatar(initials=initials(name), shape="circle")}'
        f'<div><b>{escape(name)}</b><code>{escape(farmer_id)}</code></div></div>'
    )


def chat_header(title: str | None, field_id: str | None, online: bool | None) -> str:
    """The bar above the chat: the conversation's title, the field in memory, and the backend's status."""
    heading = f'<h1 title="{escape(title)}">{escape(title)}</h1>' if title else '<h1 class="untitled">New conversation</h1>'
    field = badge(field_id, variant="outline", icon_name="map-pin", title="Field in memory") if field_id else ""
    status = ""
    if online is not None:
        status = f'<span class="status" data-online="{str(online).lower()}"><i></i>{"Online" if online else "Offline"}</span>'
    return f'<header class="header"><div class="header-title">{heading}</div><div class="header-meta">{field}{status}</div></header>'


def offline_alert(api: str) -> str:
    """Shown when the backend cannot be reached."""
    return alert(
        "The AgriVibe backend is not reachable",
        f"Nothing answers at <code>{escape(api)}</code>. Start it, then reload this page.",
        variant="warning",
        icon_name="triangle-alert",
    )


def composer_hint() -> str:
    """The note in the composer's footer: who answers."""
    icons = "".join(icon(name, 14) for name in ("cloud-rain", "satellite", "book-open", "scale"))
    return f"{icons}<span>Four specialist agents</span>"


# The empty conversation


def empty_state(name: str, suggestions: list[tuple[str, str]]) -> str:
    """The greeting, and suggestions that send a question when clicked."""
    first_name = name.split()[0] if name.split() else "there"
    cards = "".join(
        f'<button type="button" class="suggestion"{attributes(data_event="suggest", data_text=question)}>'
        f"{escape(question)}<span>{escape(hint)}</span></button>"
        for question, hint in suggestions
    )
    return (
        '<div class="empty"><div class="greeting">'
        f"<h2>Hello, {escape(first_name)}</h2>"
        "<p>Ask about your paddy field. The agents check satellite data, the weather and the "
        "Department of Agriculture's guides before they answer.</p></div>"
        f'<div class="suggestions">{cards}</div></div>'
    )


# Messages


def user_message(text: str) -> str:
    return f'<div class="message" data-role="user"><div class="bubble">{escape(text)}</div></div>'


def assistant(body_html: str, *, pending: bool = False) -> str:
    """An AgriVibe message: the avatar, then its content."""
    flag = " data-pending" if pending else ""
    return (
        f'<div class="message" data-role="assistant"{flag}>{avatar(icon_name="sprout")}'
        f'<div class="message-body">{body_html}</div></div>'
    )


def thinking_message() -> str:
    """Shown while the backend works on an answer."""
    return assistant('<div class="thinking"><span class="ui-shimmer">Asking the agents…</span></div>', pending=True)


def failed_message(error: str) -> str:
    """Shown when a turn failed: the conversation is kept, so the farmer can ask again."""
    return assistant(alert("No answer this time", escape(error), variant="warning", icon_name="triangle-alert"))


def answer_message(turn: Turn) -> str:
    """AgriVibe's answer: how it worked it out, the answer, the documents it used, and a copy button."""
    copy = (
        f'<button type="button" class="ui-button" data-variant="ghost" data-size="icon-sm"'
        f'{attributes(data_copy=CITATION.sub("", turn.answer), aria_label="Copy", title="Copy")}>'
        f'{icon("copy", 14, "icon-copy")}{icon("check", 14, "icon-check")}</button>'
    )
    answer = cite(markdown(turn.answer), cited(turn.findings))
    body = trace(turn) + f'<div class="prose">{answer}</div>' + sources(turn.findings)
    return assistant(body + f'<div class="actions">{copy}</div>')


def trace(turn: Turn) -> str:
    """The tools the orchestrator called, in order, as a collapsible chain of steps."""
    if not turn.tools_called:
        return ""
    agents = sum(1 for name in turn.tools_called if name in FINDING_OF or name == "ask_advisory_agent")
    label = f"Worked with {agents} agent{'s' if agents != 1 else ''}" if agents else "Checked your fields"
    missing = [FINDING_TITLES.get(name, name) for name, finding in turn.findings.items() if not finding.ok]
    flag = ""
    if len(missing) == 1:
        flag = badge(f"No data from {missing[0]}", variant="warning", icon_name="circle-alert")
    elif missing:
        flag = badge(f"{len(missing)} agents had no data", variant="warning", icon_name="circle-alert")
    head = (
        f'{icon("workflow", 14)}<span>{label}</span>'
        f'<span class="trace-time">· {turn.seconds:.0f}s</span>{flag}'
    )
    steps = "".join(step(name, turn) for name in turn.tools_called)
    return collapsible(head, f'<ol class="steps">{steps}</ol>', cls="trace")


def step(name: str, turn: Turn) -> str:
    """One tool call in the trace: its icon, name, status, and what it found."""
    label, icon_name = STEPS.get(name, (name, "wrench"))
    title = f'<span class="step-tool">{escape(label)}</span>' if name not in STEPS else escape(label)
    status, detail = "", ""
    if name == "save_requirements" and turn.requirements:
        parts = [turn.requirements.get(key) for key in ("field_id", "crop", "problem", "timeframe")]
        detail = f'<div class="step-desc">{escape(" · ".join(part for part in parts if part))}</div>'
    elif name == "ask_advisory_agent":
        detail = '<div class="step-desc">Weighed the evidence into the answer below.</div>'
    elif (finding := turn.findings.get(FINDING_OF.get(name, ""))) is not None:
        status = finding_status(FINDING_OF[name], finding)
        summary = cite(markdown(finding.summary), cited(turn.findings))
        detail = f'<div class="step-desc">{summary}</div>' + metrics(finding)
    return (
        f'<li class="step"><span class="step-icon">{icon(icon_name, 16)}</span><div>'
        f'<div class="step-head">{title}{status}</div>{detail}</div></li>'
    )


def finding_status(name: str, finding: Finding) -> str:
    """A specialist's badge: it found something, it had no data, or the guides do not cover it."""
    if not finding.ok:
        return badge("No data", variant="warning")
    if name == "knowledge" and not finding.data.get("found", True):
        return badge("Not in the guides", variant="outline")
    return badge("Done", variant="success", icon_name="check")


def metrics(finding: Finding) -> str:
    """A specialist's numbers as small labelled chips."""
    items = [
        metric(key, value)
        for key, value in finding.data.items()
        if key not in HIDDEN_KEYS and not isinstance(value, dict | list)
    ]
    if not items:
        return ""
    chips = "".join(f'<div class="metric"><dt>{escape(label)}</dt><dd>{escape(text)}</dd></div>' for label, text in items)
    return f'<dl class="metrics">{chips}</dl>'


def sources(findings: dict[str, Finding]) -> str:
    """The documents the answer cites, collapsed under "Used N sources"."""
    documents = cited(findings)
    if not documents:
        return ""
    items = "".join(
        f'<li class="source" title="{escape(source.id)}"><span class="source-index">{number}</span>'
        f'<span class="source-name">{escape(source.source)} <span class="source-page">· p. {source.page}</span></span>'
        + (f'<span class="source-score" title="Rerank score">{source.rerank_score:.2f}</span>' if source.rerank_score is not None else "<span></span>")
        + (f'<span class="source-quote">{escape(source.text)}</span>' if source.text else "")
        + "</li>"
        for number, source in enumerate(documents, 1)
    )
    head = f'{icon("book-open", 14)}<span>Used {len(documents)} source{"s" if len(documents) != 1 else ""}</span>'
    return collapsible(head, f'<ul class="source-list">{items}</ul>', cls="sources")


def conversation(turns: list[Turn], *, pending: str | None = None, failed: tuple[str, str] | None = None) -> str:
    """The whole conversation, plus a question still waiting for its answer or one that failed.

    Returns "" when there is nothing to show, so the page can show its empty state instead.
    """
    parts = [user_message(turn.message) + answer_message(turn) for turn in turns]
    if failed:
        question, error = failed
        parts.append(user_message(question) + failed_message(error))
    if pending:
        parts.append(user_message(pending) + thinking_message())
    return f'<div class="conversation">{"".join(parts)}</div>' if parts else ""


# The sidebar's history


def day_group(updated: datetime, today: datetime) -> str:
    """Today, Yesterday, Previous 7 days, Previous 30 days, or Older, in the farmer's local time."""
    days = (today.date() - updated.astimezone(today.tzinfo).date()).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days <= 7:
        return "Previous 7 days"
    if days <= 30:
        return "Previous 30 days"
    return "Older"


def thread_list(threads: list[ThreadSummary], active: str | None, now: datetime | None = None) -> str:
    """The conversations, most recent first, grouped by day, with the open one highlighted."""
    if not threads:
        return '<div class="history-empty">Your conversations will appear here once you ask something.</div>'
    today = now or datetime.now().astimezone()
    groups: dict[str, list[str]] = {}
    for thread in threads:
        delete = button(
            "Delete conversation",
            icon_name="trash-2",
            variant="ghost",
            size="icon-sm",
            data_event="remove",
            data_id=thread.thread_id,
            cls="history-action",
            data_confirm=f"Delete “{thread.title}” and its evidence?",
        )
        current = " data-active" if thread.thread_id == active else ""
        groups.setdefault(day_group(thread.updated_at, today), []).append(
            f'<div class="history-item"{current}>'
            f'<button type="button" class="history-link"{attributes(data_event="open", data_id=thread.thread_id, title=thread.title)}>'
            f"{escape(thread.title)}</button>{delete}</div>"
        )
    return '<div class="history">' + "".join(
        f'<div><div class="history-label">{label}</div><div class="history-items">{"".join(items)}</div></div>'
        for label, items in groups.items()
    ) + "</div>"

