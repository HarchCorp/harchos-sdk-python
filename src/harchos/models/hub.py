"""Hub Pydantic models for the HarchOS SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from .common import HarchOSBaseModel, PaginationMeta, ResourceMetadata
from .sovereignty import CarbonMetrics, DataResidencyPolicy, SovereigntyLevel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HubStatus(str, Enum):
    """Status of a HarchOS Hub."""

    CREATING = "creating"
    READY = "ready"
    UPDATING = "updating"
    SCALING = "scaling"
    DRAINING = "draining"
    OFFLINE = "offline"
    ERROR = "error"


class HubTier(str, Enum):
    """Hub performance tiers."""

    STARTER = "starter"
    STANDARD = "standard"
    PERFORMANCE = "performance"
    ENTERPRISE = "enterprise"


# ---------------------------------------------------------------------------
# Capacity
# ---------------------------------------------------------------------------

class HubCapacity(HarchOSBaseModel):
    """Current capacity information for a Hub."""

    total_gpus: int = Field(..., ge=0, description="Total GPUs in the hub")
    available_gpus: int = Field(..., ge=0, description="Currently available GPUs")
    total_cpu_cores: int = Field(..., ge=0, description="Total CPU cores")
    available_cpu_cores: int = Field(..., ge=0, description="Available CPU cores")
    total_memory_gb: float = Field(..., ge=0, description="Total memory in GB")
    available_memory_gb: float = Field(..., ge=0, description="Available memory in GB")
    total_storage_gb: float = Field(..., ge=0, description="Total storage in GB")
    available_storage_gb: float = Field(..., ge=0, description="Available storage in GB")

    @model_validator(mode="after")
    def _check_capacity_sanity(self) -> "HubCapacity":
        """Ensure available capacity doesn't exceed total."""
        if self.available_gpus > self.total_gpus:
            raise ValueError("Available GPUs cannot exceed total GPUs")
        if self.available_cpu_cores > self.total_cpu_cores:
            raise ValueError("Available CPU cores cannot exceed total")
        if self.available_memory_gb > self.total_memory_gb:
            raise ValueError("Available memory cannot exceed total")
        if self.available_storage_gb > self.total_storage_gb:
            raise ValueError("Available storage cannot exceed total")
        return self

    @property
    def gpu_utilization(self) -> float:
        """Return GPU utilization as a fraction (0..1)."""
        if self.total_gpus == 0:
            return 0.0
        return 1.0 - (self.available_gpus / self.total_gpus)


# ---------------------------------------------------------------------------
# Hub models
# ---------------------------------------------------------------------------

class HubSpec(HarchOSBaseModel):
    """Specification for creating or updating a Hub."""

    name: str = Field(..., min_length=1, max_length=128, description="Hub name")
    region: str = Field(..., min_length=1, description="Hub region")
    tier: HubTier = Field(default=HubTier.STANDARD, description="Performance tier")
    sovereignty_level: SovereigntyLevel = Field(
        default=SovereigntyLevel.STRICT, description="Sovereignty enforcement level"
    )
    data_residency: Optional[DataResidencyPolicy] = Field(
        default=None, description="Data residency constraints"
    )
    gpu_types: List[str] = Field(
        default_factory=lambda: ["a100"],
        description="GPU types available in this hub",
    )
    auto_scale: bool = Field(
        default=True, description="Enable auto-scaling"
    )
    min_gpu_count: int = Field(default=0, ge=0, description="Minimum GPU count for auto-scaling")
    max_gpu_count: int = Field(default=8, ge=1, description="Maximum GPU count for auto-scaling")
    carbon_aware_scheduling: bool = Field(
        default=True, description="Enable carbon-aware workload scheduling"
    )
    labels: Dict[str, str] = Field(default_factory=dict, description="Custom labels")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate hub name."""
        v = v.strip()
        if not v:
            raise ValueError("Hub name must not be empty")
        return v

    @field_validator("region", mode="before")
    @classmethod
    def normalize_region(cls, v: str) -> str:
        """Normalize region string."""
        return v.lower().replace("-", "_").replace(" ", "_")

    @model_validator(mode="after")
    def _check_scaling_bounds(self) -> "HubSpec":
        """Ensure min <= max GPU count."""
        if self.min_gpu_count > self.max_gpu_count:
            raise ValueError(
                f"min_gpu_count ({self.min_gpu_count}) cannot exceed "
                f"max_gpu_count ({self.max_gpu_count})"
            )
        return self


class Hub(HarchOSBaseModel):
    """A HarchOS Hub resource."""

    metadata: ResourceMetadata = Field(..., description="Resource metadata")
    spec: HubSpec = Field(..., description="Hub specification")
    status: HubStatus = Field(default=HubStatus.CREATING, description="Current hub status")
    capacity: Optional[HubCapacity] = Field(default=None, description="Current capacity")
    carbon_metrics: Optional[CarbonMetrics] = Field(
        default=None, description="Carbon metrics for the hub"
    )
    endpoint: Optional[str] = Field(
        default=None, description="API endpoint for the hub"
    )
    active_workloads: int = Field(
        default=0, ge=0, description="Number of active workloads"
    )

    @property
    def is_ready(self) -> bool:
        """Check if the hub is ready to accept workloads."""
        return self.status == HubStatus.READY

    def __repr__(self) -> str:
        gpu_info = f" gpus={self.capacity.total_gpus}" if self.capacity else ""
        ci_info = f" ci={self.carbon_metrics.region_grid_intensity}gCO2/kWh" if self.carbon_metrics else ""
        return f"Hub({self.metadata.name!r} region={self.spec.region!r} tier={self.spec.tier!r}{gpu_info}{ci_info})"


class HubList(HarchOSBaseModel):
    """A list of hubs with optional pagination info."""

    items: List[Hub] = Field(default_factory=list, description="Hub items")
    total: int = Field(default=0, ge=0, description="Total count")
    pagination: Optional["PaginationMeta"] = Field(
        default=None, description="Pagination metadata from API"
    )

    @model_validator(mode="after")
    def _sync_total_from_pagination(self) -> "HubList":
        """If total is 0 but pagination.total exists, use pagination.total."""
        if self.total == 0 and self.pagination is not None:
            object.__setattr__(self, "total", self.pagination.total)
        return self

    @property
    def total_gpus(self) -> int:
        """Sum of total_gpus across all hubs."""
        return sum(h.capacity.total_gpus for h in self.items if h.capacity)

    @property
    def available_gpus(self) -> int:
        """Sum of available_gpus across all hubs."""
        return sum(h.capacity.available_gpus for h in self.items if h.capacity)

    @property
    def avg_carbon_intensity(self) -> float:
        """Average carbon intensity across all hubs (gCO2/kWh)."""
        intensities = [
            h.carbon_metrics.region_grid_intensity
            for h in self.items
            if h.carbon_metrics and h.carbon_metrics.region_grid_intensity
        ]
        return sum(intensities) / len(intensities) if intensities else 0.0

    @property
    def avg_renewable_percentage(self) -> float:
        """Average renewable percentage across all hubs."""
        renewables = [
            h.carbon_metrics.renewable_percentage
            for h in self.items
            if h.carbon_metrics and h.carbon_metrics.renewable_percentage
        ]
        return sum(renewables) / len(renewables) if renewables else 0.0

    def to_dataframe(self) -> Any:
        """Convert hub list to a pandas DataFrame.

        Requires the 'pandas' extra: pip install harchos[pandas]

        Raises:
            ImportError: If pandas is not installed
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install it with: pip install harchos[pandas]"
            ) from None
        return pd.DataFrame([item.model_dump() for item in self.items])

    def __repr__(self) -> str:
        return f"HubList({len(self.items)} hubs, total_gpus={self.total_gpus}, avg_ci={self.avg_carbon_intensity:.0f}gCO2/kWh)"
