"""Inference resource — OpenAI-compatible chat and text completions.

Provides ``harchos.inference.chat.completions.create(...)``,
``harchos.inference.completions.create(...)``, and
``harchos.inference.models.list()`` with built-in carbon tracking
on every response.

Streaming is supported via ``stream=True``:
::

    for chunk in harchos.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[...],
        stream=True,
    ):
        print(chunk.choices[0].delta.content, end="")
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Union

from .._streaming import AsyncStreamIterator, StreamIterator
from .._types import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    ChatMessage,
    CompletionChunk,
    CompletionResponse,
    ModelInfo,
    ModelList,
)


# ---------------------------------------------------------------------------
# Nested resource classes for dot-notation API
# ---------------------------------------------------------------------------

class _ChatCompletions:
    """``harchos.inference.chat.completions`` — OpenAI-compatible chat API."""

    def __init__(self, resource: "InferenceResource") -> None:
        self._resource = resource

    def create(
        self,
        *,
        model: str,
        messages: List[Union[Dict[str, Any], ChatMessage]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletionResponse, Iterator[ChatCompletionChunk]]:
        """Create a chat completion.

        Args:
            model: Model ID (e.g. ``"harchos-llama-3.3-70b"``).
            messages: List of message dicts or :class:`ChatMessage` objects.
            temperature: Sampling temperature (0–2).
            top_p: Nucleus sampling threshold.
            max_tokens: Maximum tokens to generate.
            stream: If True, returns an iterator of streaming chunks.
            stop: Stop sequences.
            frequency_penalty: Frequency penalty (-2–2).
            presence_penalty: Presence penalty (-2–2).
            seed: Deterministic seed.
            **kwargs: Additional parameters passed to the API.

        Returns:
            A :class:`ChatCompletionResponse` or an iterator of
            :class:`ChatCompletionChunk` if ``stream=True``.
        """
        # Normalize messages to dicts
        normalized_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                normalized_messages.append(msg.model_dump(exclude_none=True))
            elif isinstance(msg, dict):
                normalized_messages.append(msg)
            else:
                normalized_messages.append({"role": "user", "content": str(msg)})

        body: Dict[str, Any] = {
            "model": model,
            "messages": normalized_messages,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if stop is not None:
            body["stop"] = stop
        if frequency_penalty is not None:
            body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            body["presence_penalty"] = presence_penalty
        if seed is not None:
            body["seed"] = seed
        body.update(kwargs)

        if stream:
            return self._stream_create(body)

        result = self._resource._client.request(
            "POST", "/inference/chat/completions", json=body,
        )
        return ChatCompletionResponse.model_validate(result)

    def _stream_create(
        self, body: Dict[str, Any]
    ) -> Iterator[ChatCompletionChunk]:
        """Open a streaming chat completion and yield chunks."""
        body["stream"] = True
        response = self._resource._client.stream_request(
            "POST", "/inference/chat/completions", json=body,
        )
        try:
            iterator = StreamIterator(response, chunk_type=ChatCompletionChunk)
            for chunk in iterator:
                yield chunk
        finally:
            response.close()


class _Chat:
    """``harchos.inference.chat`` namespace."""

    def __init__(self, resource: "InferenceResource") -> None:
        self.completions = _ChatCompletions(resource)


class _Completions:
    """``harchos.inference.completions`` — Text completion API."""

    def __init__(self, resource: "InferenceResource") -> None:
        self._resource = resource

    def create(
        self,
        *,
        model: str,
        prompt: Union[str, List[str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Union[CompletionResponse, Iterator[CompletionChunk]]:
        """Create a text completion.

        Args:
            model: Model ID.
            prompt: Text prompt or list of prompts.
            temperature: Sampling temperature (0–2).
            top_p: Nucleus sampling threshold.
            max_tokens: Maximum tokens to generate.
            stream: If True, returns an iterator of streaming chunks.
            stop: Stop sequences.
            frequency_penalty: Frequency penalty (-2–2).
            presence_penalty: Presence penalty (-2–2).
            seed: Deterministic seed.
            **kwargs: Additional parameters.

        Returns:
            A :class:`CompletionResponse` or iterator of
            :class:`CompletionChunk` if ``stream=True``.
        """
        body: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if stop is not None:
            body["stop"] = stop
        if frequency_penalty is not None:
            body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            body["presence_penalty"] = presence_penalty
        if seed is not None:
            body["seed"] = seed
        body.update(kwargs)

        if stream:
            return self._stream_create(body)

        result = self._resource._client.request(
            "POST", "/inference/completions", json=body,
        )
        return CompletionResponse.model_validate(result)

    def _stream_create(
        self, body: Dict[str, Any]
    ) -> Iterator[CompletionChunk]:
        """Open a streaming text completion and yield chunks."""
        body["stream"] = True
        response = self._resource._client.stream_request(
            "POST", "/inference/completions", json=body,
        )
        try:
            iterator = StreamIterator(response, chunk_type=CompletionChunk)
            for chunk in iterator:
                yield chunk
        finally:
            response.close()


class _Models:
    """``harchos.inference.models`` — Model catalog."""

    def __init__(self, resource: "InferenceResource") -> None:
        self._resource = resource

    def list(self) -> ModelList:
        """List all available models.

        Returns:
            A :class:`ModelList` containing model information.
        """
        result = self._resource._client.request(
            "GET", "/inference/models",
        )
        return ModelList.model_validate(result)


class InferenceResource:
    """Synchronous inference resource.

    Accessed via ``client.inference``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self.chat = _Chat(self)
        self.completions = _Completions(self)
        self.models = _Models(self)


# ===========================================================================
# Async variants
# ===========================================================================

class _AsyncChatCompletions:
    """``AsyncHarchOS.inference.chat.completions`` — async chat API."""

    def __init__(self, resource: "AsyncInferenceResource") -> None:
        self._resource = resource

    async def create(
        self,
        *,
        model: str,
        messages: List[Union[Dict[str, Any], ChatMessage]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletionResponse, AsyncStreamIterator]:
        """Create a chat completion (async).

        Args and return type are identical to the sync version.
        """
        normalized_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                normalized_messages.append(msg.model_dump(exclude_none=True))
            elif isinstance(msg, dict):
                normalized_messages.append(msg)
            else:
                normalized_messages.append({"role": "user", "content": str(msg)})

        body: Dict[str, Any] = {
            "model": model,
            "messages": normalized_messages,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if stop is not None:
            body["stop"] = stop
        if frequency_penalty is not None:
            body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            body["presence_penalty"] = presence_penalty
        if seed is not None:
            body["seed"] = seed
        body.update(kwargs)

        if stream:
            return await self._stream_create(body)

        result = await self._resource._client.request(
            "POST", "/inference/chat/completions", json=body,
        )
        return ChatCompletionResponse.model_validate(result)

    async def _stream_create(
        self, body: Dict[str, Any]
    ) -> AsyncStreamIterator:
        """Open an async streaming chat completion."""
        body["stream"] = True
        response = await self._resource._client.stream_request(
            "POST", "/inference/chat/completions", json=body,
        )
        return AsyncStreamIterator(response, chunk_type=ChatCompletionChunk)


class _AsyncChat:
    """Async ``inference.chat`` namespace."""

    def __init__(self, resource: "AsyncInferenceResource") -> None:
        self.completions = _AsyncChatCompletions(resource)


class _AsyncCompletions:
    """``AsyncHarchOS.inference.completions`` — async text completion."""

    def __init__(self, resource: "AsyncInferenceResource") -> None:
        self._resource = resource

    async def create(
        self,
        *,
        model: str,
        prompt: Union[str, List[str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Union[CompletionResponse, AsyncStreamIterator]:
        """Create a text completion (async)."""
        body: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if stop is not None:
            body["stop"] = stop
        if frequency_penalty is not None:
            body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            body["presence_penalty"] = presence_penalty
        if seed is not None:
            body["seed"] = seed
        body.update(kwargs)

        if stream:
            return await self._stream_create(body)

        result = await self._resource._client.request(
            "POST", "/inference/completions", json=body,
        )
        return CompletionResponse.model_validate(result)

    async def _stream_create(
        self, body: Dict[str, Any]
    ) -> AsyncStreamIterator:
        """Open an async streaming text completion."""
        body["stream"] = True
        response = await self._resource._client.stream_request(
            "POST", "/inference/completions", json=body,
        )
        return AsyncStreamIterator(response, chunk_type=CompletionChunk)


class _AsyncModels:
    """Async ``inference.models`` — model catalog."""

    def __init__(self, resource: "AsyncInferenceResource") -> None:
        self._resource = resource

    async def list(self) -> ModelList:
        """List all available models (async)."""
        result = await self._resource._client.request(
            "GET", "/inference/models",
        )
        return ModelList.model_validate(result)


class AsyncInferenceResource:
    """Asynchronous inference resource.

    Accessed via ``async_client.inference``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self.chat = _AsyncChat(self)
        self.completions = _AsyncCompletions(self)
        self.models = _AsyncModels(self)
