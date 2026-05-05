"""SSE streaming parser for HarchOS API.

Provides Server-Sent Events (SSE) parsing and sync/async streaming
generators for consuming streaming responses from the HarchOS API.
"""

from __future__ import annotations

import json as json_module
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Type, TypeVar

import httpx

from ._exceptions import HarchOSError, make_error

T = TypeVar("T")


@dataclass
class SSEEvent:
    """A single Server-Sent Event.

    Attributes:
        event: Event type (from ``event:`` field).
        data: Event data (from ``data:`` field).
        id: Optional event ID.
        retry: Optional retry interval in ms.
    """

    event: str = "message"
    data: str = ""
    id: Optional[str] = None
    retry: Optional[int] = None

    @property
    def json(self) -> Any:
        """Parse the data field as JSON."""
        return json_module.loads(self.data)


class SSEParser:
    """Parse a stream of text into SSE events.

    Handles buffering of partial lines and multi-line ``data:`` fields
    per the SSE specification.
    """

    def __init__(self) -> None:
        self._buffer: str = ""
        self._event: str = "message"
        self._data_lines: List[str] = []

    def feed(self, chunk: str) -> List[SSEEvent]:
        """Feed a text chunk and return complete events."""
        events: List[SSEEvent] = []
        self._buffer += chunk

        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")

            if line == "":
                # Empty line = dispatch event
                if self._data_lines:
                    data = "\n".join(self._data_lines)
                    events.append(SSEEvent(
                        event=self._event,
                        data=data,
                    ))
                self._event = "message"
                self._data_lines = []
                continue

            if line.startswith(":"):
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
                pass  # Could store last_event_id
            elif field == "retry":
                pass  # Could parse retry interval

        return events

    def flush(self) -> List[SSEEvent]:
        """Flush any remaining buffered data as a final event."""
        events: List[SSEEvent] = []
        if self._data_lines:
            data = "\n".join(self._data_lines)
            events.append(SSEEvent(event=self._event, data=data))
            self._data_lines = []
        return events


def parse_sse_stream(text: str) -> Iterator[SSEEvent]:
    """Parse a complete SSE text stream into events.

    Args:
        text: Complete SSE text (e.g. from a sync response).

    Yields:
        SSEEvent objects.
    """
    parser = SSEParser()
    for event in parser.feed(text):
        yield event
    for event in parser.flush():
        yield event


async def async_parse_sse_stream(response: httpx.Response) -> AsyncIterator[SSEEvent]:
    """Yield SSE events from an httpx async streaming response.

    Args:
        response: An httpx response opened in streaming mode.

    Yields:
        SSEEvent objects as they arrive.
    """
    parser = SSEParser()
    async for chunk in response.aiter_text():
        for event in parser.feed(chunk):
            yield event
    for event in parser.flush():
        yield event


def parse_stream_chunk(data: str, model_class: Optional[Type[T]] = None) -> Optional[Any]:
    """Parse a single SSE data field into a typed object.

    Skips ``[DONE]`` sentinel events and invalid JSON.

    Args:
        data: The SSE ``data`` field content.
        model_class: Optional Pydantic model to validate against.

    Returns:
        Parsed object, or None if the event should be skipped.
    """
    if data.strip() == "[DONE]":
        return None

    try:
        parsed = json_module.loads(data)
    except (json_module.JSONDecodeError, ValueError):
        return None

    if model_class is not None:
        return model_class.model_validate(parsed)
    return parsed


# ---------------------------------------------------------------------------
# Streaming response wrapper for sync iteration
# ---------------------------------------------------------------------------

class StreamIterator:
    """Synchronous iterator over streaming SSE chunks.

    Reads from an httpx streaming response and yields typed chunks.
    """

    def __init__(
        self,
        response: httpx.Response,
        chunk_type: Optional[Type[T]] = None,
    ) -> None:
        self._response = response
        self._chunk_type = chunk_type
        self._parser = SSEParser()
        self._buffer: List[Any] = []
        self._done = False

    def __iter__(self) -> "StreamIterator":
        return self

    def __next__(self) -> Any:
        # Drain buffer first
        if self._buffer:
            return self._buffer.pop(0)

        if self._done:
            raise StopIteration

        # Read next chunk from response
        for raw_line in self._response.iter_lines():
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            events = self._parser.feed(line + "\n")
            for event in events:
                if event.data.strip() == "[DONE]":
                    self._done = True
                    # Flush remaining
                    for remaining in self._parser.flush():
                        chunk = parse_stream_chunk(remaining.data, self._chunk_type)
                        if chunk is not None:
                            self._buffer.append(chunk)
                    if self._buffer:
                        return self._buffer.pop(0)
                    raise StopIteration
                chunk = parse_stream_chunk(event.data, self._chunk_type)
                if chunk is not None:
                    return chunk

        self._done = True
        for remaining in self._parser.flush():
            chunk = parse_stream_chunk(remaining.data, self._chunk_type)
            if chunk is not None:
                self._buffer.append(chunk)
        if self._buffer:
            return self._buffer.pop(0)
        raise StopIteration


class AsyncStreamIterator:
    """Async iterator over streaming SSE chunks.

    Reads from an httpx async streaming response and yields typed chunks.
    """

    def __init__(
        self,
        response: httpx.Response,
        chunk_type: Optional[Type[T]] = None,
    ) -> None:
        self._response = response
        self._chunk_type = chunk_type

    def __aiter__(self) -> "AsyncStreamIterator":
        return self

    async def __anext__(self) -> Any:
        parser = SSEParser()
        async for chunk_text in self._response.aiter_text():
            events = parser.feed(chunk_text)
            for event in events:
                if event.data.strip() == "[DONE]":
                    raise StopAsyncIteration
                parsed = parse_stream_chunk(event.data, self._chunk_type)
                if parsed is not None:
                    return parsed
        # Flush
        for event in parser.flush():
            if event.data.strip() == "[DONE]":
                raise StopAsyncIteration
            parsed = parse_stream_chunk(event.data, self._chunk_type)
            if parsed is not None:
                return parsed
        raise StopAsyncIteration
