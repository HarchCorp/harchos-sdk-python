"""Tests for the HubsResource module (v0.3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from harchos._client import HarchOS, AsyncHarchOS
from harchos._types import Hub, HubCapacity, HubList
from harchos.resources.hubs import HubsResource, AsyncHubsResource


class TestHubsResource:
    """Tests for the synchronous HubsResource."""

    def test_list(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "items": [
                {
                    "id": "hub_morocco1",
                    "name": "morocco-primary",
                    "region": "morocco",
                    "status": "ready",
                    "tier": "enterprise",
                    "active_workloads": 4,
                },
            ],
            "total": 1,
        }
        resource = HubsResource(client)
        result = resource.list()
        assert isinstance(result, HubList)
        assert result.total == 1
        assert len(result) == 1
        assert result.items[0].id == "hub_morocco1"
        client.request.assert_called_once()
        call_args = client.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/hubs"

    def test_list_with_filters(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {"items": [], "total": 0}
        resource = HubsResource(client)
        resource.list(region="morocco", status="ready", tier="enterprise")
        call_args = client.request.call_args
        params = call_args[1]["params"]
        assert params["region"] == "morocco"
        assert params["status"] == "ready"
        assert params["tier"] == "enterprise"

    def test_get(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "hub_morocco1",
            "name": "morocco-primary",
            "region": "morocco",
            "status": "ready",
            "tier": "enterprise",
            "capacity": {
                "total_gpus": 16,
                "available_gpus": 8,
                "total_cpu_cores": 256,
                "available_cpu_cores": 128,
                "total_memory_gb": 2048.0,
                "available_memory_gb": 1024.0,
            },
        }
        resource = HubsResource(client)
        result = resource.get("hub_morocco1")
        assert isinstance(result, Hub)
        assert result.id == "hub_morocco1"
        assert result.region == "morocco"
        assert result.capacity is not None
        assert result.capacity.total_gpus == 16
        client.request.assert_called_once_with("GET", "/hubs/hub_morocco1")


class TestAsyncHubsResource:
    """Tests for the asynchronous AsyncHubsResource."""

    @pytest.mark.asyncio
    async def test_list(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "items": [
                {"id": "hub_1", "name": "hub1", "region": "morocco"},
            ],
            "total": 1,
        })
        resource = AsyncHubsResource(client)
        result = await resource.list()
        assert isinstance(result, HubList)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "id": "hub_1",
            "name": "morocco-primary",
            "region": "morocco",
        })
        resource = AsyncHubsResource(client)
        result = await resource.get("hub_1")
        assert isinstance(result, Hub)
        assert result.id == "hub_1"


class TestHubViaClient:
    """Tests that hub resources are accessible via the HarchOS client."""

    def test_sync_client_has_hubs(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "hubs")
        assert isinstance(client.hubs, HubsResource)

    def test_async_client_has_hubs(self) -> None:
        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "hubs")
        assert isinstance(client.hubs, AsyncHubsResource)
