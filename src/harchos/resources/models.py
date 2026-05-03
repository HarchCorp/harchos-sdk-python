"""Models (AI models) resource module for the HarchOS SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models.model import (
    Model,
    ModelList,
    ModelSpec,
    ModelStatus,
    ModelTask,
    ModelFramework,
)
from .base import BaseResource


class ModelsResource(BaseResource):
    """Manages AI models in HarchOS.

    Provides both async and sync methods for model CRUD, deployment,
    and discovery.
    """

    _resource_path = "/models"
    _model_class = Model

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_list(
        self,
        *,
        task: Optional[ModelTask] = None,
        framework: Optional[ModelFramework] = None,
        status: Optional[ModelStatus] = None,
        hub_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ModelList:
        """List models with optional filtering (async).

        Args:
            task: Filter by model task.
            framework: Filter by ML framework.
            status: Filter by model status.
            hub_id: Filter by hub.
            labels: Filter by labels.
            page: Page number.
            per_page: Items per page.

        Returns:
            A :class:`ModelList` with matching models.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if task is not None:
            params["task"] = task.value if isinstance(task, ModelTask) else task
        if framework is not None:
            params["framework"] = framework.value if isinstance(framework, ModelFramework) else framework
        if status is not None:
            params["status"] = status.value if isinstance(status, ModelStatus) else status
        if hub_id is not None:
            params["hub_id"] = hub_id
        if labels:
            for key, value in labels.items():
                params[f"label.{key}"] = value

        data = await self._async_list(params=params)
        return ModelList.model_validate(data)

    async def async_get(self, model_id: str) -> Model:
        """Retrieve a model by ID (async).

        Args:
            model_id: The unique model identifier.

        Returns:
            The requested :class:`Model`.
        """
        data = await self._async_get(model_id)
        return Model.model_validate(data)

    async def async_create(self, spec: ModelSpec) -> Model:
        """Register a new model (async).

        Args:
            spec: The model specification.

        Returns:
            The newly created :class:`Model`.
        """
        data = await self._async_create(spec.model_dump(mode="json", exclude_none=True))
        return Model.model_validate(data)

    async def async_update(self, model_id: str, spec: ModelSpec) -> Model:
        """Update an existing model (async).

        Args:
            model_id: The model to update.
            spec: The updated specification.

        Returns:
            The updated :class:`Model`.
        """
        data = await self._async_update(
            model_id, spec.model_dump(mode="json", exclude_none=True)
        )
        return Model.model_validate(data)

    async def async_deploy(self, model_id: str, *, hub_id: Optional[str] = None) -> Model:
        """Deploy a model to a hub (async).

        Args:
            model_id: The model to deploy.
            hub_id: Optional hub to deploy to (uses default if omitted).

        Returns:
            The deploying :class:`Model`.
        """
        payload: Dict[str, Any] = {"action": "deploy"}
        if hub_id:
            payload["hub_id"] = hub_id
        data = await self._async_patch(model_id, payload)
        return Model.model_validate(data)

    async def async_undeploy(self, model_id: str) -> Model:
        """Undeploy a model (async).

        Args:
            model_id: The model to undeploy.

        Returns:
            The undeploying :class:`Model`.
        """
        data = await self._async_patch(model_id, {"action": "undeploy"})
        return Model.model_validate(data)

    async def async_delete(self, model_id: str) -> None:
        """Delete a model (async).

        Args:
            model_id: The model to delete.
        """
        await self._async_delete(model_id)

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        task: Optional[ModelTask] = None,
        framework: Optional[ModelFramework] = None,
        status: Optional[ModelStatus] = None,
        hub_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ModelList:
        """List models with optional filtering (sync)."""
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if task is not None:
            params["task"] = task.value if isinstance(task, ModelTask) else task
        if framework is not None:
            params["framework"] = framework.value if isinstance(framework, ModelFramework) else framework
        if status is not None:
            params["status"] = status.value if isinstance(status, ModelStatus) else status
        if hub_id is not None:
            params["hub_id"] = hub_id
        if labels:
            for key, value in labels.items():
                params[f"label.{key}"] = value

        data = self._sync_list(params=params)
        return ModelList.model_validate(data)

    def get(self, model_id: str) -> Model:
        """Retrieve a model by ID (sync)."""
        data = self._sync_get(model_id)
        return Model.model_validate(data)

    def create(self, spec: ModelSpec) -> Model:
        """Register a new model (sync)."""
        data = self._sync_create(spec.model_dump(mode="json", exclude_none=True))
        return Model.model_validate(data)

    def update(self, model_id: str, spec: ModelSpec) -> Model:
        """Update an existing model (sync)."""
        data = self._sync_update(model_id, spec.model_dump(mode="json", exclude_none=True))
        return Model.model_validate(data)

    def deploy(self, model_id: str, *, hub_id: Optional[str] = None) -> Model:
        """Deploy a model (sync)."""
        payload: Dict[str, Any] = {"action": "deploy"}
        if hub_id:
            payload["hub_id"] = hub_id
        data = self._sync_patch(model_id, payload)
        return Model.model_validate(data)

    def undeploy(self, model_id: str) -> Model:
        """Undeploy a model (sync)."""
        data = self._sync_patch(model_id, {"action": "undeploy"})
        return Model.model_validate(data)

    def delete(self, model_id: str) -> None:
        """Delete a model (sync)."""
        self._sync_delete(model_id)
