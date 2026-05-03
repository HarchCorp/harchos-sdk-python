"""HarchOS SDK - The Official Python SDK for HarchOS.

HarchOS is the Operating System for Sovereign AI Infrastructure.
This SDK provides both sync and async access to the HarchOS API
with sovereign defaults: region="morocco", sovereignty="strict",
carbon_aware=True.

Example::

    from harchos import HarchOSClient

    client = HarchOSClient(api_key="hsk_...")
    with client:
        workloads = client.workloads.list()

    # Or async
    async with HarchOSClient(api_key="hsk_...") as client:
        workloads = await client.workloads.async_list()
"""

from .auth import Authenticator
from .client import HarchOSClient
from .config import HarchOSConfig, Profile
from .errors import (
    APIKeyExpiredError,
    AuthenticationError,
    BadRequestError,
    CarbonBudgetExceededError,
    ConflictError,
    ConnectionError,
    DataResidencyError,
    ForbiddenError,
    HarchOSError,
    InternalServerError,
    InvalidAPIKeyError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    SovereigntyError,
    TimeoutError,
    UnauthorizedError,
    ValidationError,
)
from .models import (
    CarbonBudget,
    CarbonMetrics,
    ComputePriority,
    ComputeRequirements,
    DataClassification,
    DataResidencyPolicy,
    EnergyConsumption,
    EnergyEfficiency,
    EnergyReport,
    EnergySource,
    EnergySummary,
    GreenWindow,
    Hub,
    HubCapacity,
    HubList,
    HubSpec,
    HubStatus,
    HubTier,
    Model,
    ModelCapabilities,
    ModelFramework,
    ModelList,
    ModelSize,
    ModelSpec,
    ModelStatus,
    ModelTask,
    SovereigntyLevel,
    SovereigntyReport,
    Workload,
    WorkloadList,
    WorkloadSpec,
    WorkloadStatus,
    WorkloadType,
)
from .resources import EnergyResource, HubsResource, ModelsResource, WorkloadsResource

__version__ = "0.1.0"
__author__ = "VitalCheffe"

__all__ = [
    # Client
    "HarchOSClient",
    # Auth
    "Authenticator",
    # Config
    "HarchOSConfig",
    "Profile",
    # Errors
    "APIKeyExpiredError",
    "AuthenticationError",
    "BadRequestError",
    "CarbonBudgetExceededError",
    "ConflictError",
    "ConnectionError",
    "DataResidencyError",
    "ForbiddenError",
    "HarchOSError",
    "InternalServerError",
    "InvalidAPIKeyError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServiceUnavailableError",
    "SovereigntyError",
    "TimeoutError",
    "UnauthorizedError",
    "ValidationError",
    # Models
    "CarbonBudget",
    "CarbonMetrics",
    "ComputePriority",
    "ComputeRequirements",
    "DataClassification",
    "DataResidencyPolicy",
    "EnergyConsumption",
    "EnergyEfficiency",
    "EnergyReport",
    "EnergySource",
    "EnergySummary",
    "GreenWindow",
    "Hub",
    "HubCapacity",
    "HubList",
    "HubSpec",
    "HubStatus",
    "HubTier",
    "Model",
    "ModelCapabilities",
    "ModelFramework",
    "ModelList",
    "ModelSize",
    "ModelSpec",
    "ModelStatus",
    "ModelTask",
    "SovereigntyLevel",
    "SovereigntyReport",
    "Workload",
    "WorkloadList",
    "WorkloadSpec",
    "WorkloadStatus",
    "WorkloadType",
    # Resources
    "EnergyResource",
    "HubsResource",
    "ModelsResource",
    "WorkloadsResource",
]
