"""Tests for workload resource module."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harchos import HarchOSClient
from harchos.models.workload import (
    Workload,
    WorkloadList,
    WorkloadSpec,
    WorkloadStatus,
    WorkloadType,
)


class TestWorkloadsAsync:
    """Tests for async workload operations."""

    @pytest.mark.asyncio
    async def test_async_list(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [sample_workload_data],
            "total": 1,
        }
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.workloads.async_list()
            assert isinstance(result, WorkloadList)
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_async_get(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_workload_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            wl = await client.workloads.async_get("wl_abc123")
            assert wl.metadata.id == "wl_abc123"

    @pytest.mark.asyncio
    async def test_async_create(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_workload_data
        with patch.object(
            client._transport, "async_post", new_callable=AsyncMock, return_value=mock_response
        ):
            spec = WorkloadSpec(name="test-wl", type=WorkloadType.TRAINING)
            wl = await client.workloads.async_create(spec)
            assert wl.spec.name == "gpt4-training-run"

    @pytest.mark.asyncio
    async def test_async_cancel(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        cancelled_data = {**sample_workload_data, "status": "cancelled"}
        mock_response = MagicMock()
        mock_response.json.return_value = cancelled_data
        with patch.object(
            client._transport, "async_patch", new_callable=AsyncMock, return_value=mock_response
        ):
            wl = await client.workloads.async_cancel("wl_abc123")
            assert wl.status == WorkloadStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_async_delete(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        with patch.object(
            client._transport, "async_delete", new_callable=AsyncMock, return_value=mock_response
        ):
            await client.workloads.async_delete("wl_abc123")  # Should not raise


class TestWorkloadsSync:
    """Tests for sync workload operations."""

    def test_list(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [sample_workload_data],
            "total": 1,
        }
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            result = client.workloads.list()
            assert isinstance(result, WorkloadList)

    def test_get(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_workload_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            wl = client.workloads.get("wl_abc123")
            assert wl.metadata.id == "wl_abc123"

    def test_create(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_workload_data
        with patch.object(client._transport, "sync_post", return_value=mock_response):
            spec = WorkloadSpec(name="test", type=WorkloadType.TRAINING)
            wl = client.workloads.create(spec)
            assert isinstance(wl, Workload)

    def test_cancel(self, sample_workload_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        cancelled_data = {**sample_workload_data, "status": "cancelled"}
        mock_response = MagicMock()
        mock_response.json.return_value = cancelled_data
        with patch.object(client._transport, "sync_patch", return_value=mock_response):
            wl = client.workloads.cancel("wl_abc123")
            assert wl.status == WorkloadStatus.CANCELLED

    def test_delete(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        with patch.object(client._transport, "sync_delete", return_value=mock_response):
            client.workloads.delete("wl_abc123")  # Should not raise
