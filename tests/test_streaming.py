"""Tests for streaming support."""

from __future__ import annotations

import pytest

from harchos._streaming import SSEEvent, SSEParser


class TestSSEEvent:
    """Tests for SSEEvent dataclass."""

    def test_defaults(self) -> None:
        event = SSEEvent()
        assert event.event == "message"
        assert event.data == ""
        assert event.id is None
        assert event.retry is None

    def test_json_parsing(self) -> None:
        event = SSEEvent(data='{"key": "value", "num": 42}')
        parsed = event.json
        assert parsed["key"] == "value"
        assert parsed["num"] == 42

    def test_json_invalid(self) -> None:
        event = SSEEvent(data="not json")
        with pytest.raises(ValueError):
            event.json


class TestSSEParser:
    """Tests for SSEParser."""

    def test_single_event(self) -> None:
        parser = SSEParser()
        chunk = "data: hello world\n\n"
        events = parser.feed(chunk)
        assert len(events) == 1
        assert events[0].data == "hello world"
        assert events[0].event == "message"

    def test_event_type(self) -> None:
        parser = SSEParser()
        chunk = "event: update\ndata: test\n\n"
        events = parser.feed(chunk)
        assert len(events) == 1
        assert events[0].event == "update"
        assert events[0].data == "test"

    def test_multi_line_data(self) -> None:
        parser = SSEParser()
        chunk = "data: line1\ndata: line2\ndata: line3\n\n"
        events = parser.feed(chunk)
        assert len(events) == 1
        assert events[0].data == "line1\nline2\nline3"

    def test_event_id(self) -> None:
        parser = SSEParser()
        chunk = "id: evt123\ndata: test\n\n"
        events = parser.feed(chunk)
        assert events[0].id == "evt123"

    def test_retry_field(self) -> None:
        parser = SSEParser()
        chunk = "retry: 5000\ndata: test\n\n"
        events = parser.feed(chunk)
        assert events[0].retry == 5000

    def test_comment_ignored(self) -> None:
        parser = SSEParser()
        chunk = ": this is a comment\ndata: test\n\n"
        events = parser.feed(chunk)
        assert len(events) == 1
        assert events[0].data == "test"

    def test_multiple_events(self) -> None:
        parser = SSEParser()
        chunk = "data: first\n\ndata: second\n\n"
        events = parser.feed(chunk)
        assert len(events) == 2
        assert events[0].data == "first"
        assert events[1].data == "second"

    def test_partial_chunk(self) -> None:
        parser = SSEParser()
        # Feed partial data
        events1 = parser.feed("data: hel")
        assert len(events1) == 0  # Not complete yet
        events2 = parser.feed("lo\n\n")
        assert len(events2) == 1
        assert events2[0].data == "hello"

    def test_carriage_return_handling(self) -> None:
        parser = SSEParser()
        chunk = "data: test\r\n\r\n"
        events = parser.feed(chunk)
        assert len(events) == 1
        assert events[0].data == "test"

    def test_close_flushes_remaining(self) -> None:
        parser = SSEParser()
        parser.feed("data: unflushed")
        events = parser.close()
        assert len(events) == 1
        assert events[0].data == "unflushed"

    def test_close_empty(self) -> None:
        parser = SSEParser()
        events = parser.close()
        assert len(events) == 0

    def test_invalid_retry_ignored(self) -> None:
        parser = SSEParser()
        chunk = "retry: notanumber\ndata: test\n\n"
        events = parser.feed(chunk)
        assert events[0].retry is None

    def test_field_with_colon_in_value(self) -> None:
        parser = SSEParser()
        chunk = "data: {\"key\": \"value\"}\n\n"
        events = parser.feed(chunk)
        assert events[0].data == '{"key": "value"}'
