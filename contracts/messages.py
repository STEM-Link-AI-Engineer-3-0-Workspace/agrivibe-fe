"""Turns as gr.Chatbot messages: the question, how AgriVibe worked it out, its answer and sources.

Everything here is Markdown, never HTML. gr.Chatbot sanitises any HTML inside a message
(sanitize_html=True, its default), so text from the backend can be shown as it is.
"""

from api.models import Turn
from contracts.evidence import FINDING_OF, FINDING_TITLES, STEPS, cite, evidence, status


def thought(title: str, content: str = "", **metadata) -> dict:
    """An assistant message that gr.Chatbot shows as a collapsible "thought" instead of a reply."""
    return {"role": "assistant", "content": content, "metadata": {"title": title, **metadata}}


def trace(turn: Turn, n: int) -> list[dict]:
    """The tools the orchestrator called, in order: one thought, with a nested thought per step."""
    if not turn.tools_called:
        return []
    agents = sum(1 for name in turn.tools_called if name in FINDING_OF or name == "ask_advisory_agent")
    missing = [FINDING_TITLES.get(name, name) for name, finding in turn.findings.items() if not finding.ok]
    parent = f"turn-{n}"
    title = f"Worked with {agents} agent{'s' if agents != 1 else ''}" if agents else "Checked your fields"
    log = f"No data from {', '.join(missing)}" if missing else ""
    steps = [thought(title, id=parent, status="done", duration=round(turn.seconds), log=log)]
    for k, name in enumerate(turn.tools_called):
        step = {"id": f"{parent}-{k}", "parent_id": parent, "status": "done"}
        finding = turn.findings.get(FINDING_OF.get(name, ""))
        if finding is not None:
            steps.append(thought(STEPS[name], evidence(finding, turn.sources), log=status(finding), **step))
        elif name == "save_requirements" and turn.requirements:
            parts = [turn.requirements.get(key) for key in ("field_id", "crop", "problem", "timeframe")]
            steps.append(thought(STEPS[name], " · ".join(part for part in parts if part), **step))
        elif name == "ask_advisory_agent":
            steps.append(thought(STEPS[name], "Weighed the evidence into the answer below.", **step))
        else:
            steps.append(thought(STEPS.get(name, name), **step))
    return steps


def source_list(turn: Turn) -> list[dict]:
    """The document passages the answer cites, as one closed thought after it."""
    if not turn.sources:
        return []
    lines = []
    for number, source in enumerate(turn.sources, 1):
        score = f" · relevance {source.rerank_score:.2f}" if source.rerank_score is not None else ""
        text = " ".join(source.text.split())  # one line, so it stays inside its quote
        quote = text if len(text) <= 220 else text[:220].rsplit(" ", 1)[0] + "…"
        lines.append(f"{number}. **{source.source}**, page {source.page}{score}\n\n   > {quote}")
    title = f"Used {len(turn.sources)} source{'s' if len(turn.sources) != 1 else ''}"
    return [thought(title, "\n\n".join(lines), status="done")]


def turn_messages(turn: Turn, n: int) -> list[dict]:
    """One turn: the farmer's question, how AgriVibe worked it out, its answer, and its sources."""
    answer = {"role": "assistant", "content": cite(turn.answer, turn.sources)}
    return [{"role": "user", "content": turn.message}, *trace(turn, n), answer, *source_list(turn)]


def chat_messages(turns: list[Turn], *, pending: str | None = None, failed: tuple[str, str] | None = None) -> list[dict]:
    """The conversation for gr.Chatbot, plus a question still being answered or one that failed."""
    messages = [message for n, turn in enumerate(turns) for message in turn_messages(turn, n)]
    if failed:
        question, error = failed
        messages += [{"role": "user", "content": question}, {"role": "assistant", "content": f"⚠️ **No answer this time.** {error}"}]
    if pending:
        messages += [
            {"role": "user", "content": pending},
            thought("Asking the agents", "The orchestrator is choosing which specialists to ask.", status="pending"),
        ]
    return messages
