"""Tests for the HarchOS retry logic (v0.3)."""

from __future__ import annotations

import asyncio

import pytest

from harchos._retry import RetryConfig, retry_async, retry_sync, DEFAULT_RETRYABLE_CODES
from harchos._exceptions import HarchOSError, InferenceError, RateLimitError


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_defaults(self) -> None:
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.jitter is True
        assert config.retryable_codes == DEFAULT_RETRYABLE_CODES
        assert 429 in config.retryable_codes
        assert 500 in config.retryable_codes

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
        config = RetryConfig(base_delay=1.0, jitter=True)
        for _ in range(100):
            delay = config.compute_delay(0)
            # base_delay + [0, 0.5) jitter
            assert 1.0 <= delay < 1.5

    def test_is_retryable_by_status_code(self) -> None:
        config = RetryConfig()
        assert config.is_retryable(InferenceError(status_code=500))

    def test_is_not_retryable_client_error(self) -> None:
        config = RetryConfig()
        error = HarchOSError("Bad request", code="bad_request", status_code=400)
        assert not config.is_retryable(error)

    def test_is_not_retryable_no_status_code(self) -> None:
        config = RetryConfig()
        error = HarchOSError("Unknown error")
        assert not config.is_retryable(error)

    def test_custom_status_codes(self) -> None:
        config = RetryConfig(retryable_codes={429, 502})
        assert config.is_retryable(RateLimitError())
        assert not config.is_retryable(InferenceError())

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
                raise InferenceError()
            return "success"

        result = await retry_async(fn, config=config)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        async def fn() -> str:
            raise InferenceError()

        with pytest.raises(InferenceError):
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
                raise InferenceError()
            return "success"

        result = retry_sync(fn, config=config)
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self) -> None:
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        def fn() -> str:
            raise InferenceError()

        with pytest.raises(InferenceError):
            retry_sync(fn, config=config)

    def test_non_retryable_error_raised_immediately(self) -> None:
        config = RetryConfig(max_retries=3)
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            raise HarchOSError("Not retryable", code="not_retryable")

        with pytest.raises(HarchOSError):
            retry_sync(fn, config=config)
        assert call_count == 1
