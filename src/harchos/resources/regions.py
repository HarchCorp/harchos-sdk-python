"""Regions resource module for the HarchOS SDK.

Provides both async and sync methods for querying available
HarchOS regions, their capabilities, and compliance info.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models.region import Region
from .base import BaseResource


class RegionsResource(BaseResource):
    """Manages region information for the HarchOS platform.

    Use this resource to:

    * List all available regions and their capabilities
    * Get detailed information about a specific region

    Usage::

        client = HarchOSClient(api_key="hsk_...")

        # List all available regions
        regions = client.regions.list()
        for r in regions:
            print(f"{r.name} ({r.code}): {r.total_gpus} GPUs, {r.avg_renewable_percentage}% renewable")

        # Get a specific region
        morocco = client.regions.get("morocco")
        print(f"Compliance: {morocco.compliance_frameworks}")
    """

    _resource_path = "/regions"

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_list(
        self,
        *,
        available: Optional[bool] = None,
    ) -> List[Region]:
        """List all available regions (async).

        Args:
            available: If set, filter by availability status.

        Returns:
            A list of :class:`Region` objects.
        """
        params: Dict[str, Any] = {}
        if available is not None:
            params["available"] = available

        response = await self._transport.async_get("/regions", params=params or None)
        data = response.json()
        if isinstance(data, list):
            return [Region.model_validate(r) for r in data]
        items = data.get("items", data.get("regions", []))
        return [Region.model_validate(r) for r in items]

    async def async_get(self, region_code: str) -> Region:
        """Get details for a specific region (async).

        Args:
            region_code: The region code (e.g. 'morocco', 'nigeria').

        Returns:
            A :class:`Region` object with full details.
        """
        data = await self._async_get(region_code, path=f"/regions/{region_code}")
        return Region.model_validate(data)

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        available: Optional[bool] = None,
    ) -> List[Region]:
        """List all available regions (sync).

        Args:
            available: If set, filter by availability status.

        Returns:
            A list of :class:`Region` objects.
        """
        params: Dict[str, Any] = {}
        if available is not None:
            params["available"] = available

        response = self._transport.sync_get("/regions", params=params or None)
        data = response.json()
        if isinstance(data, list):
            return [Region.model_validate(r) for r in data]
        items = data.get("items", data.get("regions", []))
        return [Region.model_validate(r) for r in items]

    def get(self, region_code: str) -> Region:
        """Get details for a specific region (sync).

        Args:
            region_code: The region code (e.g. 'morocco', 'nigeria').

        Returns:
            A :class:`Region` object with full details.
        """
        data = self._sync_get(region_code, path=f"/regions/{region_code}")
        return Region.model_validate(data)
