"""Pricing resource — Cost estimation and plan information.

Provides ``harchos.pricing.estimate(...)`` and ``harchos.pricing.plans()``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._types import CostEstimate, PricingPlan


class PricingResource:
    """Synchronous pricing resource.

    Accessed via ``client.pricing``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def estimate(
        self,
        *,
        gpu_count: int = 1,
        gpu_type: str = "a100",
        hours: float = 1.0,
        region: str = "morocco",
        tier: str = "community",
    ) -> CostEstimate:
        """Estimate the cost of a planned deployment.

        Args:
            gpu_count: Number of GPUs.
            gpu_type: GPU type (e.g. ``"a100"``, ``"h100"``).
            hours: Estimated hours of usage.
            region: Target region.
            tier: Target tier (``community``, ``enterprise``, ``sovereign``).

        Returns:
            A :class:`CostEstimate` with detailed cost breakdown.
        """
        body: Dict[str, Any] = {
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "hours": hours,
            "region": region,
            "tier": tier,
        }
        result = self._client.request("POST", "/pricing/estimate", json=body)
        return CostEstimate.model_validate(result)

    def plans(
        self,
        *,
        region: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> List[PricingPlan]:
        """List available pricing plans.

        Args:
            region: Filter by region.
            tier: Filter by tier.

        Returns:
            A list of :class:`PricingPlan` objects.
        """
        params: Dict[str, Any] = {}
        if region is not None:
            params["region"] = region
        if tier is not None:
            params["tier"] = tier

        result = self._client.request("GET", "/pricing/plans", params=params)
        if isinstance(result, dict) and "data" in result:
            return [PricingPlan.model_validate(p) for p in result["data"]]
        if isinstance(result, list):
            return [PricingPlan.model_validate(p) for p in result]
        return []


# ===========================================================================
# Async variant
# ===========================================================================

class AsyncPricingResource:
    """Asynchronous pricing resource.

    Accessed via ``async_client.pricing``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def estimate(
        self,
        *,
        gpu_count: int = 1,
        gpu_type: str = "a100",
        hours: float = 1.0,
        region: str = "morocco",
        tier: str = "community",
    ) -> CostEstimate:
        """Estimate the cost of a planned deployment (async)."""
        body: Dict[str, Any] = {
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "hours": hours,
            "region": region,
            "tier": tier,
        }
        result = await self._client.request("POST", "/pricing/estimate", json=body)
        return CostEstimate.model_validate(result)

    async def plans(
        self,
        *,
        region: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> List[PricingPlan]:
        """List available pricing plans (async)."""
        params: Dict[str, Any] = {}
        if region is not None:
            params["region"] = region
        if tier is not None:
            params["tier"] = tier

        result = await self._client.request("GET", "/pricing/plans", params=params)
        if isinstance(result, dict) and "data" in result:
            return [PricingPlan.model_validate(p) for p in result["data"]]
        if isinstance(result, list):
            return [PricingPlan.model_validate(p) for p in result]
        return []
