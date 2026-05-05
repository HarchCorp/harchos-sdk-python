"""Retry logic with exponential backoff and jitter.

Implements production-grade retry handling for transient HTTP errors
(429, 500, 502, 503, 504). Respects ``Retry-After`` headers on
rate-limited responses and adds random jitter to avoid thundering herd.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Awaitable, Callable, Optional, Set, Type

from ._exceptions import HarchOSError, RateLimitError

# Default status codes that trigger retries
DEFAULT_RETRYABLE_CODES: Set[int] = {429, 500, 502, 503, 504}


class RetryConfig:
    """Configuration for retry behaviour.

    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries).
        base_delay: Base delay in seconds for exponential backoff.
        max_delay: Maximum delay cap in seconds.
        backoff_factor: Multiplier for exponential backoff.
        jitter: Whether to add random jitter to delays.
        retryable_codes: HTTP status codes that trigger a retry.
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retryable_codes: Optional[Set[int]] = None,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retryable_codes = retryable_codes or DEFAULT_RETRYABLE_CODES

    def compute_delay(self, attempt: int) -> float:
        """Compute delay before the next retry attempt.

        Uses exponential backoff: ``base_delay * backoff_factor^attempt``,
        capped at ``max_delay``, with optional jitter.

        Args:
            attempt: Zero-indexed attempt number.

        Returns:
            Delay in seconds.
        """
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        if self.jitter:
            delay += random.uniform(0, 0.5)
        return delay

    def is_retryable(self, error: HarchOSError) -> bool:
        """Check if an error is retryable based on status code."""
        if error.status_code and error.status_code in self.retryable_codes:
            return True
        return False


async def retry_async(
    fn: Callable[..., Awaitable[Any]],
    *,
    config: RetryConfig,
) -> Any:
    """Execute an async callable with retry logic.

    Args:
        fn: The async callable to execute.
        config: Retry configuration.

    Returns:
        The result of *fn* on success.

    Raises:
        HarchOSError: The last error after exhausting retries.
    """
    last_error: Optional[HarchOSError] = None

    for attempt in range(config.max_retries + 1):
        try:
            return await fn()
        except HarchOSError as exc:
            last_error = exc

            if attempt >= config.max_retries or not config.is_retryable(exc):
                raise

            delay = config.compute_delay(attempt)

            # Respect Retry-After on 429
            if isinstance(exc, RateLimitError) and exc.retry_after is not None:
                delay = max(delay, exc.retry_after)

            await asyncio.sleep(delay)

    raise last_error  # type: ignore[misc]


def retry_sync(
    fn: Callable[..., Any],
    *,
    config: RetryConfig,
) -> Any:
    """Execute a synchronous callable with retry logic.

    Args:
        fn: The synchronous callable to execute.
        config: Retry configuration.

    Returns:
        The result of *fn* on success.

    Raises:
        HarchOSError: The last error after exhausting retries.
    """
    last_error: Optional[HarchOSError] = None

    for attempt in range(config.max_retries + 1):
        try:
            return fn()
        except HarchOSError as exc:
            last_error = exc

            if attempt >= config.max_retries or not config.is_retryable(exc):
                raise

            delay = config.compute_delay(attempt)

            if isinstance(exc, RateLimitError) and exc.retry_after is not None:
                delay = max(delay, exc.retry_after)

            time.sleep(delay)

    raise last_error  # type: ignore[misc]
