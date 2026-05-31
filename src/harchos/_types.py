"""Shared Pydantic models for HarchOS SDK responses.

These models provide typed responses matching the HarchOS API schemas.
All models inherit from ``pydantic.BaseModel`` for validation and
serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Carbon footprint (included in every inference response)
# ---------------------------------------------------------------------------

class CarbonFootprint(BaseModel):
    """Carbon footprint data attached to every inference response.

    This is the unique differentiator of the HarchOS platform — every
    API response includes real-time carbon tracking.
    """

    gco2_per_request: float = Field(..., description="Grams of CO2 emitted for this request")
    hub_region: str = Field(..., description="Hub region where inference ran")
    carbon_intensity_gco2_kwh: float = Field(
        ..., ge=0, description="Carbon intensity at hub in gCO2/kWh"
    )
    renewable_percentage: float = Field(
        ..., ge=0, le=100, description="Renewable energy percentage at hub"
    )
    gpu_type: str = Field(default="", description="GPU type used for inference")
    estimated_power_watts: float = Field(default=0.0, ge=0, description="Estimated GPU power consumption in watts")
    inference_duration_seconds: float = Field(default=0.0, ge=0, description="Inference duration in seconds")
    carbon_saved_vs_average_gco2: float = Field(
        default=0.0, ge=0, description="CO2 saved compared to global average grid"
    )

    # Backward-compatible aliases
    @property
    def gco2(self) -> float:
        """Grams of CO2 emitted (alias for gco2_per_request)."""
        return self.gco2_per_request

    @property
    def net_gco2(self) -> float:
        """Net CO2 after savings."""
        return max(0.0, self.gco2_per_request - self.carbon_saved_vs_average_gco2)

    @property
    def is_green(self) -> bool:
        """Whether the inference ran on a green hub (< 200 gCO2/kWh)."""
        return self.carbon_intensity_gco2_kwh < 200.0

    def __repr__(self) -> str:
        return (
            f"CarbonFootprint(gco2={self.gco2_per_request}, region={self.hub_region!r}, "
            f"renewable={self.renewable_percentage}%)"
        )


# ---------------------------------------------------------------------------
# Inference models
# ---------------------------------------------------------------------------

class ModelInfo(BaseModel):
    """Information about an AI model available on HarchOS."""

    id: str = Field(..., description="Model identifier (e.g. 'harchos-llama-3.3-70b')")
    name: str = Field(..., description="Human-readable model name")
    owned_by: str = Field(default="harchos", description="Model owner")
    type: str = Field(default="chat", description="Model type: chat, completion, embedding")
    context_length: int = Field(default=4096, description="Maximum context length in tokens")
    pricing_prompt_per_million: Optional[float] = Field(
        None, description="Price per million prompt tokens"
    )
    pricing_completion_per_million: Optional[float] = Field(
        None, description="Price per million completion tokens"
    )
    created: Optional[int] = Field(None, description="Unix timestamp of model creation")

    def __repr__(self) -> str:
        return f"ModelInfo(id={self.id!r}, type={self.type!r})"


class ModelList(BaseModel):
    """Paginated list of models."""

    object: str = Field(default="list")
    data: List[ModelInfo] = Field(default_factory=list)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="Message role"
    )
    content: Optional[str] = Field(None, description="Message text content")
    name: Optional[str] = Field(None, description="Participant name")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID for tool responses")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tool calls from assistant"
    )


class CompletionChoice(BaseModel):
    """A single completion choice."""

    index: int = Field(default=0)
    text: str = Field(default="")
    finish_reason: Optional[str] = Field(None)
    logprobs: Optional[Any] = Field(None)


class ChatChoice(BaseModel):
    """A single chat completion choice."""

    index: int = Field(default=0)
    message: ChatMessage = Field(...)
    finish_reason: Optional[str] = Field(None)
    logprobs: Optional[Any] = Field(None)


class Usage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)


class CompletionResponse(BaseModel):
    """Response from a text completion request."""

    id: str = Field(default="")
    object: str = Field(default="text_completion")
    created: int = Field(default=0)
    model: str = Field(default="")
    choices: List[CompletionChoice] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    carbon_footprint: CarbonFootprint = Field(
        default_factory=lambda: CarbonFootprint(
            gco2_per_request=0.0, hub_region="unknown", renewable_percentage=0.0,
            carbon_intensity_gco2_kwh=0.0,
        )
    )

    def __repr__(self) -> str:
        return (
            f"CompletionResponse(id={self.id!r}, model={self.model!r}, "
            f"tokens={self.usage.total_tokens})"
        )


class ChatCompletionResponse(BaseModel):
    """Response from a chat completion request."""

    id: str = Field(default="")
    object: str = Field(default="chat.completion")
    created: int = Field(default=0)
    model: str = Field(default="")
    choices: List[ChatChoice] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    carbon_footprint: CarbonFootprint = Field(
        default_factory=lambda: CarbonFootprint(
            gco2_per_request=0.0, hub_region="unknown", renewable_percentage=0.0,
            carbon_intensity_gco2_kwh=0.0,
        )
    )

    @property
    def content(self) -> Optional[str]:
        """Shortcut to get the first choice's message content."""
        if self.choices:
            return self.choices[0].message.content
        return None

    def __repr__(self) -> str:
        return (
            f"ChatCompletionResponse(id={self.id!r}, model={self.model!r}, "
            f"tokens={self.usage.total_tokens}, "
            f"carbon={self.carbon_footprint.gco2}gCO2)"
        )


# ---------------------------------------------------------------------------
# Streaming chunk models
# ---------------------------------------------------------------------------

class DeltaMessage(BaseModel):
    """Partial message delta for streaming responses."""

    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    """A single streaming choice."""

    index: int = Field(default=0)
    delta: DeltaMessage = Field(default_factory=DeltaMessage)
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class ChatCompletionChunk(BaseModel):
    """A streaming chunk from a chat completion request."""

    id: str = Field(default="")
    object: str = Field(default="chat.completion.chunk")
    created: int = Field(default=0)
    model: str = Field(default="")
    choices: List[StreamChoice] = Field(default_factory=list)
    carbon_footprint: Optional[CarbonFootprint] = Field(
        None,
        description="Carbon data (present in the final chunk with finish_reason)",
    )


class CompletionStreamChoice(BaseModel):
    """A single streaming choice for text completions."""

    index: int = Field(default=0)
    text: str = Field(default="")
    finish_reason: Optional[str] = None


class CompletionChunk(BaseModel):
    """A streaming chunk from a text completion request."""

    id: str = Field(default="")
    object: str = Field(default="text_completion")
    created: int = Field(default=0)
    model: str = Field(default="")
    choices: List[CompletionStreamChoice] = Field(default_factory=list)
    carbon_footprint: Optional[CarbonFootprint] = Field(None)


# ---------------------------------------------------------------------------
# Workload models
# ---------------------------------------------------------------------------

class WorkloadSpec(BaseModel):
    """Specification for creating a workload."""

    name: str = Field(..., min_length=1, description="Workload name")
    type: str = Field(default="training", description="Workload type")
    model_id: Optional[str] = Field(None, description="Model ID to use")
    hub_id: Optional[str] = Field(None, description="Target hub ID")
    gpu_count: int = Field(default=1, ge=0, description="Number of GPUs")
    gpu_type: Optional[str] = Field(None, description="GPU type (e.g. 'a100')")
    cpu_cores: int = Field(default=1, ge=1, description="CPU cores")
    memory_gb: float = Field(default=1.0, gt=0, description="Memory in GB")
    priority: str = Field(default="normal", description="Scheduling priority")
    image: Optional[str] = Field(None, description="Container image")
    command: Optional[List[str]] = Field(None, description="Command and args")
    env: Dict[str, str] = Field(default_factory=dict, description="Env vars")
    carbon_budget_grams: Optional[float] = Field(None, gt=0, description="Max CO2 budget")
    max_duration_seconds: Optional[int] = Field(None, gt=0, description="Max runtime")
    labels: Dict[str, str] = Field(default_factory=dict, description="Labels")


class Workload(BaseModel):
    """A HarchOS workload resource."""

    id: str = Field(..., description="Unique workload identifier")
    name: str = Field(..., description="Workload name")
    type: str = Field(default="training", description="Workload type")
    status: str = Field(default="pending", description="Current status")
    spec: Optional[WorkloadSpec] = None
    hub_id: Optional[str] = Field(None, description="Hub where running")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __repr__(self) -> str:
        return f"Workload(id={self.id!r}, name={self.name!r}, status={self.status!r})"


class WorkloadList(BaseModel):
    """Paginated list of workloads."""

    items: List[Workload] = Field(default_factory=list)
    total: int = Field(default=0)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


# ---------------------------------------------------------------------------
# Hub models
# ---------------------------------------------------------------------------

class HubCapacity(BaseModel):
    """Current capacity of a hub."""

    total_gpus: int = Field(default=0, ge=0)
    available_gpus: int = Field(default=0, ge=0)
    total_cpu_cores: int = Field(default=0, ge=0)
    available_cpu_cores: int = Field(default=0, ge=0)
    total_memory_gb: float = Field(default=0.0, ge=0)
    available_memory_gb: float = Field(default=0.0, ge=0)

    @property
    def gpu_utilization(self) -> float:
        """Return GPU utilization as a fraction (0..1)."""
        if self.total_gpus == 0:
            return 0.0
        return 1.0 - (self.available_gpus / self.total_gpus)


class Hub(BaseModel):
    """A HarchOS Hub resource."""

    id: str = Field(..., description="Unique hub identifier")
    name: str = Field(..., description="Hub name")
    region: str = Field(..., description="Hub region")
    status: str = Field(default="ready", description="Hub status")
    tier: str = Field(default="standard", description="Performance tier")
    capacity: Optional[HubCapacity] = None
    endpoint: Optional[str] = None
    active_workloads: int = Field(default=0, ge=0)
    carbon_intensity_gco2_kwh: Optional[float] = None
    renewable_percentage: Optional[float] = None
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return (
            f"Hub(id={self.id!r}, name={self.name!r}, region={self.region!r})"
        )


class HubList(BaseModel):
    """Paginated list of hubs."""

    items: List[Hub] = Field(default_factory=list)
    total: int = Field(default=0)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


# ---------------------------------------------------------------------------
# Carbon models
# ---------------------------------------------------------------------------

class CarbonIntensity(BaseModel):
    """Carbon intensity for a single zone."""

    zone: str = Field(..., description="Zone code (e.g. 'MA', 'FR')")
    zone_name: str = Field(default="", description="Human-readable zone name")
    carbon_intensity_gco2_kwh: float = Field(..., ge=0, description="gCO2/kWh")
    renewable_percentage: float = Field(..., ge=0, le=100, description="Renewable %")
    fossil_percentage: float = Field(default=0.0, ge=0, le=100, description="Fossil %")
    updated_at: Optional[datetime] = None

    @property
    def is_green(self) -> bool:
        """Whether this zone is below the green threshold (< 200 gCO2/kWh)."""
        return self.carbon_intensity_gco2_kwh < 200.0

    def __repr__(self) -> str:
        tag = "GREEN" if self.is_green else "FOSSIL"
        return f"CarbonIntensity({self.zone} {self.carbon_intensity_gco2_kwh}gCO2/kWh [{tag}])"


class CarbonIntensityList(BaseModel):
    """List of carbon intensity readings."""

    zones: List[CarbonIntensity] = Field(default_factory=list)
    total: int = Field(default=0)


class CarbonForecastPoint(BaseModel):
    """A single forecast data point."""

    reading_datetime: datetime = Field(..., alias="datetime", description="Forecast timestamp")
    carbon_intensity_gco2_kwh: float = Field(..., ge=0)
    renewable_percentage: float = Field(..., ge=0, le=100)
    is_green: bool = Field(default=False)

    model_config = {"populate_by_name": True}


class CarbonForecast(BaseModel):
    """Carbon intensity forecast for a zone."""

    zone: str
    zone_name: str = Field(default="")
    forecast: List[CarbonForecastPoint] = Field(default_factory=list)
    green_windows: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def best_window(self) -> Optional[Dict[str, Any]]:
        """Return the first (soonest) green window, if any."""
        return self.green_windows[0] if self.green_windows else None


class CarbonOptimalHub(BaseModel):
    """Result of carbon-optimal hub selection."""

    recommended_hub_id: Optional[str] = None
    recommended_hub_name: str = Field(default="")
    hub_region: str = Field(default="")
    hub_zone: str = Field(default="")
    carbon_intensity_gco2_kwh: float = Field(..., ge=0)
    renewable_percentage: float = Field(..., ge=0, le=100)
    available_gpus: int = Field(default=0, ge=0)
    action: str = Field(...)
    defer_hours: float = Field(default=0.0, ge=0)
    defer_reason: str = Field(default="")
    estimated_carbon_saved_kg: float = Field(default=0.0, ge=0)
    alternative_hubs: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def is_deferred(self) -> bool:
        return self.action == "defer"


class CarbonOptimizeResult(BaseModel):
    """Result of carbon-aware workload optimization."""

    action: str = Field(...)
    workload_name: str = Field(...)
    selected_hub_id: Optional[str] = None
    selected_hub_name: str = Field(default="")
    carbon_intensity_at_schedule_gco2_kwh: float = Field(default=0.0)
    carbon_saved_kg: float = Field(default=0.0, ge=0)
    baseline_carbon_kg: float = Field(default=0.0, ge=0)
    actual_carbon_kg: float = Field(default=0.0, ge=0)
    deferred_hours: float = Field(default=0.0, ge=0)
    reason: str = Field(default="")


class CarbonMetrics(BaseModel):
    """Aggregate carbon metrics."""
    total_carbon_saved_kg: float = Field(default=0.0)
    total_workloads_optimized: int = Field(default=0)
    total_workloads_deferred: int = Field(default=0)
    average_carbon_intensity_gco2_kwh: float = Field(default=0.0)
    best_hub_id: Optional[str] = None
    best_hub_name: str = Field(default="")
    best_hub_carbon_intensity: float = Field(default=0.0)
    worst_hub_carbon_intensity: float = Field(default=0.0)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class CarbonDashboard(BaseModel):
    """Full carbon-aware dashboard data."""

    metrics: CarbonMetrics = Field(default_factory=CarbonMetrics)
    hub_intensities: List[CarbonIntensity] = Field(default_factory=list)
    optimization_log: List[Dict[str, Any]] = Field(default_factory=list)
    green_windows: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pricing models
# ---------------------------------------------------------------------------

class PricingPlan(BaseModel):
    """A pricing plan for GPU/CPU resources."""

    id: str = Field(..., description="Plan identifier")
    name: str = Field(..., description="Plan name")
    gpu_type: str = Field(..., description="GPU type")
    price_per_gpu_hour: float = Field(..., ge=0)
    price_per_cpu_core_hour: float = Field(..., ge=0)
    price_per_gb_storage_month: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD")
    region: str = Field(default="morocco")
    tier: str = Field(default="community")

    def __repr__(self) -> str:
        return (
            f"PricingPlan({self.name!r}, gpu={self.gpu_type}, "
            f"${self.price_per_gpu_hour}/{self.currency} per GPU-hr)"
        )


class CostBreakdown(BaseModel):
    """Detailed cost breakdown."""

    gpu_cost: float = Field(default=0.0, ge=0)
    cpu_cost: float = Field(default=0.0, ge=0)
    memory_cost: float = Field(default=0.0, ge=0)
    storage_cost: float = Field(default=0.0, ge=0)
    network_cost: float = Field(default=0.0, ge=0)
    discount_percentage: float = Field(default=0.0, ge=0, le=100)
    subtotal: float = Field(default=0.0, ge=0)
    tax: float = Field(default=0.0, ge=0)


class CostEstimate(BaseModel):
    """A cost estimate for a planned deployment."""

    gpu_count: int = Field(..., ge=1)
    gpu_type: str = Field(...)
    hours: float = Field(..., gt=0)
    region: str = Field(default="morocco")
    tier: str = Field(default="community")
    estimated_total: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    breakdown: CostBreakdown = Field(default_factory=CostBreakdown)


# ---------------------------------------------------------------------------
# Auth models
# ---------------------------------------------------------------------------

class UserInfo(BaseModel):
    """Information about the authenticated user."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="Display name")
    plan: str = Field(default="community", description="Subscription plan")
    created_at: Optional[datetime] = None
    api_keys: List[Dict[str, Any]] = Field(default_factory=list)

    def __repr__(self) -> str:
        return f"UserInfo(id={self.id!r}, email={self.email!r}, plan={self.plan!r})"


class APIKeyInfo(BaseModel):
    """Information about an API key."""

    id: str = Field(..., description="Key ID")
    name: str = Field(..., description="Key name")
    prefix: str = Field(..., description="Key prefix (e.g. 'hsk_abcd')")
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked: bool = Field(default=False)

    def __repr__(self) -> str:
        return f"APIKeyInfo(id={self.id!r}, name={self.name!r}, prefix={self.prefix!r})"
