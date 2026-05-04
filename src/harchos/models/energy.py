"""Energy Pydantic models for the HarchOS SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field, field_validator, model_validator

from .common import HarchOSBaseModel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EnergySource(str, Enum):
    """Types of energy sources."""

    SOLAR = "solar"
    WIND = "wind"
    HYDRO = "hydro"
    NUCLEAR = "nuclear"
    NATURAL_GAS = "natural_gas"
    COAL = "coal"
    GRID_MIX = "grid_mix"
    OTHER = "other"


class EnergyEfficiency(str, Enum):
    """Energy efficiency ratings."""

    A_PLUS = "a+"
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"


class TimeOfDay(str, Enum):
    """Periods of the day for energy planning."""

    EARLY_MORNING = "early_morning"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


# ---------------------------------------------------------------------------
# Energy metrics
# ---------------------------------------------------------------------------

class EnergyConsumption(HarchOSBaseModel):
    """Energy consumption data for a resource."""

    kwh_consumed: float = Field(..., ge=0, description="Energy consumed in kWh")
    co2_grams: float = Field(..., ge=0, description="CO2 emitted in grams")
    pue: float = Field(..., gt=0, description="Power Usage Effectiveness")
    renewable_fraction: float = Field(
        default=0.0, ge=0, le=1, description="Fraction of energy from renewable sources"
    )
    grid_intensity_gco2_kwh: float = Field(
        ..., ge=0, description="Grid carbon intensity in gCO2/kWh"
    )
    period_start: datetime = Field(..., description="Measurement period start")
    period_end: datetime = Field(..., description="Measurement period end")

    @model_validator(mode="after")
    def _check_period_order(self) -> "EnergyConsumption":
        """Ensure period_start < period_end."""
        if self.period_start >= self.period_end:
            raise ValueError("period_start must be before period_end")
        return self

    @property
    def duration_hours(self) -> float:
        """Return the measurement period duration in hours."""
        return (self.period_end - self.period_start).total_seconds() / 3600

    @property
    def efficiency_rating(self) -> EnergyEfficiency:
        """Compute an energy efficiency rating based on PUE."""
        if self.pue <= 1.1:
            return EnergyEfficiency.A_PLUS
        elif self.pue <= 1.2:
            return EnergyEfficiency.A
        elif self.pue <= 1.4:
            return EnergyEfficiency.B
        elif self.pue <= 1.6:
            return EnergyEfficiency.C
        elif self.pue <= 1.8:
            return EnergyEfficiency.D
        else:
            return EnergyEfficiency.E


# ---------------------------------------------------------------------------
# Green scheduling window
# ---------------------------------------------------------------------------

class GreenWindow(HarchOSBaseModel):
    """A time window when renewable energy is most available."""

    start: datetime = Field(..., description="Window start time")
    end: datetime = Field(..., description="Window end time")
    renewable_percentage: float = Field(
        ..., ge=0, le=100, description="Expected renewable percentage"
    )
    estimated_co2_grams_per_kwh: float = Field(
        ..., ge=0, description="Estimated CO2 per kWh during this window"
    )
    energy_sources: List[EnergySource] = Field(
        default_factory=list, description="Primary energy sources during this window"
    )
    confidence: float = Field(
        default=0.5, ge=0, le=1, description="Forecast confidence (0-1)"
    )

    @model_validator(mode="after")
    def _check_window_order(self) -> "GreenWindow":
        """Ensure start < end."""
        if self.start >= self.end:
            raise ValueError("Window start must be before end")
        return self

    @property
    def duration_minutes(self) -> float:
        """Return the window duration in minutes."""
        return (self.end - self.start).total_seconds() / 60


# ---------------------------------------------------------------------------
# Energy report
# ---------------------------------------------------------------------------

class EnergyReport(HarchOSBaseModel):
    """Comprehensive energy consumption report."""

    resource_id: str = Field(..., description="ID of the resource")
    resource_type: str = Field(..., description="Type of resource")
    region: str = Field(..., description="Region of the resource")
    consumption: EnergyConsumption = Field(
        ..., description="Energy consumption details"
    )
    green_windows: List[GreenWindow] = Field(
        default_factory=list, description="Upcoming green scheduling windows"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Energy optimization recommendations"
    )
    savings_potential_kwh: Optional[float] = Field(
        default=None, ge=0, description="Potential energy savings in kWh"
    )
    savings_potential_co2_grams: Optional[float] = Field(
        default=None, ge=0, description="Potential CO2 savings in grams"
    )

    @field_validator("region", mode="before")
    @classmethod
    def normalize_region(cls, v: str) -> str:
        """Normalize region string."""
        return v.lower().replace("-", "_").replace(" ", "_")


class EnergySummary(HarchOSBaseModel):
    """Aggregated energy summary across resources."""

    total_kwh: float = Field(..., ge=0, description="Total energy consumed (kWh)")
    total_co2_grams: float = Field(..., ge=0, description="Total CO2 emitted (grams)")
    average_pue: float = Field(..., gt=0, description="Average PUE across resources")
    average_renewable_fraction: float = Field(
        ..., ge=0, le=1, description="Average renewable fraction"
    )
    resource_count: int = Field(..., ge=0, description="Number of resources included")
    period_start: datetime = Field(..., description="Summary period start")
    period_end: datetime = Field(..., description="Summary period end")
