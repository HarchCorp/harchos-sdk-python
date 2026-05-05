"""Region models for the HarchOS SDK.

These models represent geographic regions where HarchOS operates,
including availability, infrastructure stats, and compliance info.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import HarchOSBaseModel


class Region(HarchOSBaseModel):
    """A geographic region where HarchOS operates.

    Regions contain hubs (data centers) and are the top-level
    sovereignty boundary. Each region enforces data residency
    and compliance rules.
    """

    name: str = Field(..., description="Human-readable region name (e.g. 'Morocco')")
    code: str = Field(..., description="Region code (e.g. 'morocco', 'nigeria')")
    country: str = Field(..., description="ISO 3166-1 alpha-2 country code (e.g. 'MA', 'NG')")
    available: bool = Field(True, description="Whether this region is currently available for deployments")
    hub_count: int = Field(0, ge=0, description="Number of hubs in this region")
    total_gpus: int = Field(0, ge=0, description="Total GPUs across all hubs in this region")
    avg_renewable_percentage: float = Field(
        0.0, ge=0, le=100,
        description="Average renewable energy percentage across hubs"
    )
    avg_carbon_intensity: float = Field(
        0.0, ge=0,
        description="Average carbon intensity in gCO2/kWh across hubs"
    )
    latency_ms_from_casablanca: Optional[float] = Field(
        None, ge=0,
        description="Network latency in ms from the Casablanca hub"
    )
    compliance_frameworks: List[str] = Field(
        default_factory=list,
        description="Compliance frameworks supported (e.g. 'GDPR', 'PDPA', 'ISO27001')"
    )

    @property
    def is_green(self) -> bool:
        """Whether this region's average carbon intensity is below 200 gCO2/kWh."""
        return self.avg_carbon_intensity <= 200.0

    @property
    def has_hubs(self) -> bool:
        """Whether this region has any active hubs."""
        return self.hub_count > 0
