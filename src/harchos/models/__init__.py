"""HarchOS SDK Pydantic models package.

Re-exports all model classes for convenient access.
"""

from .common import (
    APIResponse,
    ErrorDetail,
    ErrorResponse,
    HarchOSBaseModel,
    HealthStatus,
    PaginatedResponse,
    PaginationMeta,
    ResourceMetadata,
)
from .energy import (
    EnergyConsumption,
    EnergyEfficiency,
    EnergyReport,
    EnergySource,
    EnergySummary,
    GreenWindow,
)
from .hub import (
    Hub,
    HubCapacity,
    HubList,
    HubSpec,
    HubStatus,
    HubTier,
)
from .model import (
    Model,
    ModelCapabilities,
    ModelFramework,
    ModelList,
    ModelSize,
    ModelSpec,
    ModelStatus,
    ModelTask,
)
from .sovereignty import (
    CarbonBudget,
    CarbonMetrics,
    ComplianceFramework,
    DataClassification,
    DataResidencyPolicy,
    SovereigntyLevel,
    SovereigntyReport,
)
from .workload import (
    ComputePriority,
    ComputeRequirements,
    Workload,
    WorkloadList,
    WorkloadSpec,
    WorkloadStatus,
    WorkloadType,
)

__all__ = [
    # Common
    "APIResponse",
    "ErrorResponse",
    "ErrorDetail",
    "HarchOSBaseModel",
    "HealthStatus",
    "PaginatedResponse",
    "PaginationMeta",
    "ResourceMetadata",
    # Energy
    "EnergyConsumption",
    "EnergyEfficiency",
    "EnergyReport",
    "EnergySource",
    "EnergySummary",
    "GreenWindow",
    # Hub
    "Hub",
    "HubCapacity",
    "HubList",
    "HubSpec",
    "HubStatus",
    "HubTier",
    # Model
    "Model",
    "ModelCapabilities",
    "ModelFramework",
    "ModelList",
    "ModelSize",
    "ModelSpec",
    "ModelStatus",
    "ModelTask",
    # Sovereignty
    "CarbonBudget",
    "CarbonMetrics",
    "ComplianceFramework",
    "DataClassification",
    "DataResidencyPolicy",
    "SovereigntyLevel",
    "SovereigntyReport",
    # Workload
    "ComputePriority",
    "ComputeRequirements",
    "Workload",
    "WorkloadList",
    "WorkloadSpec",
    "WorkloadStatus",
    "WorkloadType",
]
