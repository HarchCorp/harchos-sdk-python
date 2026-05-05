"""Auth resource — User info and API key management.

Provides ``harchos.auth.me()``, ``harchos.auth.create_api_key(name)``,
and ``harchos.auth.revoke_api_key(id)``.
"""

from __future__ import annotations

from typing import Any, Dict

from .._types import APIKeyInfo, UserInfo


class AuthResource:
    """Synchronous auth resource.

    Accessed via ``client.auth``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def me(self) -> UserInfo:
        """Get information about the authenticated user.

        Returns:
            A :class:`UserInfo` object with user details.
        """
        result = self._client.request("GET", "/auth/me")
        return UserInfo.model_validate(result)

    def create_api_key(self, name: str) -> APIKeyInfo:
        """Create a new API key.

        Args:
            name: A descriptive name for the API key.

        Returns:
            An :class:`APIKeyInfo` object with the new key details.
        """
        result = self._client.request(
            "POST", "/auth/api-keys", json={"name": name},
        )
        return APIKeyInfo.model_validate(result)

    def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        """Revoke an API key.

        Args:
            key_id: The API key identifier to revoke.

        Returns:
            Confirmation dict from the API.
        """
        return self._client.request("DELETE", f"/auth/api-keys/{key_id}")


# ===========================================================================
# Async variant
# ===========================================================================

class AsyncAuthResource:
    """Asynchronous auth resource.

    Accessed via ``async_client.auth``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def me(self) -> UserInfo:
        """Get information about the authenticated user (async)."""
        result = await self._client.request("GET", "/auth/me")
        return UserInfo.model_validate(result)

    async def create_api_key(self, name: str) -> APIKeyInfo:
        """Create a new API key (async)."""
        result = await self._client.request(
            "POST", "/auth/api-keys", json={"name": name},
        )
        return APIKeyInfo.model_validate(result)

    async def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        """Revoke an API key (async)."""
        return await self._client.request("DELETE", f"/auth/api-keys/{key_id}")
