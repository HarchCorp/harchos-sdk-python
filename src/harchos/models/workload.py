"""Workload Pydantic models for the HarchOS SDK."""

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

class WorkloadStatus(str, Enum):
    """Possible states of a HarchOS workload."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkloadType(str, Enum):
    """Types of AI workloads supported by HarchOS."""

    TRAINING = "training"
    INFERENCE = "inference"
    FINE_TUNING = "fine_tuning"
    EVALUATION = "evaluation"
    DATA_PIPELINE = "data_pipeline"
    BATCH = "batch"


class ComputePriority(str, Enum):
    """Compute priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Resource requirements
# ---------------------------------------------------------------------------

class ComputeRequirements(HarchOSBaseModel):
    """Compute resource requirements for a workload."""

    gpu_count: int = Field(default=0, ge=0, description="Number of GPUs required")
    gpu_type: Optional[str] = Field(default=None, description="GPU type (e.g., 'a100', 'h100')")
    cpu_cores: int = Field(default=1, ge=1, description="Number of CPU cores required")
    memory_gb: float = Field(default=1.0, gt=0, description="Memory required in GB")
    storage_gb: float = Field(default=10.0, gt=0, description="Storage required in GB")
    ephemeral_storage_gb: Optional[float] = Field(
        default=None, gt=0, description="Ephemeral storage in GB"
    )

    @field_validator("gpu_type", mode="before")
    @classmethod
    def normalize_gpu_type(cls, v: Optional[str]) -> Optional[str]:
        """Normalize GPU type to lowercase."""
        return v.lower() if v else v


# ---------------------------------------------------------------------------
# Workload models
# ---------------------------------------------------------------------------

class WorkloadSpec(HarchOSBaseModel):
    """Specification for creating or updating a workload."""

    name: str = Field(..., min_length=1, max_length=128, description="Workload name")
    type: WorkloadType = Field(..., description="Workload type")
    model_id: Optional[str] = Field(default=None, description="ID of the model to use")
    hub_id: Optional[str] = Field(default=None, description="ID of the hub to run on")
    compute: ComputeRequirements = Field(
        default_factory=ComputeRequirements, description="Compute requirements"
    )
    priority: ComputePriority = Field(
        default=ComputePriority.NORMAL, description="Scheduling priority"
    )
    image: Optional[str] = Field(default=None, description="Container image to run")
    command: Optional[List[str]] = Field(
        default=None, description="Command and arguments"
    )
    env: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    sovereignty_level: SovereigntyLevel = Field(
        default=SovereigntyLevel.STRICT, description="Sovereignty enforcement level"
    )
    data_residency: Optional[DataResidencyPolicy] = Field(
        default=None, description="Data residency constraints"
    )
    carbon_budget_grams: Optional[float] = Field(
        default=None, gt=0, description="Maximum CO2 budget in grams"
    )
    max_duration_seconds: Optional[int] = Field(
        default=None, gt=0, description="Maximum runtime in seconds"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict, description="Custom labels"
    )
    auto_restart: bool = Field(
        default=False, description="Automatically restart on failure"
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workload name format."""
        v = v.strip()
        if not v:
            raise ValueError("Workload name must not be empty or whitespace")
        return v


class Workload(HarchOSBaseModel):
    """A HarchOS workload resource."""

    metadata: ResourceMetadata = Field(..., description="Resource metadata")
    spec: WorkloadSpec = Field(..., description="Workload specification")
    status: WorkloadStatus = Field(
        default=WorkloadStatus.PENDING, description="Current workload status"
    )
    hub_id: Optional[str] = Field(
        default=None, description="Hub where the workload is running"
    )
    carbon_metrics: Optional[CarbonMetrics] = Field(
        default=None, description="Carbon emission metrics"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="When the workload started running"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When the workload completed"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if the workload failed"
    )
    retry_count: int = Field(
        default=0, ge=0, description="Number of times the workload has been retried"
    )

    @property
    def is_terminal(self) -> bool:
        """Check if the workload is in a terminal state."""
        return self.status in {
            WorkloadStatus.COMPLETED,
            WorkloadStatus.FAILED,
            WorkloadStatus.CANCELLED,
        }

    @property
    def duration_seconds(self) -> Optional[float]:
        """Return workload duration in seconds (if started)."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()


class WorkloadList(HarchOSBaseModel):
    """A list of workloads with optional pagination info."""

    items: List[Workload] = Field(default_factory=list, description="Workload items")
    total: int = Field(default=0, ge=0, description="Total count")
