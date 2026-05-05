"""HarchOS SDK configuration.

Manages API key, base URL, timeouts, and other client settings.
Supports environment variables and programmatic overrides.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

DEFAULT_BASE_URL = "https://api.harchos.ai/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class Config:
    """Immutable configuration for a HarchOS client.

    Args:
        api_key: HarchOS API key (starts with ``hsk_``).
        base_url: API base URL. Defaults to ``https://api.harchos.ai/v1``.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts for transient errors. Defaults to 3.
        default_headers: Extra HTTP headers sent with every request.
    """

    __slots__ = (
        "api_key",
        "base_url",
        "timeout",
        "max_retries",
        "default_headers",
    )

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        # Resolve api_key from env if not provided
        if api_key is None:
            api_key = os.environ.get("HARCHOS_API_KEY")
        self.api_key = api_key.strip() if api_key else None
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, min(max_retries, 10))
        self.default_headers = default_headers or {}

    @classmethod
    def from_env(cls, **overrides: object) -> Config:
        """Create a Config from environment variables with optional overrides.

        Reads ``HARCHOS_API_KEY``, ``HARCHOS_BASE_URL``,
        ``HARCHOS_TIMEOUT``, ``HARCHOS_MAX_RETRIES``.
        """
        kwargs: Dict[str, object] = {}
        if env_key := os.environ.get("HARCHOS_API_KEY"):
            kwargs["api_key"] = env_key
        if env_url := os.environ.get("HARCHOS_BASE_URL"):
            kwargs["base_url"] = env_url
        if env_timeout := os.environ.get("HARCHOS_TIMEOUT"):
            try:
                kwargs["timeout"] = float(env_timeout)
            except ValueError:
                pass
        if env_retries := os.environ.get("HARCHOS_MAX_RETRIES"):
            try:
                kwargs["max_retries"] = int(env_retries)
            except ValueError:
                pass
        kwargs.update(overrides)
        return cls(**kwargs)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        masked = f"***{self.api_key[-4:]}" if self.api_key else "None"
        return (
            f"Config(api_key={masked!r}, base_url={self.base_url!r}, "
            f"timeout={self.timeout}, max_retries={self.max_retries})"
        )
