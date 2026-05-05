"""Carbon-aware scheduling resource module for the HarchOS SDK.

Provides both async and sync methods for carbon intensity queries,
optimal hub selection, workload optimization, forecasting, and
carbon metrics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.carbon import (
    CarbonDashboard,
    CarbonForecast,
    CarbonIntensityZone,
    CarbonIntensityZoneList,
    CarbonMetrics,
    CarbonOptimalHub,
    CarbonOptimizeResult,
)
from .base import BaseResource


class CarbonResource(BaseResource):
    """Manages carbon-aware scheduling and carbon intensity data.

    This is HarchOS's key differentiator: native carbon-aware GPU
    orchestration.  Use this resource to:

    * Query real-time carbon intensity by zone
    * Find the greenest hub for a workload
    * Optimize workload scheduling to minimize CO2 emissions
    * Get carbon intensity forecasts
    * Track carbon savings metrics

    Usage::

        client = HarchOSClient(api_key="hsk_...")

        # Get carbon intensity for Morocco
        ma = client.carbon.get_intensity("MA")
        print(f"Morocco: {ma.carbon_intensity_gco2_kwh} gCO2/kWh")

        # Find the greenest hub
        optimal = client.carbon.optimal_hub(region="europe")
        print(f"Best hub: {optimal.recommended_hub_name}")

        # Optimize a workload
        result = client.carbon.optimize(
            workload_name="training-job",
            gpu_count=4,
            gpu_type="A100",
            carbon_aware=True,
            carbon_max_gco2=100,
        )
        print(f"Action: {result.action}, CO2 saved: {result.carbon_saved_kg} kg")
    """

    _resource_path = "/carbon"

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_get_intensity(
        self,
        zone: str,
    ) -> CarbonIntensityZone:
        """Get real-time carbon intensity for an electricity zone (async).

        Args:
            zone: Electricity Maps zone code (e.g. 'MA', 'FR', 'DE', 'GB').

        Returns:
            A :class:`CarbonIntensityZone` with current carbon data.
        """
        data = await self._async_get(zone, path=f"/carbon/intensity/{zone}")
        return CarbonIntensityZone.model_validate(data)

    async def async_list_intensities(
        self,
    ) -> CarbonIntensityZoneList:
        """Get carbon intensity for all known zones (async).

        Returns:
            A :class:`CarbonIntensityZoneList` with data for all zones.
        """
        response = await self._transport.async_get("/carbon/intensity")
        return CarbonIntensityZoneList.model_validate(response.json())

    async def async_optimal_hub(
        self,
        *,
        region: Optional[str] = None,
        gpu_count: Optional[int] = None,
        gpu_type: Optional[str] = None,
        carbon_max_gco2: Optional[float] = None,
        priority: Optional[str] = None,
        defer_ok: bool = True,
    ) -> CarbonOptimalHub:
        """Find the carbon-optimal hub for a workload (async).

        Args:
            region: Target region filter.
            gpu_count: Minimum number of GPUs required.
            gpu_type: GPU type required.
            carbon_max_gco2: Maximum acceptable carbon intensity in gCO2/kWh.
            priority: Workload priority (low/normal/high/critical).
            defer_ok: Whether deferral is acceptable.

        Returns:
            A :class:`CarbonOptimalHub` with the recommendation.
        """
        payload: Dict[str, Any] = {"defer_ok": defer_ok}
        if region is not None:
            payload["region"] = region
        if gpu_count is not None:
            payload["gpu_count"] = gpu_count
        if gpu_type is not None:
            payload["gpu_type"] = gpu_type
        if carbon_max_gco2 is not None:
            payload["carbon_max_gco2"] = carbon_max_gco2
        if priority is not None:
            payload["priority"] = priority

        data = await self._async_create(payload, path="/carbon/optimal-hub")
        return CarbonOptimalHub.model_validate(data)

    async def async_optimize(
        self,
        *,
        workload_name: str,
        workload_type: str = "training",
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        cpu_cores: int = 4,
        memory_gb: float = 16.0,
        priority: str = "normal",
        carbon_aware: bool = True,
        carbon_max_gco2: Optional[float] = None,
        region: Optional[str] = None,
        estimated_duration_hours: float = 1.0,
    ) -> CarbonOptimizeResult:
        """Optimize a workload's scheduling based on carbon intensity (async).

        This is the primary method for carbon-aware scheduling.  It
        ranks hubs by carbon intensity, selects the greenest hub, and
        decides whether to schedule now, defer, or reject.

        Args:
            workload_name: Name of the workload.
            workload_type: Type (training/inference/fine_tuning/etc.).
            gpu_count: Number of GPUs needed.
            gpu_type: GPU type required.
            cpu_cores: CPU cores needed.
            memory_gb: Memory in GB needed.
            priority: Workload priority.
            carbon_aware: Enable carbon-aware scheduling.
            carbon_max_gco2: Maximum carbon intensity threshold.
            region: Preferred region.
            estimated_duration_hours: Estimated workload duration.

        Returns:
            A :class:`CarbonOptimizeResult` with the scheduling decision.
        """
        payload: Dict[str, Any] = {
            "workload_name": workload_name,
            "workload_type": workload_type,
            "gpu_count": gpu_count,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "priority": priority,
            "carbon_aware": carbon_aware,
            "estimated_duration_hours": estimated_duration_hours,
        }
        if gpu_type is not None:
            payload["gpu_type"] = gpu_type
        if carbon_max_gco2 is not None:
            payload["carbon_max_gco2"] = carbon_max_gco2
        if region is not None:
            payload["region"] = region

        data = await self._async_create(payload, path="/carbon/optimize")
        return CarbonOptimizeResult.model_validate(data)

    async def async_get_forecast(
        self,
        zone: str,
        *,
        hours: int = 24,
    ) -> CarbonForecast:
        """Get a carbon intensity forecast for a zone (async).

        Args:
            zone: Electricity Maps zone code.
            hours: Forecast horizon (1-72 hours).

        Returns:
            A :class:`CarbonForecast` with forecast points and green windows.
        """
        response = await self._transport.async_get(
            f"/carbon/forecast/{zone}", params={"hours": hours}
        )
        return CarbonForecast.model_validate(response.json())

    async def async_get_metrics(
        self,
        *,
        period_days: int = 30,
    ) -> CarbonMetrics:
        """Get aggregate carbon metrics for the platform (async).

        Args:
            period_days: Metrics period in days (1-365).

        Returns:
            A :class:`CarbonMetrics` with savings and hub data.
        """
        response = await self._transport.async_get(
            "/carbon/metrics", params={"period_days": period_days}
        )
        return CarbonMetrics.model_validate(response.json())

    async def async_get_dashboard(
        self,
    ) -> CarbonDashboard:
        """Get full carbon-aware dashboard data (async).

        Returns:
            A :class:`CarbonDashboard` with metrics, intensities, and logs.
        """
        response = await self._transport.async_get("/carbon/dashboard")
        return CarbonDashboard.model_validate(response.json())

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def get_intensity(
        self,
        zone: str,
    ) -> CarbonIntensityZone:
        """Get real-time carbon intensity for an electricity zone (sync).

        Args:
            zone: Electricity Maps zone code (e.g. 'MA', 'FR', 'DE', 'GB').

        Returns:
            A :class:`CarbonIntensityZone` with current carbon data.
        """
        data = self._sync_get(zone, path=f"/carbon/intensity/{zone}")
        return CarbonIntensityZone.model_validate(data)

    def list_intensities(
        self,
    ) -> CarbonIntensityZoneList:
        """Get carbon intensity for all known zones (sync).

        Returns:
            A :class:`CarbonIntensityZoneList` with data for all zones.
        """
        response = self._transport.sync_get("/carbon/intensity")
        return CarbonIntensityZoneList.model_validate(response.json())

    def optimal_hub(
        self,
        *,
        region: Optional[str] = None,
        gpu_count: Optional[int] = None,
        gpu_type: Optional[str] = None,
        carbon_max_gco2: Optional[float] = None,
        priority: Optional[str] = None,
        defer_ok: bool = True,
    ) -> CarbonOptimalHub:
        """Find the carbon-optimal hub for a workload (sync).

        Args:
            region: Target region filter.
            gpu_count: Minimum number of GPUs required.
            gpu_type: GPU type required.
            carbon_max_gco2: Maximum acceptable carbon intensity.
            priority: Workload priority.
            defer_ok: Whether deferral is acceptable.

        Returns:
            A :class:`CarbonOptimalHub` with the recommendation.
        """
        payload: Dict[str, Any] = {"defer_ok": defer_ok}
        if region is not None:
            payload["region"] = region
        if gpu_count is not None:
            payload["gpu_count"] = gpu_count
        if gpu_type is not None:
            payload["gpu_type"] = gpu_type
        if carbon_max_gco2 is not None:
            payload["carbon_max_gco2"] = carbon_max_gco2
        if priority is not None:
            payload["priority"] = priority

        data = self._sync_create(payload, path="/carbon/optimal-hub")
        return CarbonOptimalHub.model_validate(data)

    def optimize(
        self,
        *,
        workload_name: str,
        workload_type: str = "training",
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        cpu_cores: int = 4,
        memory_gb: float = 16.0,
        priority: str = "normal",
        carbon_aware: bool = True,
        carbon_max_gco2: Optional[float] = None,
        region: Optional[str] = None,
        estimated_duration_hours: float = 1.0,
    ) -> CarbonOptimizeResult:
        """Optimize a workload's scheduling based on carbon intensity (sync).

        Args:
            workload_name: Name of the workload.
            workload_type: Type (training/inference/fine_tuning/etc.).
            gpu_count: Number of GPUs needed.
            gpu_type: GPU type required.
            cpu_cores: CPU cores needed.
            memory_gb: Memory in GB needed.
            priority: Workload priority.
            carbon_aware: Enable carbon-aware scheduling.
            carbon_max_gco2: Maximum carbon intensity threshold.
            region: Preferred region.
            estimated_duration_hours: Estimated workload duration.

        Returns:
            A :class:`CarbonOptimizeResult` with the scheduling decision.
        """
        payload: Dict[str, Any] = {
            "workload_name": workload_name,
            "workload_type": workload_type,
            "gpu_count": gpu_count,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "priority": priority,
            "carbon_aware": carbon_aware,
            "estimated_duration_hours": estimated_duration_hours,
        }
        if gpu_type is not None:
            payload["gpu_type"] = gpu_type
        if carbon_max_gco2 is not None:
            payload["carbon_max_gco2"] = carbon_max_gco2
        if region is not None:
            payload["region"] = region

        data = self._sync_create(payload, path="/carbon/optimize")
        return CarbonOptimizeResult.model_validate(data)

    def get_forecast(
        self,
        zone: str,
        *,
        hours: int = 24,
    ) -> CarbonForecast:
        """Get a carbon intensity forecast for a zone (sync).

        Args:
            zone: Electricity Maps zone code.
            hours: Forecast horizon (1-72 hours).

        Returns:
            A :class:`CarbonForecast` with forecast points and green windows.
        """
        response = self._transport.sync_get(
            f"/carbon/forecast/{zone}", params={"hours": hours}
        )
        return CarbonForecast.model_validate(response.json())

    def get_metrics(
        self,
        *,
        period_days: int = 30,
    ) -> CarbonMetrics:
        """Get aggregate carbon metrics for the platform (sync).

        Args:
            period_days: Metrics period in days (1-365).

        Returns:
            A :class:`CarbonMetrics` with savings and hub data.
        """
        response = self._transport.sync_get(
            "/carbon/metrics", params={"period_days": period_days}
        )
        return CarbonMetrics.model_validate(response.json())

    def get_dashboard(
        self,
    ) -> CarbonDashboard:
        """Get full carbon-aware dashboard data (sync).

        Returns:
            A :class:`CarbonDashboard` with metrics, intensities, and logs.
        """
        response = self._transport.sync_get("/carbon/dashboard")
        return CarbonDashboard.model_validate(response.json())
