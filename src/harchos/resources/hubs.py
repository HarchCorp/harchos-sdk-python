"""Hubs resource — List and inspect sovereign compute hubs.

Provides ``harchos.hubs.list()`` and ``harchos.hubs.get(id)``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .._types import Hub, HubList


class HubsResource:
    """Synchronous hubs resource.

    Accessed via ``client.hubs``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def list(
        self,
        *,
        region: Optional[str] = None,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> HubList:
        """List sovereign compute hubs.

        Args:
            region: Filter by region.
            status: Filter by status (``ready``, ``offline``, etc.).
            tier: Filter by tier (``starter``, ``standard``, ``performance``, ``enterprise``).
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            A :class:`HubList` with hub items.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if region is not None:
            params["region"] = region
        if status is not None:
            params["status"] = status
        if tier is not None:
            params["tier"] = tier

        result = self._client.request("GET", "/hubs", params=params)
        return HubList.model_validate(result)

    def get(self, hub_id: str) -> Hub:
        """Get a hub by ID.

        Args:
            hub_id: The hub identifier.

        Returns:
            A :class:`Hub` object.
        """
        result = self._client.request("GET", f"/hubs/{hub_id}")
        return Hub.model_validate(result)


# ===========================================================================
# Async variant
# ===========================================================================

class AsyncHubsResource:
    """Asynchronous hubs resource.

    Accessed via ``async_client.hubs``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def list(
        self,
        *,
        region: Optional[str] = None,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> HubList:
        """List sovereign compute hubs (async)."""
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if region is not None:
            params["region"] = region
        if status is not None:
            params["status"] = status
        if tier is not None:
            params["tier"] = tier

        result = await self._client.request("GET", "/hubs", params=params)
        return HubList.model_validate(result)

    async def get(self, hub_id: str) -> Hub:
        """Get a hub by ID (async)."""
        result = await self._client.request("GET", f"/hubs/{hub_id}")
        return Hub.model_validate(result)
