"""Tests for the HarchOSClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harchos import HarchOSClient
from harchos.config import HarchOSConfig
from harchos.resources.energy import EnergyResource
from harchos.resources.hubs import HubsResource
from harchos.resources.models import ModelsResource
from harchos.resources.workloads import WorkloadsResource


class TestHarchOSClientInit:
    """Tests for client initialization."""

    def test_default_init(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        assert client.config.region == "morocco"
        assert client.config.sovereignty == "strict"
        assert client.config.carbon_aware is True

    def test_custom_init(self) -> None:
        client = HarchOSClient(
            api_key="hsk_testapikey1234567890",
            region="uae",
            sovereignty="moderate",
            carbon_aware=False,
            timeout=60.0,
        )
        assert client.config.region == "uae"
        assert client.config.sovereignty == "moderate"
        assert client.config.carbon_aware is False
        assert client.config.timeout == 60.0

    def test_with_config(self) -> None:
        config = HarchOSConfig(
            api_key="hsk_testapikey1234567890",
            region="france",
        )
        client = HarchOSClient(config=config)
        assert client.config.region == "france"

    def test_resource_modules_initialized(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        assert isinstance(client.workloads, WorkloadsResource)
        assert isinstance(client.models, ModelsResource)
        assert isinstance(client.hubs, HubsResource)
        assert isinstance(client.energy, EnergyResource)

    def test_repr(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        r = repr(client)
        assert "HarchOSClient" in r
        assert "morocco" in r
        assert "strict" in r


class TestHarchOSClientSync:
    """Tests for sync client methods."""

    def test_sync_context_manager(self) -> None:
        with HarchOSClient(api_key="hsk_testapikey1234567890") as client:
            assert client.config is not None

    def test_close_sync(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        client.close_sync()  # Should not raise


class TestHarchOSClientAsync:
    """Tests for async client methods."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        async with HarchOSClient(api_key="hsk_testapikey1234567890") as client:
            assert client.config is not None

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        await client.close()  # Should not raise


class TestHarchOSClientHealth:
    """Tests for health check."""

    @pytest.mark.asyncio
    async def test_async_health(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "region": "morocco",
        }
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            health = await client.async_health()
            assert health.status == "healthy"

    def test_sync_health(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "region": "morocco",
        }
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            health = client.health()
            assert health.status == "healthy"
