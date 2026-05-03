"""Hubs resource module for the HarchOS SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models.hub import (
    Hub,
    HubCapacity,
    HubList,
    HubSpec,
    HubStatus,
    HubTier,
)
from .base import BaseResource


class HubsResource(BaseResource):
    """Manages HarchOS Hubs – sovereign compute clusters.

    Provides both async and sync methods for hub CRUD, capacity
    inspection, and scaling.
    """

    _resource_path = "/hubs"
    _model_class = Hub

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_list(
        self,
        *,
        status: Optional[HubStatus] = None,
        tier: Optional[HubTier] = None,
        region: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> HubList:
        """List hubs with optional filtering (async).

        Args:
            status: Filter by hub status.
            tier: Filter by tier.
            region: Filter by region.
            labels: Filter by labels.
            page: Page number.
            per_page: Items per page.

        Returns:
            A :class:`HubList` with matching hubs.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if status is not None:
            params["status"] = status.value if isinstance(status, HubStatus) else status
        if tier is not None:
            params["tier"] = tier.value if isinstance(tier, HubTier) else tier
        if region is not None:
            params["region"] = region
        if labels:
            for key, value in labels.items():
                params[f"label.{key}"] = value

        data = await self._async_list(params=params)
        return HubList.model_validate(data)

    async def async_get(self, hub_id: str) -> Hub:
        """Retrieve a hub by ID (async).

        Args:
            hub_id: The unique hub identifier.

        Returns:
            The requested :class:`Hub`.
        """
        data = await self._async_get(hub_id)
        return Hub.model_validate(data)

    async def async_create(self, spec: HubSpec) -> Hub:
        """Create a new hub (async).

        Args:
            spec: The hub specification.

        Returns:
            The newly created :class:`Hub`.
        """
        data = await self._async_create(spec.model_dump(mode="json", exclude_none=True))
        return Hub.model_validate(data)

    async def async_update(self, hub_id: str, spec: HubSpec) -> Hub:
        """Update an existing hub (async).

        Args:
            hub_id: The hub to update.
            spec: The updated specification.

        Returns:
            The updated :class:`Hub`.
        """
        data = await self._async_update(
            hub_id, spec.model_dump(mode="json", exclude_none=True)
        )
        return Hub.model_validate(data)

    async def async_capacity(self, hub_id: str) -> HubCapacity:
        """Get current capacity for a hub (async).

        Args:
            hub_id: The hub to inspect.

        Returns:
            Current :class:`HubCapacity`.
        """
        data = await self._async_get(hub_id, path=f"/hubs/{hub_id}/capacity")
        return HubCapacity.model_validate(data)

    async def async_scale(
        self, hub_id: str, *, target_gpu_count: int
    ) -> Hub:
        """Scale a hub to a target GPU count (async).

        Args:
            hub_id: The hub to scale.
            target_gpu_count: Desired number of GPUs.

        Returns:
            The scaling :class:`Hub`.
        """
        data = await self._async_patch(
            hub_id, {"action": "scale", "target_gpu_count": target_gpu_count}
        )
        return Hub.model_validate(data)

    async def async_drain(self, hub_id: str) -> Hub:
        """Drain a hub (gracefully remove all workloads) (async).

        Args:
            hub_id: The hub to drain.

        Returns:
            The draining :class:`Hub`.
        """
        data = await self._async_patch(hub_id, {"action": "drain"})
        return Hub.model_validate(data)

    async def async_delete(self, hub_id: str) -> None:
        """Delete a hub (async).

        Args:
            hub_id: The hub to delete.
        """
        await self._async_delete(hub_id)

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        status: Optional[HubStatus] = None,
        tier: Optional[HubTier] = None,
        region: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> HubList:
        """List hubs with optional filtering (sync)."""
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if status is not None:
            params["status"] = status.value if isinstance(status, HubStatus) else status
        if tier is not None:
            params["tier"] = tier.value if isinstance(tier, HubTier) else tier
        if region is not None:
            params["region"] = region
        if labels:
            for key, value in labels.items():
                params[f"label.{key}"] = value

        data = self._sync_list(params=params)
        return HubList.model_validate(data)

    def get(self, hub_id: str) -> Hub:
        """Retrieve a hub by ID (sync)."""
        data = self._sync_get(hub_id)
        return Hub.model_validate(data)

    def create(self, spec: HubSpec) -> Hub:
        """Create a new hub (sync)."""
        data = self._sync_create(spec.model_dump(mode="json", exclude_none=True))
        return Hub.model_validate(data)

    def update(self, hub_id: str, spec: HubSpec) -> Hub:
        """Update an existing hub (sync)."""
        data = self._sync_update(hub_id, spec.model_dump(mode="json", exclude_none=True))
        return Hub.model_validate(data)

    def capacity(self, hub_id: str) -> HubCapacity:
        """Get current capacity for a hub (sync)."""
        data = self._sync_get(hub_id, path=f"/hubs/{hub_id}/capacity")
        return HubCapacity.model_validate(data)

    def scale(self, hub_id: str, *, target_gpu_count: int) -> Hub:
        """Scale a hub (sync)."""
        data = self._sync_patch(
            hub_id, {"action": "scale", "target_gpu_count": target_gpu_count}
        )
        return Hub.model_validate(data)

    def drain(self, hub_id: str) -> Hub:
        """Drain a hub (sync)."""
        data = self._sync_patch(hub_id, {"action": "drain"})
        return Hub.model_validate(data)

    def delete(self, hub_id: str) -> None:
        """Delete a hub (sync)."""
        self._sync_delete(hub_id)
