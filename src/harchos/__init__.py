"""HarchOS Python SDK v0.3.0 — The Operating System for Sovereign AI Infrastructure.

This SDK provides both sync and async access to the HarchOS API
with built-in carbon tracking, OpenAI-compatible inference, and
carbon-aware workload scheduling.

Example (sync)::

    from harchos import HarchOS

    client = HarchOS(api_key="hsk_...")
    response = client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.content)
    print(f"Carbon: {response.carbon_footprint.gco2}g CO2")

Example (async)::

    from harchos import AsyncHarchOS

    async with AsyncHarchOS(api_key="hsk_...") as client:
        response = await client.inference.chat.completions.create(
            model="harchos-llama-3.3-70b",
            messages=[{"role": "user", "content": "Hello"}],
        )

Example (streaming)::

    for chunk in client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
    ):
        print(chunk.choices[0].delta.content, end="")

Example (carbon tracker)::

    with client.carbon.tracker() as tracker:
        r1 = client.inference.chat.completions.create(...)
        r2 = client.inference.chat.completions.create(...)
        for r in [r1, r2]:
            tracker.record(gco2=r.carbon_footprint.gco2, region=r.carbon_footprint.hub_region)
    print(f"Total CO2: {tracker.total_gco2}g")
"""

from ._client import AsyncHarchOS, HarchOS, __version__
from ._config import Config
from ._exceptions import (
    AuthenticationError,
    HarchOSError,
    InferenceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ._types import (
    APIKeyInfo,
    CarbonDashboard,
    CarbonFootprint,
    CarbonForecast,
    CarbonForecastPoint,
    CarbonIntensity,
    CarbonMetrics,
    CarbonOptimalHub,
    CarbonOptimizeResult,
    ChatChoice,
    ChatCompletionChunk,
    ChatCompletionResponse,
    ChatMessage,
    CompletionChunk,
    CompletionChoice,
    CompletionResponse,
    CostBreakdown,
    CostEstimate,
    Hub,
    HubCapacity,
    HubList,
    ModelInfo,
    ModelList,
    PricingPlan,
    UserInfo,
    Usage,
    Workload,
    WorkloadList,
    WorkloadSpec,
)

__author__ = "VitalCheffe"

__all__ = [
    # Client
    "HarchOS",
    "AsyncHarchOS",
    # Config
    "Config",
    # Version
    "__version__",
    # Exceptions
    "HarchOSError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "InferenceError",
    # Types — Carbon
    "CarbonFootprint",
    "CarbonIntensity",
    "CarbonForecast",
    "CarbonForecastPoint",
    "CarbonOptimalHub",
    "CarbonOptimizeResult",
    "CarbonDashboard",
    "CarbonMetrics",
    # Types — Inference
    "ModelInfo",
    "ModelList",
    "ChatMessage",
    "ChatChoice",
    "ChatCompletionResponse",
    "ChatCompletionChunk",
    "CompletionChoice",
    "CompletionResponse",
    "CompletionChunk",
    "Usage",
    # Types — Workloads
    "Workload",
    "WorkloadList",
    "WorkloadSpec",
    # Types — Hubs
    "Hub",
    "HubCapacity",
    "HubList",
    # Types — Pricing
    "PricingPlan",
    "CostEstimate",
    "CostBreakdown",
    # Types — Auth
    "UserInfo",
    "APIKeyInfo",
]
