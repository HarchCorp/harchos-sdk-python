"""HarchOS SDK authentication module.

Handles API key validation, token refresh, and header construction.
Supports both static API keys and short-lived tokens obtained via
the HarchOS auth endpoint.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from .errors import APIKeyExpiredError, InvalidAPIKeyError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_API_KEY_PREFIX = "hsk_"
_TOKEN_PREFIX = "hst_"
_API_KEY_MIN_LENGTH = 20


# ---------------------------------------------------------------------------
# Authenticator
# ---------------------------------------------------------------------------

class Authenticator:
    """Manages authentication credentials for HarchOS API requests.

    Supports:
    - Static API keys (``hsk_...``)
    - Short-lived bearer tokens (``hst_...``)
    - Automatic token refresh when approaching expiry

    Example::

        auth = Authenticator(api_key="hsk_abcdef...")
        headers = auth.get_headers()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        token: Optional[str] = None,
        token_expires_at: Optional[float] = None,
        refresh_buffer: float = 60.0,
    ) -> None:
        """Initialize the authenticator.

        Args:
            api_key: HarchOS API key (starts with ``hsk_``).
            token: Existing bearer token (starts with ``hst_``).
            token_expires_at: Unix timestamp when *token* expires.
            refresh_buffer: Seconds before expiry to trigger a refresh.

        Raises:
            InvalidAPIKeyError: If the API key format is invalid.
        """
        self._api_key: Optional[str] = None
        self._token: Optional[str] = None
        self._token_expires_at: Optional[float] = token_expires_at
        self._refresh_buffer = refresh_buffer

        if api_key is not None:
            self.set_api_key(api_key)

        if token is not None:
            self.set_token(token, expires_at=token_expires_at)

    # ------------------------------------------------------------------
    # API Key management
    # ------------------------------------------------------------------

    @property
    def api_key(self) -> Optional[str]:
        """Return the configured API key (if any)."""
        return self._api_key

    def set_api_key(self, api_key: str) -> None:
        """Set and validate the API key.

        Args:
            api_key: The API key string.

        Raises:
            InvalidAPIKeyError: If the key format is invalid.
        """
        key = api_key.strip()
        if not key:
            raise InvalidAPIKeyError("API key must not be empty")

        if not key.startswith(_API_KEY_PREFIX):
            raise InvalidAPIKeyError(
                f"API key must start with '{_API_KEY_PREFIX}'"
            )

        if len(key) < _API_KEY_MIN_LENGTH:
            raise InvalidAPIKeyError(
                f"API key must be at least {_API_KEY_MIN_LENGTH} characters long"
            )

        self._api_key = key

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    @property
    def token(self) -> Optional[str]:
        """Return the current bearer token (if any)."""
        return self._token

    @property
    def is_token_expired(self) -> bool:
        """Check whether the current token has expired or is about to."""
        if self._token is None:
            return True
        if self._token_expires_at is None:
            return False
        return time.time() >= (self._token_expires_at - self._refresh_buffer)

    def set_token(
        self,
        token: str,
        *,
        expires_at: Optional[float] = None,
        ttl: Optional[float] = None,
    ) -> None:
        """Set a bearer token with optional expiry information.

        Args:
            token: The bearer token string.
            expires_at: Absolute Unix timestamp for token expiry.
            ttl: Time-to-live in seconds from now (alternative to *expires_at*).

        Raises:
            ValueError: If both *expires_at* and *ttl* are provided.
        """
        if expires_at is not None and ttl is not None:
            raise ValueError("Provide either 'expires_at' or 'ttl', not both")

        self._token = token.strip()

        if ttl is not None:
            self._token_expires_at = time.time() + ttl
        else:
            self._token_expires_at = expires_at

    def clear_token(self) -> None:
        """Remove the current bearer token."""
        self._token = None
        self._token_expires_at = None

    # ------------------------------------------------------------------
    # Header construction
    # ------------------------------------------------------------------

    def get_headers(self) -> Dict[str, str]:
        """Build authentication headers for an API request.

        Preference order:
        1. Bearer token (if present and not expired)
        2. API key via ``X-API-Key`` header

        Returns:
            A dictionary of HTTP headers.

        Raises:
            APIKeyExpiredError: If a token is present but expired and no
                API key is available for re-authentication.
        """
        headers: Dict[str, str] = {}

        # Prefer bearer token
        if self._token is not None:
            if self.is_token_expired:
                if self._api_key is None:
                    raise APIKeyExpiredError(
                        "Token expired and no API key available for re-authentication"
                    )
                # Token expired – fall back to API key
                self.clear_token()
            else:
                headers["Authorization"] = f"Bearer {self._token}"
                return headers

        # Fall back to API key
        if self._api_key is not None:
            headers["X-API-Key"] = self._api_key
            return headers

        # No credentials at all
        return headers

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        parts: list[str] = [self.__class__.__name__]
        if self._api_key:
            masked = self._api_key[:8] + "..." + self._api_key[-4:]
            parts.append(f"api_key={masked!r}")
        if self._token:
            parts.append("token=***")
        return f"<{' '.join(parts)}>"

    @classmethod
    def from_env(cls) -> "Authenticator":
        """Create an :class:`Authenticator` from the ``HARCHOS_API_KEY`` env var.

        Returns:
            A new authenticator with the key from the environment.

        Raises:
            InvalidAPIKeyError: If the environment variable is set but invalid.
        """
        api_key = os.environ.get("HARCHOS_API_KEY")
        if api_key:
            return cls(api_key=api_key)
        return cls()
