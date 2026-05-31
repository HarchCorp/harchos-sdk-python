"""Tests for the CarbonResource module (v0.3).

Replaces the old test_energy.py which tested the removed EnergyResource.
Carbon is now handled via client.carbon (CarbonResource / AsyncCarbonResource).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from harchos._client import HarchOS, AsyncHarchOS
from harchos._types import (
    CarbonIntensity,
    CarbonForecast,
    CarbonDashboard,
    CarbonOptimalHub,
    CarbonOptimizeResult,
)
from harchos.resources.carbon import CarbonResource, AsyncCarbonResource


class TestCarbonResource:
    """Tests for the synchronous CarbonResource."""

    def test_intensity(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "zone": "MA",
            "zone_name": "Morocco",
            "carbon_intensity_gco2_kwh": 150.0,
            "renewable_percentage": 65.0,
            "fossil_percentage": 35.0,
        }
        resource = CarbonResource(client)
        result = resource.intensity("MA")
        assert isinstance(result, CarbonIntensity)
        assert result.zone == "MA"
        assert result.carbon_intensity_gco2_kwh == 150.0
        assert result.is_green is True  # 150 < 200
        client.request.assert_called_once_with("GET", "/carbon/intensity", params={"zone": "MA"})

    def test_intensity_high_carbon(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "zone": "US",
            "zone_name": "United States",
            "carbon_intensity_gco2_kwh": 450.0,
            "renewable_percentage": 25.0,
            "fossil_percentage": 75.0,
        }
        resource = CarbonResource(client)
        result = resource.intensity("US")
        assert isinstance(result, CarbonIntensity)
        assert result.is_green is False  # 450 >= 200

    def test_optimize(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "action": "schedule",
            "workload_name": "test-workload",
            "selected_hub_id": "hub_xyz789",
            "selected_hub_name": "morocco-primary",
            "carbon_intensity_at_schedule_gco2_kwh": 120.0,
            "carbon_saved_kg": 0.5,
        }
        resource = CarbonResource(client)
        result = resource.optimize(
            workload_name="test-workload",
            gpu_count=2,
            gpu_type="a100",
        )
        assert isinstance(result, CarbonOptimizeResult)
        assert result.action == "schedule"
        assert result.workload_name == "test-workload"
        assert result.selected_hub_id == "hub_xyz789"

    def test_optimize_with_defer(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "action": "defer",
            "workload_name": "deferred-workload",
            "deferred_hours": 3.5,
            "reason": "Green window available in 3.5 hours",
        }
        resource = CarbonResource(client)
        result = resource.optimize(workload_name="deferred-workload")
        assert isinstance(result, CarbonOptimizeResult)
        assert result.action == "defer"
        assert result.deferred_hours == 3.5

    def test_forecast(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "zone": "MA",
            "zone_name": "Morocco",
            "forecast": [
                {
                    "timestamp": "2024-01-15T12:00:00Z",
                    "carbon_intensity_gco2_kwh": 100.0,
                    "renewable_percentage": 80.0,
                    "is_green": True,
                },
            ],
            "green_windows": [
                {"start": "2024-01-15T10:00:00Z", "end": "2024-01-15T14:00:00Z"},
            ],
        }
        resource = CarbonResource(client)
        result = resource.forecast("MA")
        assert isinstance(result, CarbonForecast)
        assert result.zone == "MA"
        assert len(result.forecast) == 1
        assert result.best_window is not None
        client.request.assert_called_once_with("GET", "/carbon/forecast", params={"zone": "MA"})

    def test_forecast_no_green_windows(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "zone": "US",
            "zone_name": "United States",
            "forecast": [],
            "green_windows": [],
        }
        resource = CarbonResource(client)
        result = resource.forecast("US")
        assert result.best_window is None

    def test_dashboard(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "total_carbon_saved_kg": 150.0,
            "total_workloads_optimized": 42,
            "total_workloads_deferred": 10,
            "avg_carbon_intensity_gco2_kwh": 130.0,
            "best_hub_name": "morocco-primary",
            "best_hub_carbon_intensity": 80.0,
            "worst_hub_carbon_intensity": 500.0,
        }
        resource = CarbonResource(client)
        result = resource.dashboard()
        assert isinstance(result, CarbonDashboard)
        assert result.total_carbon_saved_kg == 150.0
        assert result.total_workloads_optimized == 42
        client.request.assert_called_once_with("GET", "/carbon/dashboard")

    def test_optimal_hub(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "recommended_hub_id": "hub_morocco1",
            "recommended_hub_name": "morocco-primary",
            "hub_region": "morocco",
            "hub_zone": "MA",
            "carbon_intensity_gco2_kwh": 80.0,
            "renewable_percentage": 85.0,
            "available_gpus": 4,
            "action": "schedule",
            "estimated_carbon_saved_kg": 0.3,
        }
        resource = CarbonResource(client)
        result = resource.optimal_hub(gpu_count=2, gpu_type="a100")
        assert isinstance(result, CarbonOptimalHub)
        assert result.recommended_hub_id == "hub_morocco1"
        assert result.is_deferred is False

    def test_tracker_context_manager(self) -> None:
        resource = CarbonResource(MagicMock(spec=HarchOS))
        with resource.tracker() as tracker:
            assert tracker.total_gco2 == 0.0
            assert tracker.request_count == 0
            tracker.record(gco2=1.5, region="morocco")
            tracker.record(gco2=2.0, region="morocco")
            assert tracker.total_gco2 == 3.5
            assert tracker.request_count == 2
            assert tracker.regions == ["morocco"]
            assert tracker.avg_gco2_per_request == 1.75
        # After exit, tracker is still accessible but detached
        assert tracker.total_gco2 == 3.5

    def test_tracker_multiple_regions(self) -> None:
        resource = CarbonResource(MagicMock(spec=HarchOS))
        with resource.tracker() as tracker:
            tracker.record(gco2=1.0, region="morocco")
            tracker.record(gco2=2.0, region="france")
            assert len(tracker.regions) == 2
            assert "morocco" in tracker.regions
            assert "france" in tracker.regions

    def test_tracker_repr(self) -> None:
        resource = CarbonResource(MagicMock(spec=HarchOS))
        with resource.tracker() as tracker:
            tracker.record(gco2=1.5)
            r = repr(tracker)
            assert "CarbonTracker" in r
            assert "1" in r  # request count


class TestAsyncCarbonResource:
    """Tests for the asynchronous AsyncCarbonResource."""

    @pytest.mark.asyncio
    async def test_intensity(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "zone": "MA",
            "zone_name": "Morocco",
            "carbon_intensity_gco2_kwh": 150.0,
            "renewable_percentage": 65.0,
            "fossil_percentage": 35.0,
        })
        resource = AsyncCarbonResource(client)
        result = await resource.intensity("MA")
        assert isinstance(result, CarbonIntensity)
        assert result.zone == "MA"

    @pytest.mark.asyncio
    async def test_optimize(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "action": "schedule",
            "workload_name": "test-workload",
            "selected_hub_id": "hub_xyz789",
        })
        resource = AsyncCarbonResource(client)
        result = await resource.optimize(workload_name="test-workload")
        assert isinstance(result, CarbonOptimizeResult)
        assert result.action == "schedule"

    @pytest.mark.asyncio
    async def test_forecast(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "zone": "MA",
            "zone_name": "Morocco",
            "forecast": [],
            "green_windows": [],
        })
        resource = AsyncCarbonResource(client)
        result = await resource.forecast("MA")
        assert isinstance(result, CarbonForecast)
        assert result.zone == "MA"

    @pytest.mark.asyncio
    async def test_dashboard(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "total_carbon_saved_kg": 150.0,
            "total_workloads_optimized": 42,
        })
        resource = AsyncCarbonResource(client)
        result = await resource.dashboard()
        assert isinstance(result, CarbonDashboard)
        assert result.total_carbon_saved_kg == 150.0

    @pytest.mark.asyncio
    async def test_optimal_hub(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "recommended_hub_id": "hub_morocco1",
            "recommended_hub_name": "morocco-primary",
            "hub_region": "morocco",
            "hub_zone": "MA",
            "carbon_intensity_gco2_kwh": 80.0,
            "renewable_percentage": 85.0,
            "available_gpus": 4,
            "action": "schedule",
        })
        resource = AsyncCarbonResource(client)
        result = await resource.optimal_hub(gpu_count=2)
        assert isinstance(result, CarbonOptimalHub)
        assert result.recommended_hub_id == "hub_morocco1"

    @pytest.mark.asyncio
    async def test_tracker_context_manager(self) -> None:
        resource = AsyncCarbonResource(MagicMock(spec=AsyncHarchOS))
        async with resource.tracker() as tracker:
            assert tracker.total_gco2 == 0.0
            tracker.record(gco2=1.5, region="morocco")
            assert tracker.total_gco2 == 1.5
            assert tracker.request_count == 1
