"""Tests for the WorkloadsResource module (v0.3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from harchos._client import HarchOS, AsyncHarchOS
from harchos._types import Workload, WorkloadList, WorkloadSpec
from harchos.resources.workloads import WorkloadsResource, AsyncWorkloadsResource


class TestWorkloadsResource:
    """Tests for the synchronous WorkloadsResource."""

    def test_create(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "wl_abc123",
            "name": "test-workload",
            "type": "training",
            "status": "pending",
            "spec": {
                "name": "test-workload",
                "type": "training",
                "gpu_count": 4,
                "gpu_type": "a100",
                "cpu_cores": 16,
                "memory_gb": 64.0,
                "priority": "high",
            },
            "hub_id": "hub_xyz789",
        }
        resource = WorkloadsResource(client)
        result = resource.create(name="test-workload", gpu_count=4, gpu_type="a100")
        assert isinstance(result, Workload)
        assert result.id == "wl_abc123"
        assert result.name == "test-workload"
        assert result.spec is not None
        assert result.spec.gpu_count == 4

    def test_create_with_carbon_budget(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "wl_abc123",
            "name": "green-workload",
            "type": "training",
            "status": "pending",
        }
        resource = WorkloadsResource(client)
        resource.create(
            name="green-workload",
            carbon_budget_grams=5000.0,
        )
        call_args = client.request.call_args
        body = call_args[1]["json"]
        assert body["carbon_budget_grams"] == 5000.0

    def test_list(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "items": [
                {
                    "id": "wl_abc123",
                    "name": "workload-1",
                    "type": "training",
                    "status": "running",
                },
                {
                    "id": "wl_def456",
                    "name": "workload-2",
                    "type": "inference",
                    "status": "pending",
                },
            ],
            "total": 2,
        }
        resource = WorkloadsResource(client)
        result = resource.list()
        assert isinstance(result, WorkloadList)
        assert result.total == 2
        assert len(result) == 2

    def test_list_with_filters(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {"items": [], "total": 0}
        resource = WorkloadsResource(client)
        resource.list(status="running", hub_id="hub_xyz789")
        call_args = client.request.call_args
        params = call_args[1]["params"]
        assert params["status"] == "running"
        assert params["hub_id"] == "hub_xyz789"

    def test_get(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "wl_abc123",
            "name": "test-workload",
            "type": "training",
            "status": "running",
        }
        resource = WorkloadsResource(client)
        result = resource.get("wl_abc123")
        assert isinstance(result, Workload)
        assert result.id == "wl_abc123"
        assert result.status == "running"
        client.request.assert_called_once_with("GET", "/workloads/wl_abc123")

    def test_update(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "wl_abc123",
            "name": "updated-workload",
            "type": "training",
            "status": "running",
        }
        resource = WorkloadsResource(client)
        result = resource.update("wl_abc123", name="updated-workload", status="running")
        assert isinstance(result, Workload)
        call_args = client.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "/workloads/wl_abc123"
        body = call_args[1]["json"]
        assert body["name"] == "updated-workload"
        assert body["status"] == "running"

    def test_delete(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {"deleted": True}
        resource = WorkloadsResource(client)
        result = resource.delete("wl_abc123")
        assert result == {"deleted": True}
        client.request.assert_called_once_with("DELETE", "/workloads/wl_abc123")


class TestAsyncWorkloadsResource:
    """Tests for the asynchronous AsyncWorkloadsResource."""

    @pytest.mark.asyncio
    async def test_create(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "id": "wl_abc123",
            "name": "test-workload",
            "type": "training",
            "status": "pending",
        })
        resource = AsyncWorkloadsResource(client)
        result = await resource.create(name="test-workload")
        assert isinstance(result, Workload)
        assert result.id == "wl_abc123"

    @pytest.mark.asyncio
    async def test_list(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "items": [
                {"id": "wl_1", "name": "wl1", "type": "training", "status": "running"},
            ],
            "total": 1,
        })
        resource = AsyncWorkloadsResource(client)
        result = await resource.list()
        assert isinstance(result, WorkloadList)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "id": "wl_abc123",
            "name": "test-workload",
            "type": "training",
            "status": "running",
        })
        resource = AsyncWorkloadsResource(client)
        result = await resource.get("wl_abc123")
        assert isinstance(result, Workload)

    @pytest.mark.asyncio
    async def test_update(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "id": "wl_abc123",
            "name": "updated",
            "type": "training",
            "status": "completed",
        })
        resource = AsyncWorkloadsResource(client)
        result = await resource.update("wl_abc123", status="completed")
        assert isinstance(result, Workload)

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={"deleted": True})
        resource = AsyncWorkloadsResource(client)
        result = await resource.delete("wl_abc123")
        assert result == {"deleted": True}


class TestWorkloadsViaClient:
    """Tests that workload resources are accessible via the HarchOS client."""

    def test_sync_client_has_workloads(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "workloads")
        assert isinstance(client.workloads, WorkloadsResource)

    def test_async_client_has_workloads(self) -> None:
        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "workloads")
        assert isinstance(client.workloads, AsyncWorkloadsResource)
