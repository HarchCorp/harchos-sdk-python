"""Monitoring models for the HarchOS SDK.

These models represent platform-level metrics and health information
for the HarchOS infrastructure.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import HarchOSBaseModel


# ---------------------------------------------------------------------------
# Platform Metrics
# ---------------------------------------------------------------------------

class PlatformMetrics(HarchOSBaseModel):
    """Aggregate platform metrics for HarchOS infrastructure.

    Provides a high-level overview of the entire platform including
    GPU utilization, energy consumption, and carbon impact.
    """

    total_hubs: int = Field(0, ge=0, description="Total number of hubs on the platform")
    total_gpus: int = Field(0, ge=0, description="Total GPUs across all hubs")
    available_gpus: int = Field(0, ge=0, description="Currently available (idle) GPUs")
    gpu_utilization_percent: float = Field(
        0.0, ge=0, le=100,
        description="Average GPU utilization across all hubs"
    )
    total_workloads: int = Field(0, ge=0, description="Total workloads ever created")
    active_workloads: int = Field(0, ge=0, description="Currently running workloads")
    total_energy_kwh: float = Field(0.0, ge=0, description="Total energy consumed (kWh)")
    avg_renewable_percentage: float = Field(
        0.0, ge=0, le=100,
        description="Average renewable energy percentage across all hubs"
    )
    avg_carbon_intensity: float = Field(
        0.0, ge=0,
        description="Average carbon intensity across all hubs (gCO2/kWh)"
    )
    avg_pue: float = Field(
        0.0, ge=1.0,
        description="Average Power Usage Effectiveness across hubs"
    )
    total_co2_saved_kg: float = Field(
        0.0, ge=0,
        description="Total CO2 saved through carbon-aware scheduling (kg)"
    )

    @property
    def utilization_health(self) -> str:
        """Categorize GPU utilization health."""
        if self.gpu_utilization_percent >= 90:
            return "critical"
        elif self.gpu_utilization_percent >= 75:
            return "high"
        elif self.gpu_utilization_percent >= 50:
            return "moderate"
        else:
            return "low"

    def __repr__(self) -> str:
        return (
            f"PlatformMetrics("
            f"hubs={self.total_hubs} "
            f"gpus={self.total_gpus}({self.available_gpus} avail) "
            f"util={self.gpu_utilization_percent:.0f}% "
            f"renewable={self.avg_renewable_percentage:.0f}% "
            f"ci={self.avg_carbon_intensity}gCO2/kWh "
            f"co2_saved={self.total_co2_saved_kg}kg)"
        )


# ---------------------------------------------------------------------------
# Detailed Health
# ---------------------------------------------------------------------------

class DetailedHealth(HarchOSBaseModel):
    """Detailed health check response for the HarchOS platform.

    Provides granular information about the API server's health,
    including database connectivity, uptime, and connection stats.
    """

    status: str = Field(
        ..., description="Overall health status: healthy, degraded, unhealthy"
    )
    database_status: str = Field(
        ..., description="Database connectivity status: connected, degraded, disconnected"
    )
    api_version: str = Field(
        ..., description="API server version (e.g. '0.1.0')"
    )
    uptime_seconds: float = Field(
        ..., ge=0, description="Server uptime in seconds"
    )
    total_endpoints: int = Field(
        0, ge=0, description="Total number of registered API endpoints"
    )
    active_connections: int = Field(
        0, ge=0, description="Number of currently active API connections"
    )

    @property
    def is_healthy(self) -> bool:
        """Whether the platform is in a healthy state."""
        return self.status == "healthy" and self.database_status == "connected"

    @property
    def uptime_hours(self) -> float:
        """Server uptime expressed in hours."""
        return round(self.uptime_seconds / 3600.0, 2)

    @property
    def uptime_days(self) -> float:
        """Server uptime expressed in days."""
        return round(self.uptime_seconds / 86400.0, 2)
