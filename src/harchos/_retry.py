"""HarchOS SDK retry logic with exponential backoff and jitter.

Implements a production-grade retry strategy that respects rate limits,
handles transient failures, and incorporates carbon-aware scheduling hints.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Awaitable, Callable, Optional, Set, Type

from .errors import (
    HarchOSError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
)
from .errors import TimeoutError as HarchOSTimeoutError

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

RetryablePredicate = Callable[[HarchOSError], bool]


# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------

class RetryConfig:
    """Configuration for retry behaviour.

    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries).
        base_delay: Base delay in seconds for exponential backoff.
        max_delay: Maximum delay cap in seconds.
            The formula is ``min(base_delay * 2 ** attempt + jitter, max_delay)``.
        backoff_factor: Multiplier for exponential backoff.
        jitter: Whether to add random jitter to delays.
        jitter_range: Max jitter in seconds (uniform random ``[0, jitter_range)``).
        retryable_status_codes: HTTP status codes that trigger a retry.
        retryable_exceptions: Exception types that trigger a retry.
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.5,
        retryable_status_codes: Optional[Set[int]] = None,
        retryable_exceptions: Optional[Set[Type[HarchOSError]]] = None,
        custom_predicate: Optional[RetryablePredicate] = None,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.jitter_range = jitter_range
        self.retryable_status_codes = (
            retryable_status_codes
            if retryable_status_codes is not None
            else {429, 500, 502, 503, 504}
        )
        self.retryable_exceptions = retryable_exceptions if retryable_exceptions is not None else {
            InternalServerError,
            ServiceUnavailableError,
            HarchOSTimeoutError,
        }
        self.custom_predicate = custom_predicate

    def compute_delay(self, attempt: int) -> float:
        """Compute the delay before the next retry attempt.

        Uses exponential backoff with optional jitter.

        Args:
            attempt: Zero-indexed attempt number.

        Returns:
            Delay in seconds.
        """
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay += random.uniform(0, self.jitter_range)

        return delay

    def is_retryable(self, error: HarchOSError) -> bool:
        """Determine whether *error* warrants a retry.

        Args:
            error: The error encountered during the request.

        Returns:
            ``True`` if the request should be retried.
        """
        # Check custom predicate first
        if self.custom_predicate is not None:
            try:
                if self.custom_predicate(error):
                    return True
            except Exception:
                pass

        # Check by status code
        if error.status_code and error.status_code in self.retryable_status_codes:
            return True

        # Check by exception type
        return any(isinstance(error, exc_type) for exc_type in self.retryable_exceptions)


# ---------------------------------------------------------------------------
# Async retry executor
# ---------------------------------------------------------------------------

async def retry_async(
    fn: Callable[..., Awaitable[Any]],
    *,
    config: RetryConfig,
    on_retry: Optional[Callable[[int, HarchOSError, float], None]] = None,
) -> Any:
    """Execute an async callable with retry logic.

    Args:
        fn: The async callable to execute.
        config: Retry configuration.
        on_retry: Optional callback invoked before each retry with
            ``(attempt, error, delay)``.

    Returns:
        The result of *fn* on success.

    Raises:
        HarchOSError: The last error encountered after exhausting all retries.
    """
    last_error: Optional[HarchOSError] = None

    for attempt in range(config.max_retries + 1):
        try:
            return await fn()
        except HarchOSError as exc:
            last_error = exc

            if attempt >= config.max_retries or not config.is_retryable(exc):
                raise

            # Special handling for rate limits – respect Retry-After
            delay = config.compute_delay(attempt)
            if isinstance(exc, RateLimitError) and exc.retry_after is not None:
                delay = max(delay, exc.retry_after)

            if on_retry is not None:
                on_retry(attempt, exc, delay)

            await asyncio.sleep(delay)

    # Should never reach here, but satisfy type checker
    raise last_error  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Sync retry executor
# ---------------------------------------------------------------------------

def retry_sync(
    fn: Callable[..., Any],
    *,
    config: RetryConfig,
    on_retry: Optional[Callable[[int, HarchOSError, float], None]] = None,
) -> Any:
    """Execute a synchronous callable with retry logic.

    Args:
        fn: The synchronous callable to execute.
        config: Retry configuration.
        on_retry: Optional callback invoked before each retry.

    Returns:
        The result of *fn* on success.

    Raises:
        HarchOSError: The last error encountered after exhausting all retries.
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

            if on_retry is not None:
                on_retry(attempt, exc, delay)

            time.sleep(delay)

    raise last_error  # type: ignore[misc]
