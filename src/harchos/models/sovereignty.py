"""Sovereignty models for the HarchOS SDK.

Defines data structures for sovereignty enforcement, data residency
constraints, and carbon-aware scheduling.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from .common import HarchOSBaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SovereigntyLevel(str, Enum):
    """Sovereignty enforcement level."""

    STRICT = "strict"
    MODERATE = "moderate"
    MINIMAL = "minimal"


class DataClassification(str, Enum):
    """Data classification levels for sovereignty enforcement."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""

    GDPR = "gdpr"
    PDPL_MOROCCO = "pdpl_morocco"
    PDPL_ALGERIA = "pdpl_algeria"
    PDPL_TUNISIA = "pdpl_tunisia"
    ISO_27001 = "iso_27001"
    SOC2 = "soc2"


# ---------------------------------------------------------------------------
# Data Residency
# ---------------------------------------------------------------------------

class DataResidencyPolicy(HarchOSBaseModel):
    """Defines where data is allowed to be stored and processed.

    When ``sovereignty`` is ``strict``, the data must remain within
    the specified regions at all times.
    """

    allowed_regions: List[str] = Field(
        ..., min_length=1, description="Regions where data may reside"
    )
    restricted_regions: List[str] = Field(
        default_factory=list, description="Regions where data must NOT reside"
    )
    data_classification: DataClassification = Field(
        default=DataClassification.CONFIDENTIAL,
        description="Classification level of the data",
    )
    encryption_at_rest: bool = Field(
        default=True, description="Require encryption at rest"
    )
    encryption_in_transit: bool = Field(
        default=True, description="Require encryption in transit"
    )
    key_management_region: Optional[str] = Field(
        default=None,
        description="Region where encryption keys must be managed",
    )

    @field_validator("allowed_regions", mode="before")
    @classmethod
    def normalize_regions(cls, v: List[str]) -> List[str]:
        """Normalize region strings."""
        return [r.lower().replace("-", "_").replace(" ", "_") for r in v]

    @model_validator(mode="after")
    def _check_no_overlap(self) -> "DataResidencyPolicy":
        """Ensure allowed and restricted regions don't overlap."""
        overlap = set(self.allowed_regions) & set(self.restricted_regions)
        if overlap:
            raise ValueError(
                f"Regions cannot be both allowed and restricted: {overlap}"
            )
        return self


# ---------------------------------------------------------------------------
# Carbon tracking
# ---------------------------------------------------------------------------

class CarbonMetrics(HarchOSBaseModel):
    """Carbon emission metrics for a resource or operation."""

    co2_grams: float = Field(..., ge=0, description="CO2 emitted in grams")
    energy_kwh: float = Field(..., ge=0, description="Energy consumed in kWh")
    pue: float = Field(..., gt=0, description="Power Usage Effectiveness ratio")
    region_grid_intensity: float = Field(
        ..., ge=0, description="Grid carbon intensity in gCO2/kWh for the region"
    )
    renewable_percentage: float = Field(
        default=0.0, ge=0, le=100, description="Percentage of renewable energy used"
    )
    measured_at: datetime = Field(..., description="When the measurement was taken")


class CarbonBudget(HarchOSBaseModel):
    """Carbon budget allocation for a workload or project."""

    budget_grams: float = Field(..., gt=0, description="Total CO2 budget in grams")
    consumed_grams: float = Field(
        default=0.0, ge=0, description="CO2 consumed so far in grams"
    )
    remaining_grams: float = Field(
        ..., ge=0, description="CO2 remaining in the budget"
    )
    period_start: datetime = Field(..., description="Budget period start")
    period_end: datetime = Field(..., description="Budget period end")
    alert_threshold: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description="Fraction at which to trigger budget alerts",
    )

    @model_validator(mode="after")
    def _check_budget_consistency(self) -> "CarbonBudget":
        """Validate budget arithmetic."""
        expected_remaining = self.budget_grams - self.consumed_grams
        if abs(self.remaining_grams - expected_remaining) > 0.01:
            raise ValueError(
                f"Remaining budget ({self.remaining_grams}) does not match "
                f"budget - consumed ({expected_remaining})"
            )
        return self

    @property
    def utilization(self) -> float:
        """Return budget utilization as a fraction (0..1)."""
        if self.budget_grams <= 0:
            return 1.0
        return min(self.consumed_grams / self.budget_grams, 1.0)

    @property
    def is_over_budget(self) -> bool:
        """Check if the carbon budget has been exceeded."""
        return self.consumed_grams > self.budget_grams

    @property
    def is_alert_triggered(self) -> bool:
        """Check if the alert threshold has been reached."""
        return self.utilization >= self.alert_threshold


# ---------------------------------------------------------------------------
# Sovereignty report
# ---------------------------------------------------------------------------

class SovereigntyReport(HarchOSBaseModel):
    """Comprehensive sovereignty compliance report."""

    resource_id: str = Field(..., description="ID of the assessed resource")
    resource_type: str = Field(..., description="Type of resource assessed")
    sovereignty_level: SovereigntyLevel = Field(..., description="Applied sovereignty level")
    compliant: bool = Field(..., description="Whether the resource is compliant")
    residency_policy: Optional[DataResidencyPolicy] = Field(
        default=None, description="Applied data residency policy"
    )
    carbon_budget: Optional[CarbonBudget] = Field(
        default=None, description="Carbon budget status"
    )
    violations: List[str] = Field(
        default_factory=list, description="List of sovereignty violations found"
    )
    compliance_frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Applicable compliance frameworks"
    )
    assessed_at: datetime = Field(..., description="When the assessment was performed")
