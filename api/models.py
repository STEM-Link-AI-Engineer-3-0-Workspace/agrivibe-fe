"""The backend's contract, as the UI reads it.

The UI never imports the backend's code. These models copy only the parts of the backend's
contract (src/agrivibe/models/ in agrivibe-be) that the UI reads. A field the backend adds
later is ignored, so a backend change does not break the page.

Facts about the data live here as properties (`finding.ok`, `turn.sources`); how they read on
the page is up to the presenters.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Source(BaseModel):
    """A passage the knowledge agent cites."""

    id: str
    source: str
    page: int
    text: str
    rerank_score: float | None = None


class Finding(BaseModel):
    """What one specialist reported for a message."""

    summary: str
    data: dict[str, Any]
    sources: list[Source] = []

    @property
    def ok(self) -> bool:
        """False when the specialist or its tool failed: the backend then sends empty data."""
        return bool(self.data)

    @property
    def covered(self) -> bool:
        """False when the knowledge agent searched the guides and found nothing on the question."""
        return self.data.get("found", True)


class Turn(BaseModel):
    """One message from the farmer and everything AgriVibe did to answer it."""

    message: str
    answer: str
    tools_called: list[str]
    requirements: dict[str, str] | None = None
    findings: dict[str, Finding] = {}
    seconds: float = 0.0

    @property
    def field_id(self) -> str | None:
        """The field this turn saved in memory, if it saved one."""
        return (self.requirements or {}).get("field_id")

    @property
    def sources(self) -> list[Source]:
        """Every passage the turn's specialists cited, in order. The page numbers them from 1."""
        return [source for finding in self.findings.values() for source in finding.sources]


class ChatReply(Turn):
    """POST /chat's response: the turn, and the conversation it belongs to."""

    thread_id: str


class ThreadSummary(BaseModel):
    """One of the farmer's conversations, as the list shows it."""

    thread_id: str
    title: str
    updated_at: datetime
    turns: int


class Thread(ThreadSummary):
    """A whole conversation, oldest turn first."""

    history: list[Turn]
