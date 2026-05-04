"""Base resource class for HarchOS API resources.

Provides common CRUD operations and pagination support.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type, TypeVar

from .._http import HttpTransport

T = TypeVar("T")


class BaseResource:
    """Base class for all HarchOS resource modules.

    Subclasses should set ``_resource_path`` and ``_model_class``
    to enable the generic CRUD methods.
    """

    _resource_path: str = ""
    _model_class: Optional[Type[Any]] = None

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    # ------------------------------------------------------------------
    # Async CRUD
    # ------------------------------------------------------------------

    async def _async_list(
        self,
        *,
        params: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List resources (async)."""
        target = path or self._resource_path
        response = await self._transport.async_get(target, params=params)
        return response.json()

    async def _async_get(
        self,
        resource_id: str,
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a single resource by ID (async)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = await self._transport.async_get(target)
        return response.json()

    async def _async_create(
        self,
        data: Dict[str, Any],
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new resource (async)."""
        target = path or self._resource_path
        response = await self._transport.async_post(target, json=data)
        return response.json()

    async def _async_update(
        self,
        resource_id: str,
        data: Dict[str, Any],
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing resource (async)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = await self._transport.async_put(target, json=data)
        return response.json()

    async def _async_patch(
        self,
        resource_id: str,
        data: Dict[str, Any],
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Partially update a resource (async)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = await self._transport.async_patch(target, json=data)
        return response.json()

    async def _async_delete(
        self,
        resource_id: str,
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete a resource (async)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = await self._transport.async_delete(target)
        return response.json()

    # ------------------------------------------------------------------
    # Sync CRUD
    # ------------------------------------------------------------------

    def _sync_list(
        self,
        *,
        params: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List resources (sync)."""
        target = path or self._resource_path
        response = self._transport.sync_get(target, params=params)
        return response.json()

    def _sync_get(
        self,
        resource_id: str,
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a single resource by ID (sync)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = self._transport.sync_get(target)
        return response.json()

    def _sync_create(
        self,
        data: Dict[str, Any],
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new resource (sync)."""
        target = path or self._resource_path
        response = self._transport.sync_post(target, json=data)
        return response.json()

    def _sync_update(
        self,
        resource_id: str,
        data: Dict[str, Any],
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing resource (sync)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = self._transport.sync_put(target, json=data)
        return response.json()

    def _sync_patch(
        self,
        resource_id: str,
        data: Dict[str, Any],
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Partially update a resource (sync)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = self._transport.sync_patch(target, json=data)
        return response.json()

    def _sync_delete(
        self,
        resource_id: str,
        *,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete a resource (sync)."""
        target = path or f"{self._resource_path}/{resource_id}"
        response = self._transport.sync_delete(target)
        return response.json()
