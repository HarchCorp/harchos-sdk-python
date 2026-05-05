"""Pricing and billing Pydantic models for the HarchOS SDK.

These models mirror the server's ``/v1/pricing/*`` response shapes and
provide a typed interface for Python developers working with billing,
cost estimation, and pricing plans.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from .common import HarchOSBaseModel


# ---------------------------------------------------------------------------
# Pricing Plan
# ---------------------------------------------------------------------------

class PricingPlan(HarchOSBaseModel):
    """A pricing plan for GPU/CPU/storage resources on HarchOS."""

    id: str = Field(..., description="Unique pricing plan identifier")
    name: str = Field(..., description="Human-readable plan name (e.g. 'Morocco Green Compute')")
    gpu_type: str = Field(..., description="GPU type this plan covers (e.g. 'A100', 'H100')")
    price_per_gpu_hour: float = Field(..., ge=0, description="Price per GPU hour")
    price_per_cpu_core_hour: float = Field(..., ge=0, description="Price per CPU core hour")
    price_per_gb_storage_month: float = Field(..., ge=0, description="Price per GB storage per month")
    price_per_gb_memory_hour: float = Field(..., ge=0, description="Price per GB memory hour")
    currency: str = Field("USD", description="ISO 4217 currency code (e.g. 'USD', 'MAD', 'EUR')")
    region: str = Field("morocco", description="Region this plan applies to")
    tier: str = Field("community", description="Plan tier: community, enterprise, sovereign")
    is_default: bool = Field(False, description="Whether this is the default plan for the region")

    @property
    def monthly_gpu_cost(self, hours_per_month: float = 730.0) -> float:
        """Estimate monthly cost for one GPU at this plan's rate."""
        return round(self.price_per_gpu_hour * hours_per_month, 2)


# ---------------------------------------------------------------------------
# Billing Record
# ---------------------------------------------------------------------------

class BillingRecord(HarchOSBaseModel):
    """A billing record for resource usage on HarchOS."""

    id: str = Field(..., description="Unique billing record identifier")
    user_id: str = Field(..., description="User ID this record belongs to")
    workload_id: Optional[str] = Field(None, description="Workload ID if applicable")
    hub_id: Optional[str] = Field(None, description="Hub ID where resources were consumed")
    gpu_hours: float = Field(0.0, ge=0, description="Total GPU hours consumed")
    cpu_core_hours: float = Field(0.0, ge=0, description="Total CPU core hours consumed")
    memory_gb_hours: float = Field(0.0, ge=0, description="Total memory GB-hours consumed")
    storage_gb_months: float = Field(0.0, ge=0, description="Total storage GB-months consumed")
    total_cost: float = Field(0.0, ge=0, description="Total cost for this billing period")
    currency: str = Field("USD", description="Currency code")
    status: str = Field("open", description="Billing status: open, closed, paid, overdue")
    period_start: datetime = Field(..., description="Billing period start")
    period_end: datetime = Field(..., description="Billing period end")

    @property
    def is_paid(self) -> bool:
        """Whether this billing record has been paid."""
        return self.status == "paid"


# ---------------------------------------------------------------------------
# Cost Estimate
# ---------------------------------------------------------------------------

class CostEstimate(HarchOSBaseModel):
    """A cost estimate for a planned workload deployment."""

    gpu_count: int = Field(..., ge=1, description="Number of GPUs requested")
    gpu_type: str = Field(..., description="GPU type (e.g. 'A100', 'H100')")
    hours: float = Field(..., gt=0, description="Estimated hours of usage")
    region: str = Field("morocco", description="Target region")
    tier: str = Field("community", description="Target tier")
    estimated_total: float = Field(..., ge=0, description="Estimated total cost")
    currency: str = Field("USD", description="Currency code")
    breakdown: CostBreakdown = Field(..., description="Detailed cost breakdown")


class CostBreakdown(HarchOSBaseModel):
    """Detailed breakdown of a cost estimate."""

    gpu_cost: float = Field(0.0, ge=0, description="GPU compute cost")
    cpu_cost: float = Field(0.0, ge=0, description="CPU compute cost")
    memory_cost: float = Field(0.0, ge=0, description="Memory cost")
    storage_cost: float = Field(0.0, ge=0, description="Storage cost")
    network_cost: float = Field(0.0, ge=0, description="Network egress cost")
    discount_percentage: float = Field(0.0, ge=0, le=100, description="Any applicable discount")
    subtotal: float = Field(0.0, ge=0, description="Subtotal before discount")
    tax: float = Field(0.0, ge=0, description="Estimated tax")
