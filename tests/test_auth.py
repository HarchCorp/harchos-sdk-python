"""Tests for the AuthResource module (v0.3).

Auth is now handled via client.auth (AuthResource / AsyncAuthResource)
instead of the removed Authenticator class.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harchos._client import HarchOS, AsyncHarchOS
from harchos._types import UserInfo, APIKeyInfo
from harchos.resources.auth import AuthResource, AsyncAuthResource


class TestAuthResource:
    """Tests for the synchronous AuthResource."""

    def test_me(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "usr_abc123",
            "email": "test@harchos.ai",
            "name": "Test User",
            "plan": "community",
        }
        resource = AuthResource(client)
        result = resource.me()
        assert isinstance(result, UserInfo)
        assert result.id == "usr_abc123"
        assert result.email == "test@harchos.ai"
        assert result.plan == "community"
        client.request.assert_called_once_with("GET", "/auth/me")

    def test_create_api_key(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "key_abc123",
            "name": "my-key",
            "prefix": "hsk_abcd",
            "created_at": "2024-01-10T08:00:00Z",
            "revoked": False,
        }
        resource = AuthResource(client)
        result = resource.create_api_key("my-key")
        assert isinstance(result, APIKeyInfo)
        assert result.name == "my-key"
        assert result.prefix == "hsk_abcd"
        client.request.assert_called_once_with(
            "POST", "/auth/api-keys", json={"name": "my-key"},
        )

    def test_revoke_api_key(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {"deleted": True}
        resource = AuthResource(client)
        result = resource.revoke_api_key("key_abc123")
        assert result == {"deleted": True}
        client.request.assert_called_once_with("DELETE", "/auth/api-keys/key_abc123")


class TestAsyncAuthResource:
    """Tests for the asynchronous AsyncAuthResource."""

    @pytest.mark.asyncio
    async def test_me(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "id": "usr_abc123",
            "email": "test@harchos.ai",
            "name": "Test User",
            "plan": "community",
        })
        resource = AsyncAuthResource(client)
        result = await resource.me()
        assert isinstance(result, UserInfo)
        assert result.id == "usr_abc123"
        client.request.assert_called_once_with("GET", "/auth/me")

    @pytest.mark.asyncio
    async def test_create_api_key(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "id": "key_abc123",
            "name": "my-key",
            "prefix": "hsk_abcd",
            "revoked": False,
        })
        resource = AsyncAuthResource(client)
        result = await resource.create_api_key("my-key")
        assert isinstance(result, APIKeyInfo)
        assert result.name == "my-key"
        client.request.assert_called_once_with(
            "POST", "/auth/api-keys", json={"name": "my-key"},
        )

    @pytest.mark.asyncio
    async def test_revoke_api_key(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={"deleted": True})
        resource = AsyncAuthResource(client)
        result = await resource.revoke_api_key("key_abc123")
        assert result == {"deleted": True}
        client.request.assert_called_once_with("DELETE", "/auth/api-keys/key_abc123")


class TestAuthViaClient:
    """Tests that auth resources are accessible via the HarchOS client."""

    def test_sync_client_has_auth(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "auth")
        assert isinstance(client.auth, AuthResource)

    def test_async_client_has_auth(self) -> None:
        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "auth")
        assert isinstance(client.auth, AsyncAuthResource)
