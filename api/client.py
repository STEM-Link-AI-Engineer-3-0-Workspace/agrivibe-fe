"""The HTTP calls to the AgriVibe backend, with every failure turned into one readable error.

The UI never tells the backend who the farmer is: the backend decides that on the server.
"""

from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError

import settings
from api.models import ChatReply, Thread, ThreadSummary

# A multi-agent turn usually takes 15 to 45 seconds, but a decision question has taken two minutes.
TIMEOUT_SECONDS = 180.0

UNREADABLE = "AgriVibe sent a reply the app could not read."


class BackendUnavailable(Exception):
    """The UI got no usable answer. The message is written for the farmer and safe to show."""


class ConversationNotFound(BackendUnavailable):
    """The conversation no longer exists, for example because it was deleted in another tab."""


class AgriVibeClient:
    """Calls the AgriVibe backend over HTTP."""

    def __init__(self, base_url: str, timeout: float = TIMEOUT_SECONDS, transport: httpx.BaseTransport | None = None):
        """Initializes the client.

        Args:
            base_url: Where the backend runs, for example http://127.0.0.1:8000.
            timeout: Seconds to wait for one call. A chat turn is the slowest.
            transport: Tests pass an httpx.MockTransport here instead of a real network.
        """
        self.http = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def is_up(self) -> bool:
        """Returns True when GET /health answers {"status": "ok"}."""
        try:
            return self.http.get("/health", timeout=5).json().get("status") == "ok"
        except (httpx.HTTPError, ValueError):
            return False

    def chat(self, message: str, thread_id: str | None = None) -> ChatReply:
        """Sends one message to the orchestrator. None starts a new conversation."""
        return read(ChatReply, self._call("POST", "/chat", json={"message": message, "thread_id": thread_id}))

    def list_threads(self) -> list[ThreadSummary]:
        """The farmer's conversations, the most recently used first."""
        return read(list[ThreadSummary], self._call("GET", "/threads"))

    def get_thread(self, thread_id: str) -> Thread:
        """One conversation with every turn and its evidence."""
        return read(Thread, self._call("GET", f"/threads/{thread_id}"))

    def delete_thread(self, thread_id: str) -> None:
        """Deletes one conversation."""
        self._call("DELETE", f"/threads/{thread_id}")

    def _call(self, method: str, path: str, **kwargs) -> Any:
        """Makes one request and returns its JSON body, or None for an empty one.

        Raises:
            ConversationNotFound: The backend answered 404.
            BackendUnavailable: The backend was down, too slow, failed or sent something unreadable.
        """
        try:
            response = self.http.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.TimeoutException as error:
            raise BackendUnavailable("AgriVibe took too long to answer. Try again in a moment.") from error
        except httpx.ConnectError as error:
            raise BackendUnavailable("AgriVibe's advisory service is not reachable right now.") from error
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status == 404:
                raise ConversationNotFound("That conversation no longer exists. Start a new one.") from error
            if status == 422:
                raise BackendUnavailable("That message could not be sent. Keep it under 2000 characters.") from error
            raise BackendUnavailable(
                f"AgriVibe's advisory service had a problem (HTTP {status}). Try again in a moment."
            ) from error
        except httpx.HTTPError as error:
            raise BackendUnavailable("AgriVibe's advisory service did not respond properly. Try again.") from error
        except ValueError as error:  # not JSON
            raise BackendUnavailable(UNREADABLE) from error


def read(shape: Any, data: Any) -> Any:
    """Parses a response body into the UI's models.

    Raises:
        BackendUnavailable: The body is not in the shape the UI expects.
    """
    try:
        return TypeAdapter(shape).validate_python(data)
    except ValidationError as error:
        raise BackendUnavailable(UNREADABLE) from error


# The one client the page uses. Handlers look it up as `client.agrivibe` when they run, so tests
# can swap it for a fake.
agrivibe = AgriVibeClient(settings.API, timeout=settings.TIMEOUT)
