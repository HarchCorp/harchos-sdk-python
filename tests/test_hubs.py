"""Tests for hub resource module."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harchos import HarchOSClient
from harchos.models.hub import Hub, HubCapacity, HubList, HubSpec, HubStatus, HubTier


class TestHubsAsync:
    """Tests for async hub operations."""

    @pytest.mark.asyncio
    async def test_async_list(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [sample_hub_data],
            "total": 1,
        }
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.hubs.async_list()
            assert isinstance(result, HubList)
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_async_get(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_hub_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            hub = await client.hubs.async_get("hub_xyz789")
            assert hub.metadata.id == "hub_xyz789"

    @pytest.mark.asyncio
    async def test_async_create(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_hub_data
        with patch.object(
            client._transport, "async_post", new_callable=AsyncMock, return_value=mock_response
        ):
            spec = HubSpec(name="test-hub", region="morocco")
            hub = await client.hubs.async_create(spec)
            assert isinstance(hub, Hub)

    @pytest.mark.asyncio
    async def test_async_capacity(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        capacity_data = sample_hub_data["capacity"]
        mock_response = MagicMock()
        mock_response.json.return_value = capacity_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            cap = await client.hubs.async_capacity("hub_xyz789")
            assert isinstance(cap, HubCapacity)
            assert cap.total_gpus == 16

    @pytest.mark.asyncio
    async def test_async_scale(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        scaled_data = {**sample_hub_data, "status": "scaling"}
        mock_response = MagicMock()
        mock_response.json.return_value = scaled_data
        with patch.object(
            client._transport, "async_patch", new_callable=AsyncMock, return_value=mock_response
        ):
            hub = await client.hubs.async_scale("hub_xyz789", target_gpu_count=24)
            assert hub.status == HubStatus.SCALING


class TestHubsSync:
    """Tests for sync hub operations."""

    def test_list(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [sample_hub_data],
            "total": 1,
        }
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            result = client.hubs.list()
            assert isinstance(result, HubList)

    def test_get(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_hub_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            hub = client.hubs.get("hub_xyz789")
            assert hub.metadata.id == "hub_xyz789"

    def test_capacity(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        capacity_data = sample_hub_data["capacity"]
        mock_response = MagicMock()
        mock_response.json.return_value = capacity_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            cap = client.hubs.capacity("hub_xyz789")
            assert isinstance(cap, HubCapacity)

    def test_scale(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        scaled_data = {**sample_hub_data, "status": "scaling"}
        mock_response = MagicMock()
        mock_response.json.return_value = scaled_data
        with patch.object(client._transport, "sync_patch", return_value=mock_response):
            hub = client.hubs.scale("hub_xyz789", target_gpu_count=24)
            assert hub.status == HubStatus.SCALING

    def test_drain(self, sample_hub_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        drained_data = {**sample_hub_data, "status": "draining"}
        mock_response = MagicMock()
        mock_response.json.return_value = drained_data
        with patch.object(client._transport, "sync_patch", return_value=mock_response):
            hub = client.hubs.drain("hub_xyz789")
            assert hub.status == HubStatus.DRAINING
