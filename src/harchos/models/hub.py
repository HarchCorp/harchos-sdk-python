"""Hub Pydantic models for the HarchOS SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from .common import HarchOSBaseModel, ResourceMetadata
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


class HubList(HarchOSBaseModel):
    """A list of hubs with optional pagination info."""

    items: List[Hub] = Field(default_factory=list, description="Hub items")
    total: int = Field(default=0, ge=0, description="Total count")
