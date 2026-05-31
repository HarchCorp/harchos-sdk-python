"""Tests for new features in HarchOS SDK v0.3.

Covers:
- Async carbon tracker
- Pydantic types validation
- Config.from_env with overrides
- Inference resource dot-notation API
- Top-level package exports
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import harchos
from harchos import (
    HarchOS,
    AsyncHarchOS,
    Config,
    __version__,
    HarchOSError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    InferenceError,
    CarbonFootprint,
    CarbonIntensity,
    CarbonForecast,
    CarbonForecastPoint,
    CarbonOptimalHub,
    CarbonOptimizeResult,
    CarbonDashboard,
    ModelInfo,
    ModelList,
    ChatMessage,
    ChatChoice,
    ChatCompletionResponse,
    ChatCompletionChunk,
    CompletionChoice,
    CompletionResponse,
    CompletionChunk,
    Usage,
    Workload,
    WorkloadList,
    WorkloadSpec,
    Hub,
    HubCapacity,
    HubList,
    PricingPlan,
    CostEstimate,
    CostBreakdown,
    UserInfo,
    APIKeyInfo,
)


# ---------------------------------------------------------------------------
# Package-level exports
# ---------------------------------------------------------------------------

class TestPackageExports:
    """Tests that the top-level harchos package exports the right symbols."""

    def test_version(self) -> None:
        assert __version__ == "0.3.0"

    def test_client_classes_exported(self) -> None:
        assert HarchOS is not None
        assert AsyncHarchOS is not None

    def test_config_exported(self) -> None:
        assert Config is not None

    def test_exception_classes_exported(self) -> None:
        assert HarchOSError is not None
        assert AuthenticationError is not None
        assert RateLimitError is not None
        assert NotFoundError is not None
        assert ValidationError is not None
        assert InferenceError is not None

    def test_carbon_types_exported(self) -> None:
        assert CarbonFootprint is not None
        assert CarbonIntensity is not None
        assert CarbonForecast is not None
        assert CarbonForecastPoint is not None
        assert CarbonOptimalHub is not None
        assert CarbonOptimizeResult is not None
        assert CarbonDashboard is not None

    def test_inference_types_exported(self) -> None:
        assert ModelInfo is not None
        assert ModelList is not None
        assert ChatMessage is not None
        assert ChatChoice is not None
        assert ChatCompletionResponse is not None
        assert ChatCompletionChunk is not None
        assert CompletionChoice is not None
        assert CompletionResponse is not None
        assert CompletionChunk is not None
        assert Usage is not None

    def test_workload_types_exported(self) -> None:
        assert Workload is not None
        assert WorkloadList is not None
        assert WorkloadSpec is not None

    def test_hub_types_exported(self) -> None:
        assert Hub is not None
        assert HubCapacity is not None
        assert HubList is not None

    def test_pricing_types_exported(self) -> None:
        assert PricingPlan is not None
        assert CostEstimate is not None
        assert CostBreakdown is not None

    def test_auth_types_exported(self) -> None:
        assert UserInfo is not None
        assert APIKeyInfo is not None


# ---------------------------------------------------------------------------
# Async carbon tracker
# ---------------------------------------------------------------------------

class TestAsyncCarbonTracker:
    """Tests for the async carbon tracker context manager."""

    @pytest.mark.asyncio
    async def test_tracker_basic(self) -> None:
        from harchos.resources.carbon import AsyncCarbonResource

        client = MagicMock(spec=AsyncHarchOS)
        resource = AsyncCarbonResource(client)
        async with resource.tracker() as tracker:
            assert tracker.total_gco2 == 0.0
            assert tracker.request_count == 0
            tracker.record(gco2=2.5, region="morocco")
            assert tracker.total_gco2 == 2.5
            assert tracker.request_count == 1

    @pytest.mark.asyncio
    async def test_tracker_avg(self) -> None:
        from harchos.resources.carbon import AsyncCarbonResource

        client = MagicMock(spec=AsyncHarchOS)
        resource = AsyncCarbonResource(client)
        async with resource.tracker() as tracker:
            tracker.record(gco2=2.0)
            tracker.record(gco2=4.0)
            assert tracker.avg_gco2_per_request == 3.0

    @pytest.mark.asyncio
    async def test_tracker_zero_avg(self) -> None:
        from harchos.resources.carbon import AsyncCarbonResource

        client = MagicMock(spec=AsyncHarchOS)
        resource = AsyncCarbonResource(client)
        async with resource.tracker() as tracker:
            assert tracker.avg_gco2_per_request == 0.0

    @pytest.mark.asyncio
    async def test_tracker_regions(self) -> None:
        from harchos.resources.carbon import AsyncCarbonResource

        client = MagicMock(spec=AsyncHarchOS)
        resource = AsyncCarbonResource(client)
        async with resource.tracker() as tracker:
            tracker.record(gco2=1.0, region="morocco")
            tracker.record(gco2=1.0, region="france")
            tracker.record(gco2=1.0, region="morocco")  # duplicate region
            assert len(tracker.regions) == 2
            assert tracker.request_count == 3

    @pytest.mark.asyncio
    async def test_tracker_repr(self) -> None:
        from harchos.resources.carbon import AsyncCarbonResource

        client = MagicMock(spec=AsyncHarchOS)
        resource = AsyncCarbonResource(client)
        async with resource.tracker() as tracker:
            tracker.record(gco2=1.5)
            r = repr(tracker)
            assert "AsyncCarbonTracker" in r


# ---------------------------------------------------------------------------
# Sync carbon tracker
# ---------------------------------------------------------------------------

class TestSyncCarbonTracker:
    """Tests for the sync carbon tracker context manager."""

    def test_tracker_basic(self) -> None:
        from harchos.resources.carbon import CarbonResource

        client = MagicMock(spec=HarchOS)
        resource = CarbonResource(client)
        with resource.tracker() as tracker:
            tracker.record(gco2=1.0, region="morocco")
            assert tracker.total_gco2 == 1.0

    def test_tracker_avg(self) -> None:
        from harchos.resources.carbon import CarbonResource

        client = MagicMock(spec=HarchOS)
        resource = CarbonResource(client)
        with resource.tracker() as tracker:
            tracker.record(gco2=3.0)
            tracker.record(gco2=5.0)
            assert tracker.avg_gco2_per_request == 4.0


# ---------------------------------------------------------------------------
# Pydantic type validation
# ---------------------------------------------------------------------------

class TestPydanticValidation:
    """Tests that Pydantic models validate data correctly."""

    def test_carbon_footprint_requires_fields(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            CarbonFootprint()  # missing required fields

    def test_carbon_footprint_renewable_range(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            CarbonFootprint(
                gco2_per_request=0.1, hub_region="morocco",
                renewable_percentage=150.0,  # > 100
                carbon_intensity_gco2_kwh=100.0,
            )

    def test_workload_spec_requires_name(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkloadSpec()  # name is required

    def test_workload_spec_name_min_length(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkloadSpec(name="")  # min_length=1

    def test_hub_requires_id_name_region(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            Hub()  # missing required fields

    def test_chat_message_requires_role(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChatMessage()  # role is required

    def test_chat_message_role_validation(self) -> None:
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"

    def test_model_info_requires_id_name(self) -> None:
        with pytest.raises(Exception):
            ModelInfo()  # missing required fields

    def test_usage_defaults(self) -> None:
        u = Usage()
        assert u.prompt_tokens == 0
        assert u.completion_tokens == 0
        assert u.total_tokens == 0

    def test_cost_estimate_requires_fields(self) -> None:
        with pytest.raises(Exception):
            CostEstimate()  # missing required fields


# ---------------------------------------------------------------------------
# Config.from_env with overrides
# ---------------------------------------------------------------------------

class TestConfigFromEnvOverrides:
    """Tests that Config.from_env supports overrides."""

    def test_override_api_key(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        config = Config.from_env(api_key="hsk_override1234567890")
        assert config.api_key == "hsk_override1234567890"

    def test_override_timeout(self, clean_env: None) -> None:
        os.environ["HARCHOS_TIMEOUT"] = "45.0"
        config = Config.from_env(timeout=99.0)
        assert config.timeout == 99.0

    def test_override_base_url(self, clean_env: None) -> None:
        os.environ["HARCHOS_BASE_URL"] = "https://env.api.com/v1"
        config = Config.from_env(base_url="https://override.api.com/v1")
        assert config.base_url == "https://override.api.com/v1"

    def test_override_max_retries(self, clean_env: None) -> None:
        os.environ["HARCHOS_MAX_RETRIES"] = "7"
        config = Config.from_env(max_retries=1)
        assert config.max_retries == 1


# ---------------------------------------------------------------------------
# Inference resource dot-notation API
# ---------------------------------------------------------------------------

class TestInferenceDotNotation:
    """Tests for the inference.chat.completions.create() dot-notation API."""

    def test_chat_completions_path(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        # Verify the nested attribute path exists
        assert hasattr(client.inference, "chat")
        assert hasattr(client.inference.chat, "completions")
        assert hasattr(client.inference.chat.completions, "create")

    def test_completions_path(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client.inference, "completions")
        assert hasattr(client.inference.completions, "create")

    def test_models_path(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client.inference, "models")
        assert hasattr(client.inference.models, "list")


# ---------------------------------------------------------------------------
# Client resource properties
# ---------------------------------------------------------------------------

class TestClientResourceProperties:
    """Tests that all resource properties are correctly initialized."""

    def test_sync_client_resources(self) -> None:
        from harchos.resources.auth import AuthResource
        from harchos.resources.carbon import CarbonResource
        from harchos.resources.hubs import HubsResource
        from harchos.resources.inference import InferenceResource
        from harchos.resources.pricing import PricingResource
        from harchos.resources.workloads import WorkloadsResource

        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert isinstance(client.inference, InferenceResource)
        assert isinstance(client.workloads, WorkloadsResource)
        assert isinstance(client.hubs, HubsResource)
        assert isinstance(client.carbon, CarbonResource)
        assert isinstance(client.pricing, PricingResource)
        assert isinstance(client.auth, AuthResource)

    def test_async_client_resources(self) -> None:
        from harchos.resources.auth import AsyncAuthResource
        from harchos.resources.carbon import AsyncCarbonResource
        from harchos.resources.hubs import AsyncHubsResource
        from harchos.resources.inference import AsyncInferenceResource
        from harchos.resources.pricing import AsyncPricingResource
        from harchos.resources.workloads import AsyncWorkloadsResource

        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert isinstance(client.inference, AsyncInferenceResource)
        assert isinstance(client.workloads, AsyncWorkloadsResource)
        assert isinstance(client.hubs, AsyncHubsResource)
        assert isinstance(client.carbon, AsyncCarbonResource)
        assert isinstance(client.pricing, AsyncPricingResource)
        assert isinstance(client.auth, AsyncAuthResource)

    def test_client_config_property(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert isinstance(client.config, Config)
        assert client.config.api_key == "hsk_testapikey1234567890"

    def test_async_client_config_property(self) -> None:
        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert isinstance(client.config, Config)

    def test_client_with_config_object(self) -> None:
        config = Config(api_key="hsk_testkey1234567890", timeout=60.0)
        client = HarchOS(config=config)
        assert client.config.api_key == "hsk_testkey1234567890"
        assert client.config.timeout == 60.0


# ---------------------------------------------------------------------------
# Pricing resource
# ---------------------------------------------------------------------------

class TestPricingResource:
    """Tests for the PricingResource."""

    def test_estimate(self) -> None:
        from harchos.resources.pricing import PricingResource

        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "gpu_count": 2,
            "gpu_type": "a100",
            "hours": 4.0,
            "region": "morocco",
            "tier": "community",
            "estimated_total": 20.0,
            "breakdown": {
                "gpu_cost": 16.0,
                "cpu_cost": 2.0,
                "subtotal": 18.0,
            },
        }
        resource = PricingResource(client)
        result = resource.estimate(gpu_count=2, gpu_type="a100", hours=4.0)
        assert isinstance(result, CostEstimate)
        assert result.estimated_total == 20.0
        assert result.breakdown.gpu_cost == 16.0

    def test_plans(self) -> None:
        from harchos.resources.pricing import PricingResource

        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "data": [
                {
                    "id": "plan_1",
                    "name": "Community A100",
                    "gpu_type": "a100",
                    "price_per_gpu_hour": 2.50,
                    "price_per_cpu_core_hour": 0.10,
                },
            ],
        }
        resource = PricingResource(client)
        result = resource.plans()
        assert len(result) == 1
        assert isinstance(result[0], PricingPlan)

    def test_plans_list_format(self) -> None:
        from harchos.resources.pricing import PricingResource

        client = MagicMock(spec=HarchOS)
        client.request.return_value = [
            {
                "id": "plan_1",
                "name": "Community A100",
                "gpu_type": "a100",
                "price_per_gpu_hour": 2.50,
                "price_per_cpu_core_hour": 0.10,
            },
        ]
        resource = PricingResource(client)
        result = resource.plans()
        assert len(result) == 1
