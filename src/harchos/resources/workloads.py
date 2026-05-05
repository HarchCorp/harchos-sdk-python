"""Workloads resource — CRUD operations for AI workloads.

Provides ``harchos.workloads.create(...)``, ``.list()``, ``.get(id)``,
``.update(id, ...)``, and ``.delete(id)``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._types import Workload, WorkloadList, WorkloadSpec


class WorkloadsResource:
    """Synchronous workloads resource.

    Accessed via ``client.workloads``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        name: str,
        type: str = "training",
        model_id: Optional[str] = None,
        hub_id: Optional[str] = None,
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        cpu_cores: int = 1,
        memory_gb: float = 1.0,
        priority: str = "normal",
        image: Optional[str] = None,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        carbon_budget_grams: Optional[float] = None,
        max_duration_seconds: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Workload:
        """Create a new workload.

        Args:
            name: Workload name.
            type: Workload type (``training``, ``inference``, ``fine_tuning``, etc.).
            model_id: Model ID to use.
            hub_id: Target hub ID.
            gpu_count: Number of GPUs required.
            gpu_type: GPU type (e.g. ``"a100"``, ``"h100"``).
            cpu_cores: CPU cores required.
            memory_gb: Memory in GB.
            priority: Scheduling priority (``low``, ``normal``, ``high``, ``critical``).
            image: Container image.
            command: Command and arguments.
            env: Environment variables.
            carbon_budget_grams: Maximum CO2 budget in grams.
            max_duration_seconds: Maximum runtime in seconds.
            labels: Custom labels.
            **kwargs: Additional fields.

        Returns:
            A :class:`Workload` object.
        """
        body: Dict[str, Any] = {
            "name": name,
            "type": type,
            "gpu_count": gpu_count,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "priority": priority,
        }
        if model_id is not None:
            body["model_id"] = model_id
        if hub_id is not None:
            body["hub_id"] = hub_id
        if gpu_type is not None:
            body["gpu_type"] = gpu_type
        if image is not None:
            body["image"] = image
        if command is not None:
            body["command"] = command
        if env is not None:
            body["env"] = env
        if carbon_budget_grams is not None:
            body["carbon_budget_grams"] = carbon_budget_grams
        if max_duration_seconds is not None:
            body["max_duration_seconds"] = max_duration_seconds
        if labels is not None:
            body["labels"] = labels
        body.update(kwargs)

        result = self._client.request("POST", "/workloads", json=body)
        return Workload.model_validate(result)

    def list(
        self,
        *,
        status: Optional[str] = None,
        hub_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> WorkloadList:
        """List workloads.

        Args:
            status: Filter by status (``running``, ``pending``, ``completed``, etc.).
            hub_id: Filter by hub ID.
            page: Page number (1-indexed).
            per_page: Items per page (max 100).

        Returns:
            A :class:`WorkloadList` with workload items.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if status is not None:
            params["status"] = status
        if hub_id is not None:
            params["hub_id"] = hub_id

        result = self._client.request("GET", "/workloads", params=params)
        return WorkloadList.model_validate(result)

    def get(self, workload_id: str) -> Workload:
        """Get a workload by ID.

        Args:
            workload_id: The workload identifier.

        Returns:
            A :class:`Workload` object.
        """
        result = self._client.request("GET", f"/workloads/{workload_id}")
        return Workload.model_validate(result)

    def update(
        self,
        workload_id: str,
        *,
        name: Optional[str] = None,
        status: Optional[str] = None,
        hub_id: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Workload:
        """Update an existing workload.

        Args:
            workload_id: The workload identifier.
            name: New workload name.
            status: New status.
            hub_id: New hub assignment.
            priority: New scheduling priority.
            labels: Updated labels.
            **kwargs: Additional fields.

        Returns:
            Updated :class:`Workload` object.
        """
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if status is not None:
            body["status"] = status
        if hub_id is not None:
            body["hub_id"] = hub_id
        if priority is not None:
            body["priority"] = priority
        if labels is not None:
            body["labels"] = labels
        body.update(kwargs)

        result = self._client.request(
            "PATCH", f"/workloads/{workload_id}", json=body,
        )
        return Workload.model_validate(result)

    def delete(self, workload_id: str) -> Dict[str, Any]:
        """Delete a workload.

        Args:
            workload_id: The workload identifier.

        Returns:
            Confirmation dict from the API.
        """
        return self._client.request("DELETE", f"/workloads/{workload_id}")


# ===========================================================================
# Async variant
# ===========================================================================

class AsyncWorkloadsResource:
    """Asynchronous workloads resource.

    Accessed via ``async_client.workloads``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        name: str,
        type: str = "training",
        model_id: Optional[str] = None,
        hub_id: Optional[str] = None,
        gpu_count: int = 1,
        gpu_type: Optional[str] = None,
        cpu_cores: int = 1,
        memory_gb: float = 1.0,
        priority: str = "normal",
        image: Optional[str] = None,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        carbon_budget_grams: Optional[float] = None,
        max_duration_seconds: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Workload:
        """Create a new workload (async)."""
        body: Dict[str, Any] = {
            "name": name,
            "type": type,
            "gpu_count": gpu_count,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "priority": priority,
        }
        if model_id is not None:
            body["model_id"] = model_id
        if hub_id is not None:
            body["hub_id"] = hub_id
        if gpu_type is not None:
            body["gpu_type"] = gpu_type
        if image is not None:
            body["image"] = image
        if command is not None:
            body["command"] = command
        if env is not None:
            body["env"] = env
        if carbon_budget_grams is not None:
            body["carbon_budget_grams"] = carbon_budget_grams
        if max_duration_seconds is not None:
            body["max_duration_seconds"] = max_duration_seconds
        if labels is not None:
            body["labels"] = labels
        body.update(kwargs)

        result = await self._client.request("POST", "/workloads", json=body)
        return Workload.model_validate(result)

    async def list(
        self,
        *,
        status: Optional[str] = None,
        hub_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> WorkloadList:
        """List workloads (async)."""
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if status is not None:
            params["status"] = status
        if hub_id is not None:
            params["hub_id"] = hub_id

        result = await self._client.request("GET", "/workloads", params=params)
        return WorkloadList.model_validate(result)

    async def get(self, workload_id: str) -> Workload:
        """Get a workload by ID (async)."""
        result = await self._client.request("GET", f"/workloads/{workload_id}")
        return Workload.model_validate(result)

    async def update(
        self,
        workload_id: str,
        *,
        name: Optional[str] = None,
        status: Optional[str] = None,
        hub_id: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Workload:
        """Update an existing workload (async)."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if status is not None:
            body["status"] = status
        if hub_id is not None:
            body["hub_id"] = hub_id
        if priority is not None:
            body["priority"] = priority
        if labels is not None:
            body["labels"] = labels
        body.update(kwargs)

        result = await self._client.request(
            "PATCH", f"/workloads/{workload_id}", json=body,
        )
        return Workload.model_validate(result)

    async def delete(self, workload_id: str) -> Dict[str, Any]:
        """Delete a workload (async)."""
        return await self._client.request("DELETE", f"/workloads/{workload_id}")
