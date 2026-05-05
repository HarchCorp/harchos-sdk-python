"""Pricing resource module for the HarchOS SDK.

Provides both async and sync methods for listing pricing plans,
retrieving billing records, and estimating deployment costs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.pricing import (
    BillingRecord,
    CostBreakdown,
    CostEstimate,
    PricingPlan,
)
from .base import BaseResource


class PricingResource(BaseResource):
    """Manages pricing plans, billing, and cost estimation.

    Use this resource to:

    * List and retrieve pricing plans
    * Estimate costs before deploying workloads
    * View billing records and usage history

    Usage::

        client = HarchOSClient(api_key="hsk_...")

        # List pricing plans
        plans = client.pricing.list_plans()

        # Estimate cost for a deployment
        estimate = client.pricing.estimate_cost(
            gpu_count=8,
            gpu_type="H100",
            hours=24,
            region="morocco",
        )
        print(f"Estimated total: ${estimate.estimated_total} {estimate.currency}")
    """

    _resource_path = "/pricing"

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_list_plans(
        self,
        *,
        region: Optional[str] = None,
        tier: Optional[str] = None,
        gpu_type: Optional[str] = None,
    ) -> List[PricingPlan]:
        """List available pricing plans (async).

        Args:
            region: Filter by region (e.g. 'morocco').
            tier: Filter by tier (community, enterprise, sovereign).
            gpu_type: Filter by GPU type (e.g. 'A100', 'H100').

        Returns:
            A list of :class:`PricingPlan` objects.
        """
        params: Dict[str, Any] = {}
        if region is not None:
            params["region"] = region
        if tier is not None:
            params["tier"] = tier
        if gpu_type is not None:
            params["gpu_type"] = gpu_type

        response = await self._transport.async_get("/pricing/plans", params=params or None)
        data = response.json()
        if isinstance(data, list):
            return [PricingPlan.model_validate(p) for p in data]
        items = data.get("items", data.get("plans", []))
        return [PricingPlan.model_validate(p) for p in items]

    async def async_get_plan(self, plan_id: str) -> PricingPlan:
        """Get a specific pricing plan by ID (async).

        Args:
            plan_id: The pricing plan identifier.

        Returns:
            A :class:`PricingPlan` object.
        """
        data = await self._async_get(plan_id, path=f"/pricing/plans/{plan_id}")
        return PricingPlan.model_validate(data)

    async def async_estimate_cost(
        self,
        *,
        gpu_count: int,
        gpu_type: str,
        hours: float,
        region: Optional[str] = None,
        tier: Optional[str] = None,
        cpu_cores: Optional[int] = None,
        memory_gb: Optional[float] = None,
        storage_gb: Optional[float] = None,
    ) -> CostEstimate:
        """Estimate the cost of a deployment (async).

        Args:
            gpu_count: Number of GPUs.
            gpu_type: GPU type (e.g. 'A100', 'H100').
            hours: Estimated hours of usage.
            region: Target region.
            tier: Target tier.
            cpu_cores: CPU cores needed.
            memory_gb: Memory in GB needed.
            storage_gb: Storage in GB needed.

        Returns:
            A :class:`CostEstimate` with total and breakdown.
        """
        payload: Dict[str, Any] = {
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "hours": hours,
        }
        if region is not None:
            payload["region"] = region
        if tier is not None:
            payload["tier"] = tier
        if cpu_cores is not None:
            payload["cpu_cores"] = cpu_cores
        if memory_gb is not None:
            payload["memory_gb"] = memory_gb
        if storage_gb is not None:
            payload["storage_gb"] = storage_gb

        data = await self._async_create(payload, path="/pricing/estimate")
        return CostEstimate.model_validate(data)

    async def async_list_billing_records(
        self,
        *,
        status: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[BillingRecord]:
        """List billing records (async).

        Args:
            status: Filter by status (open, closed, paid, overdue).
            period_start: Filter records from this date.
            period_end: Filter records to this date.
            limit: Maximum number of records to return.

        Returns:
            A list of :class:`BillingRecord` objects.
        """
        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if period_start is not None:
            params["period_start"] = period_start.isoformat()
        if period_end is not None:
            params["period_end"] = period_end.isoformat()
        if limit is not None:
            params["limit"] = limit

        response = await self._transport.async_get("/pricing/billing", params=params or None)
        data = response.json()
        if isinstance(data, list):
            return [BillingRecord.model_validate(r) for r in data]
        items = data.get("items", data.get("records", []))
        return [BillingRecord.model_validate(r) for r in items]

    async def async_get_billing_record(self, record_id: str) -> BillingRecord:
        """Get a specific billing record by ID (async).

        Args:
            record_id: The billing record identifier.

        Returns:
            A :class:`BillingRecord` object.
        """
        data = await self._async_get(record_id, path=f"/pricing/billing/{record_id}")
        return BillingRecord.model_validate(data)

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def list_plans(
        self,
        *,
        region: Optional[str] = None,
        tier: Optional[str] = None,
        gpu_type: Optional[str] = None,
    ) -> List[PricingPlan]:
        """List available pricing plans (sync).

        Args:
            region: Filter by region (e.g. 'morocco').
            tier: Filter by tier (community, enterprise, sovereign).
            gpu_type: Filter by GPU type (e.g. 'A100', 'H100').

        Returns:
            A list of :class:`PricingPlan` objects.
        """
        params: Dict[str, Any] = {}
        if region is not None:
            params["region"] = region
        if tier is not None:
            params["tier"] = tier
        if gpu_type is not None:
            params["gpu_type"] = gpu_type

        response = self._transport.sync_get("/pricing/plans", params=params or None)
        data = response.json()
        if isinstance(data, list):
            return [PricingPlan.model_validate(p) for p in data]
        items = data.get("items", data.get("plans", []))
        return [PricingPlan.model_validate(p) for p in items]

    def get_plan(self, plan_id: str) -> PricingPlan:
        """Get a specific pricing plan by ID (sync).

        Args:
            plan_id: The pricing plan identifier.

        Returns:
            A :class:`PricingPlan` object.
        """
        data = self._sync_get(plan_id, path=f"/pricing/plans/{plan_id}")
        return PricingPlan.model_validate(data)

    def estimate_cost(
        self,
        *,
        gpu_count: int,
        gpu_type: str,
        hours: float,
        region: Optional[str] = None,
        tier: Optional[str] = None,
        cpu_cores: Optional[int] = None,
        memory_gb: Optional[float] = None,
        storage_gb: Optional[float] = None,
    ) -> CostEstimate:
        """Estimate the cost of a deployment (sync).

        Args:
            gpu_count: Number of GPUs.
            gpu_type: GPU type (e.g. 'A100', 'H100').
            hours: Estimated hours of usage.
            region: Target region.
            tier: Target tier.
            cpu_cores: CPU cores needed.
            memory_gb: Memory in GB needed.
            storage_gb: Storage in GB needed.

        Returns:
            A :class:`CostEstimate` with total and breakdown.
        """
        payload: Dict[str, Any] = {
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "hours": hours,
        }
        if region is not None:
            payload["region"] = region
        if tier is not None:
            payload["tier"] = tier
        if cpu_cores is not None:
            payload["cpu_cores"] = cpu_cores
        if memory_gb is not None:
            payload["memory_gb"] = memory_gb
        if storage_gb is not None:
            payload["storage_gb"] = storage_gb

        data = self._sync_create(payload, path="/pricing/estimate")
        return CostEstimate.model_validate(data)

    def list_billing_records(
        self,
        *,
        status: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[BillingRecord]:
        """List billing records (sync).

        Args:
            status: Filter by status (open, closed, paid, overdue).
            period_start: Filter records from this date.
            period_end: Filter records to this date.
            limit: Maximum number of records to return.

        Returns:
            A list of :class:`BillingRecord` objects.
        """
        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if period_start is not None:
            params["period_start"] = period_start.isoformat()
        if period_end is not None:
            params["period_end"] = period_end.isoformat()
        if limit is not None:
            params["limit"] = limit

        response = self._transport.sync_get("/pricing/billing", params=params or None)
        data = response.json()
        if isinstance(data, list):
            return [BillingRecord.model_validate(r) for r in data]
        items = data.get("items", data.get("records", []))
        return [BillingRecord.model_validate(r) for r in items]

    def get_billing_record(self, record_id: str) -> BillingRecord:
        """Get a specific billing record by ID (sync).

        Args:
            record_id: The billing record identifier.

        Returns:
            A :class:`BillingRecord` object.
        """
        data = self._sync_get(record_id, path=f"/pricing/billing/{record_id}")
        return BillingRecord.model_validate(data)
