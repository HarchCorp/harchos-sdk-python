"""Tests for the HarchOS retry logic."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from harchos._retry import RetryConfig, retry_async, retry_sync
from harchos.errors import (
    HarchOSError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_defaults(self) -> None:
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.jitter is True
        assert 429 in config.retryable_status_codes
        assert 500 in config.retryable_status_codes

    def test_compute_delay_first_attempt(self) -> None:
        config = RetryConfig(base_delay=1.0, jitter=False)
        delay = config.compute_delay(0)
        assert delay == 1.0

    def test_compute_delay_exponential(self) -> None:
        config = RetryConfig(base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert config.compute_delay(0) == 1.0
        assert config.compute_delay(1) == 2.0
        assert config.compute_delay(2) == 4.0
        assert config.compute_delay(3) == 8.0

    def test_compute_delay_capped(self) -> None:
        config = RetryConfig(base_delay=1.0, max_delay=5.0, backoff_factor=2.0, jitter=False)
        assert config.compute_delay(10) == 5.0

    def test_compute_delay_with_jitter(self) -> None:
        config = RetryConfig(base_delay=1.0, jitter=True, jitter_range=0.5)
        for _ in range(100):
            delay = config.compute_delay(0)
            # base_delay + [0, jitter_range)
            assert 1.0 <= delay < 1.5

    def test_is_retryable_by_status_code(self) -> None:
        config = RetryConfig()
        assert config.is_retryable(InternalServerError(status_code=500))
        assert config.is_retryable(ServiceUnavailableError(status_code=503))

    def test_is_not_retryable_client_error(self) -> None:
        config = RetryConfig()
        error = HarchOSError("Bad request", code="bad_request", status_code=400)
        assert not config.is_retryable(error)

    def test_is_retryable_by_exception_type(self) -> None:
        config = RetryConfig()
        assert config.is_retryable(InternalServerError())
        assert config.is_retryable(ServiceUnavailableError())

    def test_custom_predicate(self) -> None:
        def always_retry(err: HarchOSError) -> bool:
            return True

        config = RetryConfig(custom_predicate=always_retry)
        error = HarchOSError("any error")
        assert config.is_retryable(error)

    def test_custom_status_codes(self) -> None:
        config = RetryConfig(retryable_status_codes={429, 502})
        assert config.is_retryable(RateLimitError())
        assert not config.is_retryable(InternalServerError())

    def test_zero_retries(self) -> None:
        config = RetryConfig(max_retries=0)
        assert config.max_retries == 0


class TestRetryAsync:
    """Tests for retry_async."""

    @pytest.mark.asyncio
    async def test_success_first_try(self) -> None:
        config = RetryConfig(max_retries=3)
        call_count = 0

        async def fn() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(fn, config=config)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        call_count = 0

        async def fn() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise InternalServerError()
            return "success"

        result = await retry_async(fn, config=config)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        async def fn() -> str:
            raise InternalServerError()

        with pytest.raises(InternalServerError):
            await retry_async(fn, config=config)

    @pytest.mark.asyncio
    async def test_non_retryable_error_raised_immediately(self) -> None:
        config = RetryConfig(max_retries=3)
        call_count = 0

        async def fn() -> str:
            nonlocal call_count
            call_count += 1
            raise HarchOSError("Not retryable", code="not_retryable")

        with pytest.raises(HarchOSError):
            await retry_async(fn, config=config)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limit_respects_retry_after(self) -> None:
        config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)
        call_count = 0
        retry_after_value = 0.05

        async def fn() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(retry_after=retry_after_value)
            return "success"

        start = asyncio.get_event_loop().time()
        result = await retry_async(fn, config=config)
        elapsed = asyncio.get_event_loop().time() - start

        assert result == "success"
        # Should have waited at least retry_after_value
        assert elapsed >= retry_after_value * 0.8  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_on_retry_callback(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        retries_log: list[tuple[int, HarchOSError, float]] = []
        call_count = 0

        async def fn() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise InternalServerError()
            return "ok"

        def on_retry(attempt: int, error: HarchOSError, delay: float) -> None:
            retries_log.append((attempt, error, delay))

        await retry_async(fn, config=config, on_retry=on_retry)
        assert len(retries_log) == 2
        assert isinstance(retries_log[0][1], InternalServerError)


class TestRetrySync:
    """Tests for retry_sync."""

    def test_success_first_try(self) -> None:
        config = RetryConfig(max_retries=3)
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry_sync(fn, config=config)
        assert result == "success"
        assert call_count == 1

    def test_retry_on_retryable_error(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise InternalServerError()
            return "success"

        result = retry_sync(fn, config=config)
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        def fn() -> str:
            raise InternalServerError()

        with pytest.raises(InternalServerError):
            retry_sync(fn, config=config)
