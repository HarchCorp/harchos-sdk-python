"""Workloads resource module for the HarchOS SDK."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

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
    management, workload-specific actions like cancellation, and
    long-polling via :meth:`wait` / :meth:`async_wait`.
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
            params["status"] = (
                status.value if isinstance(status, WorkloadStatus) else status
            )
        if workload_type is not None:
            params["type"] = (
                workload_type.value if isinstance(workload_type, WorkloadType)
                else workload_type
            )
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

    async def async_wait(
        self,
        workload_id: str,
        *,
        timeout: float = 3600.0,
        poll_interval: float = 2.0,
        terminal_statuses: Optional[set] = None,
    ) -> Workload:
        """Wait for a workload to reach a terminal state (async).

        Polls the workload at regular intervals until it reaches a
        terminal status or the timeout is exceeded.

        Args:
            workload_id: The workload to wait for.
            timeout: Maximum seconds to wait (default: 1 hour).
            poll_interval: Seconds between polls (default: 2).
            terminal_statuses: Statuses to consider terminal.
                Defaults to ``completed``, ``failed``, ``cancelled``.

        Returns:
            The :class:`Workload` in its terminal state.

        Raises:
            TimeoutError: If the workload doesn't complete within *timeout*.
        """
        if terminal_statuses is None:
            terminal_statuses = {"completed", "failed", "cancelled"}

        start = asyncio.get_event_loop().time()
        while True:
            workload = await self.async_get(workload_id)
            status_val = workload.status.value if isinstance(workload.status, WorkloadStatus) else str(workload.status)
            if status_val in terminal_statuses:
                return workload

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                from ..errors import TimeoutError as HarchOSTimeoutError
                raise HarchOSTimeoutError(
                    f"Workload {workload_id} did not reach terminal state within {timeout}s "
                    f"(current status: {workload.status})"
                )

            await asyncio.sleep(poll_interval)

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
            params["status"] = (
                status.value if isinstance(status, WorkloadStatus) else status
            )
        if workload_type is not None:
            params["type"] = (
                workload_type.value if isinstance(workload_type, WorkloadType)
                else workload_type
            )
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

    def wait(
        self,
        workload_id: str,
        *,
        timeout: float = 3600.0,
        poll_interval: float = 2.0,
        terminal_statuses: Optional[set] = None,
    ) -> Workload:
        """Wait for a workload to reach a terminal state (sync).

        Polls the workload at regular intervals until it reaches a
        terminal status or the timeout is exceeded.

        Args:
            workload_id: The workload to wait for.
            timeout: Maximum seconds to wait (default: 1 hour).
            poll_interval: Seconds between polls (default: 2).
            terminal_statuses: Statuses to consider terminal.
                Defaults to ``completed``, ``failed``, ``cancelled``.

        Returns:
            The :class:`Workload` in its terminal state.

        Raises:
            TimeoutError: If the workload doesn't complete within *timeout*.

        Example::

            client = HarchOSClient(api_key="hsk_...")
            workload = client.workloads.create(spec)
            # Block until the workload finishes (or 10 minutes max)
            workload = client.workloads.wait(workload.metadata.id, timeout=600)
            print(f"Final status: {workload.status}")
        """
        if terminal_statuses is None:
            terminal_statuses = {"completed", "failed", "cancelled"}

        start = time.monotonic()
        while True:
            workload = self.get(workload_id)
            status_val = workload.status.value if isinstance(workload.status, WorkloadStatus) else str(workload.status)
            if status_val in terminal_statuses:
                return workload

            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                from ..errors import TimeoutError as HarchOSTimeoutError
                raise HarchOSTimeoutError(
                    f"Workload {workload_id} did not reach terminal state within {timeout}s "
                    f"(current status: {workload.status})"
                )

            time.sleep(poll_interval)
