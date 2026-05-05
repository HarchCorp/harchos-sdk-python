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

from ._logging import configure_logging, get_logger
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
    BillingRecord,
    CarbonAction,
    CarbonBudget,
    CarbonDashboard,
    CarbonDataSource,
    CarbonMetrics,
    CarbonForecast,
    CarbonForecastPoint,
    CarbonIntensityZone,
    CarbonIntensityZoneList,
    CarbonOptimalHub,
    CarbonOptimizeResult,
    ComputePriority,
    ComputeRequirements,
    CostBreakdown,
    CostEstimate,
    DataClassification,
    DataResidencyPolicy,
    DetailedHealth,
    EnergyConsumption,
    EnergyEfficiency,
    EnergyReport,
    EnergySource,
    EnergySummary,
    FuelMixEntry,
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
    PlatformMetrics,
    PricingPlan,
    Region,
    SovereigntyLevel,
    SovereigntyReport,
    Workload,
    WorkloadList,
    WorkloadSpec,
    WorkloadStatus,
    WorkloadType,
)
from .resources import (
    CarbonResource,
    EnergyResource,
    HubsResource,
    ModelsResource,
    MonitoringResource,
    PricingResource,
    RegionsResource,
    WorkloadsResource,
)

__version__ = "0.2.1"
__author__ = "VitalCheffe"

__all__ = [
    # Client
    "HarchOSClient",
    # Auth
    "Authenticator",
    # Config
    "HarchOSConfig",
    "Profile",
    # Logging
    "configure_logging",
    "get_logger",
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
    "BillingRecord",
    "CarbonAction",
    "CarbonBudget",
    "CarbonDashboard",
    "CarbonDataSource",
    "CarbonForecast",
    "CarbonForecastPoint",
    "CarbonIntensityZone",
    "CarbonIntensityZoneList",
    "CarbonMetrics",
    "CarbonOptimalHub",
    "CarbonOptimizeResult",
    "ComputePriority",
    "ComputeRequirements",
    "CostBreakdown",
    "CostEstimate",
    "DataClassification",
    "DataResidencyPolicy",
    "DetailedHealth",
    "EnergyConsumption",
    "EnergyEfficiency",
    "EnergyReport",
    "EnergySource",
    "EnergySummary",
    "FuelMixEntry",
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
    "PlatformMetrics",
    "PricingPlan",
    "Region",
    "SovereigntyLevel",
    "SovereigntyReport",
    "Workload",
    "WorkloadList",
    "WorkloadSpec",
    "WorkloadStatus",
    "WorkloadType",
    # Resources
    "CarbonResource",
    "EnergyResource",
    "HubsResource",
    "ModelsResource",
    "MonitoringResource",
    "PricingResource",
    "RegionsResource",
    "WorkloadsResource",
]
