"""HarchOS SDK streaming support with async generators.

Provides Server-Sent Events (SSE) parsing and async generator wrappers
for consuming streaming responses from the HarchOS API.
"""

from __future__ import annotations

import contextlib
import json as json_module
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional, Type, TypeVar

import httpx

from ._http import HttpTransport

T = TypeVar("T")

# ---------------------------------------------------------------------------
# SSE Event
# ---------------------------------------------------------------------------

@dataclass
class SSEEvent:
    """A single Server-Sent Event.

    Attributes:
        event: The event type (from the ``event:`` field).
        data: The event data (from the ``data:`` field).
        id: Optional event ID (from the ``id:`` field).
        retry: Optional retry interval in milliseconds (from the ``retry:`` field).
    """

    event: str = "message"
    data: str = ""
    id: Optional[str] = None
    retry: Optional[int] = None

    @property
    def json(self) -> Any:
        """Parse the data field as JSON.

        Returns:
            The parsed JSON object.

        Raises:
            ValueError: If the data is not valid JSON.
        """
        return json_module.loads(self.data)


# ---------------------------------------------------------------------------
# SSE Parser
# ---------------------------------------------------------------------------

class SSEParser:
    """Parse a stream of bytes into SSE events.

    Handles buffering of partial lines and multi-line ``data:`` fields
    per the SSE specification.
    """

    def __init__(self) -> None:
        self._buffer: str = ""
        self._event: str = "message"
        self._data_lines: list[str] = []
        self._last_event_id: Optional[str] = None
        self._retry: Optional[int] = None

    def feed(self, chunk: str) -> list[SSEEvent]:
        """Feed a chunk of text and return any complete events.

        Args:
            chunk: A text chunk from the response stream.

        Returns:
            A list of fully parsed :class:`SSEEvent` objects.
        """
        events: list[SSEEvent] = []
        self._buffer += chunk

        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")

            if line == "":
                # Empty line = dispatch event
                if self._data_lines:
                    data = "\n".join(self._data_lines)
                    event = SSEEvent(
                        event=self._event,
                        data=data,
                        id=self._last_event_id,
                        retry=self._retry,
                    )
                    events.append(event)
                self._event = "message"
                self._data_lines = []
                continue

            if line.startswith(":"):
                # Comment – ignore
                continue

            if ":" in line:
                field, _, value = line.partition(":")
                value = value.lstrip(" ")
            else:
                field = line
                value = ""

            if field == "event":
                self._event = value
            elif field == "data":
                self._data_lines.append(value)
            elif field == "id":
                self._last_event_id = value
            elif field == "retry":
                with contextlib.suppress(ValueError):
                    self._retry = int(value)

        return events

    def close(self) -> list[SSEEvent]:
        """Flush any remaining buffered data as a final event.

        Returns:
            Any remaining events that were not yet dispatched.
        """
        events: list[SSEEvent] = []
        if self._data_lines:
            data = "\n".join(self._data_lines)
            event = SSEEvent(
                event=self._event,
                data=data,
                id=self._last_event_id,
                retry=self._retry,
            )
            events.append(event)
            self._data_lines = []
        return events


# ---------------------------------------------------------------------------
# Async streaming
# ---------------------------------------------------------------------------

async def stream_sse(
    response: httpx.Response,
) -> AsyncIterator[SSEEvent]:
    """Yield SSE events from an httpx streaming response.

    Args:
        response: An httpx response opened in streaming mode.

    Yields:
        :class:`SSEEvent` objects as they arrive.
    """
    parser = SSEParser()
    async for chunk in response.aiter_text():
        events = parser.feed(chunk)
        for event in events:
            yield event
    # Flush any remaining data
    for event in parser.close():
        yield event


async def stream_json(
    response: httpx.Response,
    *,
    model_class: Optional[Type[T]] = None,
) -> AsyncIterator[Any]:
    """Yield parsed JSON objects from an SSE stream.

    Automatically skips ``[DONE]`` sentinel events.

    Args:
        response: An httpx streaming response.
        model_class: Optional Pydantic model to validate each event.

    Yields:
        Parsed JSON objects or validated model instances.
    """
    async for event in stream_sse(response):
        if event.data.strip() == "[DONE]":
            return

        try:
            parsed = event.json
        except (json_module.JSONDecodeError, ValueError):
            continue

        if model_class is not None:
            yield model_class.model_validate(parsed)
        else:
            yield parsed


# ---------------------------------------------------------------------------
# Convenience streaming methods on HttpTransport
# ---------------------------------------------------------------------------

async def async_stream_request(
    transport: HttpTransport,
    method: str,
    path: str,
    *,
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    model_class: Optional[Type[T]] = None,
) -> AsyncIterator[Any]:
    """Open a streaming request and yield parsed events.

    Args:
        transport: The HTTP transport to use.
        method: HTTP method.
        path: URL path.
        json: JSON body.
        params: Query parameters.
        headers: Additional headers.
        model_class: Optional Pydantic model class for validation.

    Yields:
        Parsed streaming events (raw dicts or validated models).
    """
    client = await transport._get_async_client()
    request_headers = transport._build_headers()
    if headers:
        request_headers.update(headers)
    request_headers["Accept"] = "text/event-stream"

    request = client.build_request(
        method=method,
        url=path,
        json=json,
        params=params,
        headers=request_headers,
    )

    response = await client.send(request, stream=True)
    try:
        async for item in stream_json(response, model_class=model_class):
            yield item
    finally:
        await response.aclose()
