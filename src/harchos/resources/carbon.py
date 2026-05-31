"""Carbon resource — Carbon intensity, optimization, and tracking.

Provides carbon-aware scheduling tools unique to HarchOS:
- ``harchos.carbon.intensity(zone="MA")`` — Real-time carbon intensity
- ``harchos.carbon.optimize(...)`` — Carbon-aware workload optimization
- ``harchos.carbon.forecast(zone)`` — Carbon intensity forecast
- ``harchos.carbon.dashboard()`` — Platform-wide carbon dashboard
- ``harchos.carbon.optimal_hub(...)`` — Find the greenest hub
- ``harchos.carbon.tracker`` — Context manager for tracking total CO2
"""

from __future__ import annotations

import threading
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from .._types import (
    CarbonDashboard,
    CarbonForecast,
    CarbonIntensity,
    CarbonIntensityList,
    CarbonOptimalHub,
    CarbonOptimizeResult,
)


class _CarbonTracker:
    """Context manager to track total carbon across multiple requests.

    Usage::

        with harchos.carbon.tracker() as tracker:
            result1 = harchos.inference.chat.completions.create(...)
            result2 = harchos.inference.chat.completions.create(...)
        print(f"Total CO2: {tracker.total_gco2}g")
    """

    def __init__(self) -> None:
        self._total_gco2: float = 0.0
        self._requests: int = 0
        self._regions: List[str] = []
        self._active: bool = False

    @property
    def total_gco2(self) -> float:
        """Total grams of CO2 emitted across all tracked requests."""
        return self._total_gco2

    @property
    def request_count(self) -> int:
        """Number of requests tracked."""
        return self._requests

    @property
    def regions(self) -> List[str]:
        """List of hub regions used."""
        return list(self._regions)

    @property
    def avg_gco2_per_request(self) -> float:
        """Average CO2 per request."""
        if self._requests == 0:
            return 0.0
        return self._total_gco2 / self._requests

    def record(self, gco2: float, region: str = "unknown") -> None:
        """Record carbon data from a request.

        Args:
            gco2: Grams of CO2 emitted.
            region: Hub region.
        """
        self._total_gco2 += gco2
        self._requests += 1
        if region not in self._regions:
            self._regions.append(region)

    def __enter__(self) -> "_CarbonTracker":
        self._active = True
        return self

    def __exit__(self, *args: Any) -> None:
        self._active = False

    def __repr__(self) -> str:
        return (
            f"CarbonTracker(requests={self._requests}, "
            f"total_gco2={self._total_gco2:.2f})"
        )


class CarbonResource:
    """Synchronous carbon resource.

    Accessed via ``client.carbon``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self._tracker: Optional[_CarbonTracker] = None

    def intensity(self, zone: str) -> CarbonIntensity:
        """Get real-time carbon intensity for a zone.

        Args:
            zone: Zone code (e.g. ``"MA"`` for Morocco, ``"FR"`` for France).

        Returns:
            A :class:`CarbonIntensity` object.
        """
        result = self._client.request("GET", "/carbon/intensity", params={"zone": zone})
        return CarbonIntensity.model_validate(result)

    def optimize(
        self,
        *,
        workload_name: str,
        workload_type: str = "training",
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        carbon_aware: bool = True,
        carbon_max_gco2: Optional[float] = None,
        region: Optional[str] = None,
        estimated_duration_hours: float = 1.0,
    ) -> CarbonOptimizeResult:
        """Run carbon-aware workload optimization.

        Args:
            workload_name: Name of the workload to optimize.
            workload_type: Workload type (``training``, ``inference``, etc.).
            gpu_count: Number of GPUs required.
            gpu_type: GPU type (e.g. ``"a100"``).
            carbon_aware: Enable carbon-aware scheduling.
            carbon_max_gco2: Maximum carbon intensity threshold in gCO2/kWh.
            region: Preferred region.
            estimated_duration_hours: Estimated duration in hours.

        Returns:
            A :class:`CarbonOptimizeResult` with the optimization recommendation.
        """
        body: Dict[str, Any] = {
            "workload_name": workload_name,
            "workload_type": workload_type,
            "gpu_count": gpu_count,
            "carbon_aware": carbon_aware,
            "estimated_duration_hours": estimated_duration_hours,
        }
        if gpu_type is not None:
            body["gpu_type"] = gpu_type
        if carbon_max_gco2 is not None:
            body["carbon_max_gco2"] = carbon_max_gco2
        if region is not None:
            body["region"] = region

        result = self._client.request("POST", "/carbon/optimize", json=body)
        return CarbonOptimizeResult.model_validate(result)

    def forecast(self, zone: str) -> CarbonForecast:
        """Get carbon intensity forecast for a zone.

        Args:
            zone: Zone code (e.g. ``"MA"``).

        Returns:
            A :class:`CarbonForecast` with forecast data points and green windows.
        """
        result = self._client.request("GET", "/carbon/forecast", params={"zone": zone})
        return CarbonForecast.model_validate(result)

    def dashboard(self) -> CarbonDashboard:
        """Get the platform-wide carbon dashboard.

        Returns:
            A :class:`CarbonDashboard` with aggregate carbon metrics.
        """
        result = self._client.request("GET", "/carbon/dashboard")
        return CarbonDashboard.model_validate(result)

    def optimal_hub(
        self,
        *,
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        region: Optional[str] = None,
        carbon_max_gco2: Optional[float] = None,
    ) -> CarbonOptimalHub:
        """Find the greenest hub for a workload.

        Args:
            gpu_count: Number of GPUs required.
            gpu_type: GPU type (e.g. ``"a100"``).
            region: Preferred region.
            carbon_max_gco2: Maximum carbon intensity threshold.

        Returns:
            A :class:`CarbonOptimalHub` with the recommended hub.
        """
        params: Dict[str, Any] = {"gpu_count": gpu_count}
        if gpu_type is not None:
            params["gpu_type"] = gpu_type
        if region is not None:
            params["region"] = region
        if carbon_max_gco2 is not None:
            params["carbon_max_gco2"] = carbon_max_gco2

        result = self._client.request("GET", "/carbon/optimal-hub", params=params)
        return CarbonOptimalHub.model_validate(result)

    @contextmanager
    def tracker(self) -> Generator[_CarbonTracker, None, None]:
        """Context manager to track total carbon across multiple requests.

        Example::

            with harchos.carbon.tracker() as tracker:
                result1 = harchos.inference.chat.completions.create(...)
                result2 = harchos.inference.chat.completions.create(...)
                # Auto-track carbon from inference responses
                for resp in [result1, result2]:
                    if hasattr(resp, 'carbon_footprint'):
                        tracker.record(
                            gco2=resp.carbon_footprint.gco2,
                            region=resp.carbon_footprint.hub_region,
                        )
            print(f"Total CO2: {tracker.total_gco2}g")

        Yields:
            A :class:`_CarbonTracker` instance.
        """
        t = _CarbonTracker()
        self._tracker = t
        try:
            yield t
        finally:
            self._tracker = None


# ===========================================================================
# Async variant
# ===========================================================================

class _AsyncCarbonTracker:
    """Async context manager for tracking total carbon across requests.

    Usage::

        async with harchos.carbon.tracker() as tracker:
            result = await harchos.inference.chat.completions.create(...)
            if hasattr(result, 'carbon_footprint'):
                tracker.record(
                    gco2=result.carbon_footprint.gco2,
                    region=result.carbon_footprint.hub_region,
                )
        print(f"Total CO2: {tracker.total_gco2}g")
    """

    def __init__(self) -> None:
        self._total_gco2: float = 0.0
        self._requests: int = 0
        self._regions: List[str] = []
        self._active: bool = False

    @property
    def total_gco2(self) -> float:
        return self._total_gco2

    @property
    def request_count(self) -> int:
        return self._requests

    @property
    def regions(self) -> List[str]:
        return list(self._regions)

    @property
    def avg_gco2_per_request(self) -> float:
        if self._requests == 0:
            return 0.0
        return self._total_gco2 / self._requests

    def record(self, gco2: float, region: str = "unknown") -> None:
        self._total_gco2 += gco2
        self._requests += 1
        if region not in self._regions:
            self._regions.append(region)

    async def __aenter__(self) -> "_AsyncCarbonTracker":
        self._active = True
        return self

    async def __aexit__(self, *args: Any) -> None:
        self._active = False

    def __repr__(self) -> str:
        return (
            f"AsyncCarbonTracker(requests={self._requests}, "
            f"total_gco2={self._total_gco2:.2f})"
        )


class AsyncCarbonResource:
    """Asynchronous carbon resource.

    Accessed via ``async_client.carbon``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def intensity(self, zone: str) -> CarbonIntensity:
        """Get real-time carbon intensity for a zone (async)."""
        result = await self._client.request("GET", "/carbon/intensity", params={"zone": zone})
        return CarbonIntensity.model_validate(result)

    async def optimize(
        self,
        *,
        workload_name: str,
        workload_type: str = "training",
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        carbon_aware: bool = True,
        carbon_max_gco2: Optional[float] = None,
        region: Optional[str] = None,
        estimated_duration_hours: float = 1.0,
    ) -> CarbonOptimizeResult:
        """Run carbon-aware workload optimization (async)."""
        body: Dict[str, Any] = {
            "workload_name": workload_name,
            "workload_type": workload_type,
            "gpu_count": gpu_count,
            "carbon_aware": carbon_aware,
            "estimated_duration_hours": estimated_duration_hours,
        }
        if gpu_type is not None:
            body["gpu_type"] = gpu_type
        if carbon_max_gco2 is not None:
            body["carbon_max_gco2"] = carbon_max_gco2
        if region is not None:
            body["region"] = region

        result = await self._client.request("POST", "/carbon/optimize", json=body)
        return CarbonOptimizeResult.model_validate(result)

    async def forecast(self, zone: str) -> CarbonForecast:
        """Get carbon intensity forecast for a zone (async)."""
        result = await self._client.request("GET", "/carbon/forecast", params={"zone": zone})
        return CarbonForecast.model_validate(result)

    async def dashboard(self) -> CarbonDashboard:
        """Get the platform-wide carbon dashboard (async)."""
        result = await self._client.request("GET", "/carbon/dashboard")
        return CarbonDashboard.model_validate(result)

    async def optimal_hub(
        self,
        *,
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        region: Optional[str] = None,
        carbon_max_gco2: Optional[float] = None,
    ) -> CarbonOptimalHub:
        """Find the greenest hub for a workload (async)."""
        params: Dict[str, Any] = {"gpu_count": gpu_count}
        if gpu_type is not None:
            params["gpu_type"] = gpu_type
        if region is not None:
            params["region"] = region
        if carbon_max_gco2 is not None:
            params["carbon_max_gco2"] = carbon_max_gco2

        result = await self._client.request("GET", "/carbon/optimal-hub", params=params)
        return CarbonOptimalHub.model_validate(result)

    @asynccontextmanager
    async def tracker(self) -> AsyncGenerator[_AsyncCarbonTracker, None]:
        """Context manager to track total carbon across async requests.

        Usage::

            async with async_client.carbon.tracker() as tracker:
                result = await async_client.inference.chat.completions.create(...)
                tracker.record(gco2=result.carbon_footprint.gco2)

        Yields:
            An :class:`_AsyncCarbonTracker` instance.
        """
        t = _AsyncCarbonTracker()
        try:
            yield t
        finally:
            pass
