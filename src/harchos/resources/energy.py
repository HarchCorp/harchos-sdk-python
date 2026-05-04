"""Energy resource module for the HarchOS SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.energy import (
    EnergyConsumption,
    EnergyReport,
    EnergySummary,
    GreenWindow,
)
from .base import BaseResource


class EnergyResource(BaseResource):
    """Manages energy monitoring and carbon-aware scheduling.

    Provides both async and sync methods for energy reports, green
    scheduling windows, and carbon budget tracking.
    """

    _resource_path = "/energy"

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_get_report(
        self,
        resource_id: str,
        *,
        resource_type: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> EnergyReport:
        """Get an energy report for a specific resource (async).

        Args:
            resource_id: The resource to report on.
            resource_type: Optional resource type hint.
            period_start: Report period start.
            period_end: Report period end.

        Returns:
            An :class:`EnergyReport` with consumption data.
        """
        params: Dict[str, Any] = {}
        if resource_type:
            params["resource_type"] = resource_type
        if period_start:
            params["period_start"] = period_start.isoformat()
        if period_end:
            params["period_end"] = period_end.isoformat()

        data = await self._async_list(
            path=f"/energy/reports/{resource_id}", params=params or None
        )
        return EnergyReport.model_validate(data)

    async def async_get_summary(
        self,
        *,
        region: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> EnergySummary:
        """Get an aggregated energy summary (async).

        Args:
            region: Optional region filter.
            period_start: Summary period start.
            period_end: Summary period end.

        Returns:
            An :class:`EnergySummary` across resources.
        """
        params: Dict[str, Any] = {}
        if region:
            params["region"] = region
        if period_start:
            params["period_start"] = period_start.isoformat()
        if period_end:
            params["period_end"] = period_end.isoformat()

        response = await self._transport.async_get("/energy/summary", params=params)
        return EnergySummary.model_validate(response.json())

    async def async_get_green_windows(
        self,
        *,
        region: Optional[str] = None,
        min_renewable_percentage: Optional[float] = None,
    ) -> List[GreenWindow]:
        """Get upcoming green scheduling windows (async).

        Args:
            region: Optional region filter.
            min_renewable_percentage: Minimum renewable fraction to include.

        Returns:
            A list of :class:`GreenWindow` objects.
        """
        params: Dict[str, Any] = {}
        if region:
            params["region"] = region
        if min_renewable_percentage is not None:
            params["min_renewable_percentage"] = min_renewable_percentage

        response = await self._transport.async_get("/energy/green-windows", params=params)
        data = response.json()
        if isinstance(data, list):
            return [GreenWindow.model_validate(w) for w in data]
        items = data.get("items", data.get("windows", []))
        return [GreenWindow.model_validate(w) for w in items]

    async def async_get_consumption(
        self,
        resource_id: str,
        *,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> EnergyConsumption:
        """Get energy consumption for a resource (async).

        Args:
            resource_id: The resource to query.
            period_start: Consumption period start.
            period_end: Consumption period end.

        Returns:
            :class:`EnergyConsumption` details.
        """
        params: Dict[str, Any] = {}
        if period_start:
            params["period_start"] = period_start.isoformat()
        if period_end:
            params["period_end"] = period_end.isoformat()

        response = await self._transport.async_get(
            f"/energy/consumption/{resource_id}", params=params
        )
        return EnergyConsumption.model_validate(response.json())

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def get_report(
        self,
        resource_id: str,
        *,
        resource_type: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> EnergyReport:
        """Get an energy report for a specific resource (sync)."""
        params: Dict[str, Any] = {}
        if resource_type:
            params["resource_type"] = resource_type
        if period_start:
            params["period_start"] = period_start.isoformat()
        if period_end:
            params["period_end"] = period_end.isoformat()

        data = self._sync_list(
            path=f"/energy/reports/{resource_id}", params=params or None
        )
        return EnergyReport.model_validate(data)

    def get_summary(
        self,
        *,
        region: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> EnergySummary:
        """Get an aggregated energy summary (sync)."""
        params: Dict[str, Any] = {}
        if region:
            params["region"] = region
        if period_start:
            params["period_start"] = period_start.isoformat()
        if period_end:
            params["period_end"] = period_end.isoformat()

        response = self._transport.sync_get("/energy/summary", params=params)
        return EnergySummary.model_validate(response.json())

    def get_green_windows(
        self,
        *,
        region: Optional[str] = None,
        min_renewable_percentage: Optional[float] = None,
    ) -> List[GreenWindow]:
        """Get upcoming green scheduling windows (sync)."""
        params: Dict[str, Any] = {}
        if region:
            params["region"] = region
        if min_renewable_percentage is not None:
            params["min_renewable_percentage"] = min_renewable_percentage

        response = self._transport.sync_get("/energy/green-windows", params=params)
        data = response.json()
        if isinstance(data, list):
            return [GreenWindow.model_validate(w) for w in data]
        items = data.get("items", data.get("windows", []))
        return [GreenWindow.model_validate(w) for w in items]

    def get_consumption(
        self,
        resource_id: str,
        *,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> EnergyConsumption:
        """Get energy consumption for a resource (sync)."""
        params: Dict[str, Any] = {}
        if period_start:
            params["period_start"] = period_start.isoformat()
        if period_end:
            params["period_end"] = period_end.isoformat()

        response = self._transport.sync_get(
            f"/energy/consumption/{resource_id}", params=params
        )
        return EnergyConsumption.model_validate(response.json())
