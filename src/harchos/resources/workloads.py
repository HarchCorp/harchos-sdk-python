"""Workloads resource module for the HarchOS SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models.workload import (
    Workload,
    WorkloadList,
    WorkloadSpec,
    WorkloadStatus,
    WorkloadType,
)
from .base import BaseResource


class WorkloadsResource(BaseResource):
    """Manages HarchOS workloads – the primary compute abstraction.

    Provides both async and sync methods for CRUD operations, status
    management, and workload-specific actions like cancellation.
    """

    _resource_path = "/workloads"
    _model_class = Workload

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_list(
        self,
        *,
        status: Optional[WorkloadStatus] = None,
        workload_type: Optional[WorkloadType] = None,
        hub_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> WorkloadList:
        """List workloads with optional filtering (async).

        Args:
            status: Filter by workload status.
            workload_type: Filter by workload type.
            hub_id: Filter by hub.
            labels: Filter by label key-value pairs.
            page: Page number (1-indexed).
            per_page: Items per page (max 100).

        Returns:
            A :class:`WorkloadList` containing matching workloads.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if status is not None:
            params["status"] = status.value if isinstance(status, WorkloadStatus) else status
        if workload_type is not None:
            params["type"] = workload_type.value if isinstance(workload_type, WorkloadType) else workload_type
        if hub_id is not None:
            params["hub_id"] = hub_id
        if labels:
            for key, value in labels.items():
                params[f"label.{key}"] = value

        data = await self._async_list(params=params)
        return WorkloadList.model_validate(data)

    async def async_get(self, workload_id: str) -> Workload:
        """Retrieve a workload by ID (async).

        Args:
            workload_id: The unique workload identifier.

        Returns:
            The requested :class:`Workload`.

        Raises:
            NotFoundError: If the workload does not exist.
        """
        data = await self._async_get(workload_id)
        return Workload.model_validate(data)

    async def async_create(self, spec: WorkloadSpec) -> Workload:
        """Create a new workload (async).

        Args:
            spec: The workload specification.

        Returns:
            The newly created :class:`Workload`.
        """
        data = await self._async_create(spec.model_dump(mode="json", exclude_none=True))
        return Workload.model_validate(data)

    async def async_update(self, workload_id: str, spec: WorkloadSpec) -> Workload:
        """Update an existing workload (async).

        Args:
            workload_id: The workload to update.
            spec: The updated specification.

        Returns:
            The updated :class:`Workload`.
        """
        data = await self._async_update(
            workload_id, spec.model_dump(mode="json", exclude_none=True)
        )
        return Workload.model_validate(data)

    async def async_cancel(self, workload_id: str) -> Workload:
        """Cancel a running workload (async).

        Args:
            workload_id: The workload to cancel.

        Returns:
            The updated :class:`Workload` with cancelled status.
        """
        data = await self._async_patch(workload_id, {"status": "cancelled"})
        return Workload.model_validate(data)

    async def async_pause(self, workload_id: str) -> Workload:
        """Pause a running workload (async).

        Args:
            workload_id: The workload to pause.

        Returns:
            The paused :class:`Workload`.
        """
        data = await self._async_patch(workload_id, {"status": "paused"})
        return Workload.model_validate(data)

    async def async_resume(self, workload_id: str) -> Workload:
        """Resume a paused workload (async).

        Args:
            workload_id: The workload to resume.

        Returns:
            The resumed :class:`Workload`.
        """
        data = await self._async_patch(workload_id, {"status": "running"})
        return Workload.model_validate(data)

    async def async_delete(self, workload_id: str) -> None:
        """Delete a workload (async).

        Args:
            workload_id: The workload to delete.
        """
        await self._async_delete(workload_id)

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        status: Optional[WorkloadStatus] = None,
        workload_type: Optional[WorkloadType] = None,
        hub_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> WorkloadList:
        """List workloads with optional filtering (sync)."""
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if status is not None:
            params["status"] = status.value if isinstance(status, WorkloadStatus) else status
        if workload_type is not None:
            params["type"] = workload_type.value if isinstance(workload_type, WorkloadType) else workload_type
        if hub_id is not None:
            params["hub_id"] = hub_id
        if labels:
            for key, value in labels.items():
                params[f"label.{key}"] = value

        data = self._sync_list(params=params)
        return WorkloadList.model_validate(data)

    def get(self, workload_id: str) -> Workload:
        """Retrieve a workload by ID (sync)."""
        data = self._sync_get(workload_id)
        return Workload.model_validate(data)

    def create(self, spec: WorkloadSpec) -> Workload:
        """Create a new workload (sync)."""
        data = self._sync_create(spec.model_dump(mode="json", exclude_none=True))
        return Workload.model_validate(data)

    def update(self, workload_id: str, spec: WorkloadSpec) -> Workload:
        """Update an existing workload (sync)."""
        data = self._sync_update(workload_id, spec.model_dump(mode="json", exclude_none=True))
        return Workload.model_validate(data)

    def cancel(self, workload_id: str) -> Workload:
        """Cancel a running workload (sync)."""
        data = self._sync_patch(workload_id, {"status": "cancelled"})
        return Workload.model_validate(data)

    def pause(self, workload_id: str) -> Workload:
        """Pause a running workload (sync)."""
        data = self._sync_patch(workload_id, {"status": "paused"})
        return Workload.model_validate(data)

    def resume(self, workload_id: str) -> Workload:
        """Resume a paused workload (sync)."""
        data = self._sync_patch(workload_id, {"status": "running"})
        return Workload.model_validate(data)

    def delete(self, workload_id: str) -> None:
        """Delete a workload (sync)."""
        self._sync_delete(workload_id)
