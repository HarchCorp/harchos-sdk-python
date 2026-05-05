"""Carbon-aware scheduling Pydantic models for the HarchOS SDK.

These models mirror the server's ``/v1/carbon/*`` response shapes and
provide a typed interface for Python developers building carbon-aware
workflows.
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

class CarbonAction(str, Enum):
    """Possible outcomes of carbon-aware scheduling."""

    SCHEDULE_NOW = "schedule_now"
    DEFER = "defer"
    REJECT = "reject"
    NO_SUITABLE_HUB = "no_suitable_hub"


class CarbonDataSource(str, Enum):
    """Where carbon intensity data came from."""

    ELECTRICITY_MAPS = "electricity_maps"
    CARBON_INTENSITY_UK = "carbon_intensity_uk"
    STATIC = "static"
    MANUAL = "manual"


# ---------------------------------------------------------------------------
# Fuel mix
# ---------------------------------------------------------------------------

class FuelMixEntry(HarchOSBaseModel):
    """Single fuel type contribution in a zone's energy mix."""

    fuel_type: str = Field(..., description="Fuel type: solar, wind, hydro, nuclear, gas, coal, etc.")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of this fuel in the mix")
    power_mw: Optional[float] = Field(None, ge=0, description="Power output in MW")


# ---------------------------------------------------------------------------
# Zone carbon intensity
# ---------------------------------------------------------------------------

class CarbonIntensityZone(HarchOSBaseModel):
    """Real-time carbon intensity for a single electricity zone."""

    zone: str = Field(..., description="Electricity Maps zone code (e.g. 'MA', 'FR')")
    zone_name: str = Field("", description="Human-readable zone name")
    carbon_intensity_gco2_kwh: float = Field(
        ..., ge=0, description="Grid carbon intensity in gCO2/kWh"
    )
    renewable_percentage: float = Field(
        ..., ge=0, le=100, description="Renewable energy %"
    )
    fossil_percentage: float = Field(
        ..., ge=0, le=100, description="Fossil fuel %"
    )
    fuel_mix: List[FuelMixEntry] = Field(
        default_factory=list, description="Detailed fuel mix breakdown"
    )
    source: str = Field(
        "electricity_maps", description="Data source"
    )
    is_forecast: bool = Field(False, description="Whether this is a forecast")
    reading_datetime: datetime = Field(..., alias="datetime", description="Timestamp of the reading")
    updated_at: datetime = Field(..., description="When this data was fetched")

    @property
    def is_green(self) -> bool:
        """Whether this zone is currently below the green threshold (200 gCO2/kWh)."""
        return self.carbon_intensity_gco2_kwh <= 200.0

    def __repr__(self) -> str:
        green = "GREEN" if self.is_green else "FOSSIL"
        return f"CarbonZone({self.zone} {self.zone_name!r} ci={self.carbon_intensity_gco2_kwh}gCO2/kWh renewable={self.renewable_percentage}% [{green}])"


class CarbonIntensityZoneList(HarchOSBaseModel):
    """List of carbon intensity readings across multiple zones."""

    zones: List[CarbonIntensityZone] = Field(default_factory=list)
    total: int = 0


# ---------------------------------------------------------------------------
# Optimal hub selection
# ---------------------------------------------------------------------------

class CarbonOptimalHub(HarchOSBaseModel):
    """Result of carbon-optimal hub selection."""

    recommended_hub_id: Optional[str] = Field(None, description="ID of the recommended hub")
    recommended_hub_name: str = Field("", description="Name of the recommended hub")
    hub_region: str = Field("", description="Region of the recommended hub")
    hub_zone: str = Field("", description="Electricity zone of the recommended hub")
    carbon_intensity_gco2_kwh: float = Field(
        ..., ge=0, description="Current carbon intensity at the recommended hub"
    )
    renewable_percentage: float = Field(
        ..., ge=0, le=100, description="Current renewable % at the recommended hub"
    )
    available_gpus: int = Field(0, ge=0, description="Available GPUs at the recommended hub")
    action: str = Field(
        ..., description="Recommended action: schedule_now | defer | no_suitable_hub"
    )
    defer_hours: float = Field(0.0, ge=0, description="Hours to defer if action=defer")
    defer_reason: str = Field("", description="Why deferral is recommended")
    estimated_carbon_saved_kg: float = Field(
        0.0, ge=0, description="Estimated CO2 saved vs worst-case hub"
    )
    alternative_hubs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Other hubs sorted by carbon intensity (top 5)"
    )
    analyzed_at: datetime = Field(..., description="When this analysis was performed")

    @property
    def is_deferred(self) -> bool:
        """Whether the recommendation is to defer the workload."""
        return self.action == "defer"


# ---------------------------------------------------------------------------
# Workload carbon optimization
# ---------------------------------------------------------------------------

class CarbonOptimizeResult(HarchOSBaseModel):
    """Result of carbon-aware workload optimization."""

    action: str = Field(
        ..., description="schedule_now | defer | reject"
    )
    workload_name: str = Field(..., description="Name of the workload")
    selected_hub_id: Optional[str] = None
    selected_hub_name: str = ""
    carbon_intensity_at_schedule_gco2_kwh: float = 0.0
    carbon_saved_kg: float = Field(0.0, ge=0, description="Estimated CO2 saved in kg")
    baseline_carbon_kg: float = Field(0.0, ge=0, description="CO2 on the dirtiest hub")
    actual_carbon_kg: float = Field(0.0, ge=0, description="CO2 on the selected hub")
    deferred_hours: float = Field(0.0, ge=0, description="Hours deferred")
    reason: str = Field("", description="Human-readable explanation")
    estimated_green_window: Optional[Dict[str, Any]] = Field(
        None, description="Next green window if deferred"
    )
    optimized_at: datetime = Field(..., description="When optimization was computed")

    @property
    def carbon_savings_percentage(self) -> float:
        """Carbon savings as a percentage of baseline."""
        if self.baseline_carbon_kg <= 0:
            return 0.0
        return round((self.carbon_saved_kg / self.baseline_carbon_kg) * 100, 2)


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

class CarbonForecastPoint(HarchOSBaseModel):
    """A single point in a carbon intensity forecast."""

    reading_datetime: datetime = Field(..., alias="datetime")
    carbon_intensity_gco2_kwh: float = Field(..., ge=0)
    renewable_percentage: float = Field(..., ge=0, le=100)
    is_green: bool = Field(False, description="Whether this point meets the green threshold")


class CarbonForecast(HarchOSBaseModel):
    """Carbon intensity forecast for a zone."""

    zone: str
    zone_name: str = ""
    forecast: List[CarbonForecastPoint] = Field(default_factory=list)
    green_windows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified green windows in the forecast period"
    )

    @property
    def best_window(self) -> Optional[Dict[str, Any]]:
        """Return the first (soonest) green window, if any."""
        return self.green_windows[0] if self.green_windows else None

    @property
    def green_hours_count(self) -> float:
        """Total green hours in the forecast."""
        count = 0
        for i, point in enumerate(self.forecast):
            if point.is_green and i + 1 < len(self.forecast):
                # Approximate: each point represents ~15 min
                count += 0.25
        return round(count, 2)


# ---------------------------------------------------------------------------
# Metrics & Dashboard
# ---------------------------------------------------------------------------

class CarbonMetrics(HarchOSBaseModel):
    """Aggregate carbon metrics across the platform."""

    total_carbon_saved_kg: float = Field(0.0, ge=0, description="Total CO2 saved")
    total_workloads_optimized: int = Field(0, ge=0)
    total_workloads_deferred: int = Field(0, ge=0)
    average_carbon_intensity_gco2_kwh: float = Field(0.0, ge=0)
    best_hub_id: Optional[str] = None
    best_hub_name: str = ""
    best_hub_carbon_intensity: float = 0.0
    worst_hub_carbon_intensity: float = 0.0
    period_start: datetime
    period_end: datetime


class CarbonDashboard(HarchOSBaseModel):
    """Full carbon-aware dashboard data."""

    metrics: CarbonMetrics
    hub_intensities: List[CarbonIntensityZone] = Field(default_factory=list)
    optimization_log: List[Dict[str, Any]] = Field(default_factory=list)
    green_windows: List[Dict[str, Any]] = Field(default_factory=list)
