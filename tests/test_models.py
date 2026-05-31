"""Tests for the InferenceResource module and Pydantic type models (v0.3).

Replaces the old test_models.py which tested the removed ModelsResource.
Models are now accessed via client.inference.models.
Type models are defined in harchos._types.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from harchos._client import HarchOS, AsyncHarchOS
from harchos._types import (
    ModelInfo,
    ModelList,
    ChatMessage,
    ChatChoice,
    ChatCompletionResponse,
    CompletionResponse,
    CompletionChoice,
    Usage,
    CarbonFootprint,
    Workload,
    WorkloadSpec,
    Hub,
    HubCapacity,
    HubList,
    CarbonIntensity,
    CarbonForecast,
    CarbonForecastPoint,
    CarbonOptimalHub,
    CarbonOptimizeResult,
    CarbonDashboard,
    PricingPlan,
    CostEstimate,
    CostBreakdown,
    UserInfo,
    APIKeyInfo,
)
from harchos.resources.inference import InferenceResource, AsyncInferenceResource


# ---------------------------------------------------------------------------
# Pydantic type model tests
# ---------------------------------------------------------------------------

class TestCarbonFootprintModel:
    """Tests for CarbonFootprint type model."""

    def test_basic_creation(self) -> None:
        cf = CarbonFootprint(
            gco2=0.12,
            hub_region="morocco",
            renewable_percentage=75.0,
            grid_intensity_gco2_kwh=120.0,
        )
        assert cf.gco2 == 0.12
        assert cf.hub_region == "morocco"

    def test_net_gco2(self) -> None:
        cf = CarbonFootprint(
            gco2=10.0,
            hub_region="morocco",
            renewable_percentage=75.0,
            grid_intensity_gco2_kwh=120.0,
            offset_gco2=3.0,
        )
        assert cf.net_gco2 == 7.0

    def test_net_gco2_cannot_go_negative(self) -> None:
        cf = CarbonFootprint(
            gco2=5.0,
            hub_region="morocco",
            renewable_percentage=75.0,
            grid_intensity_gco2_kwh=120.0,
            offset_gco2=10.0,
        )
        assert cf.net_gco2 == 0.0

    def test_is_green(self) -> None:
        cf_green = CarbonFootprint(
            gco2=0.1, hub_region="morocco",
            renewable_percentage=90.0, grid_intensity_gco2_kwh=100.0,
        )
        assert cf_green.is_green is True

        cf_fossil = CarbonFootprint(
            gco2=0.5, hub_region="us-east",
            renewable_percentage=20.0, grid_intensity_gco2_kwh=400.0,
        )
        assert cf_fossil.is_green is False

    def test_repr(self) -> None:
        cf = CarbonFootprint(
            gco2=0.12, hub_region="morocco",
            renewable_percentage=75.0, grid_intensity_gco2_kwh=120.0,
        )
        r = repr(cf)
        assert "CarbonFootprint" in r
        assert "0.12" in r


class TestModelInfoModel:
    """Tests for ModelInfo type model."""

    def test_basic_creation(self) -> None:
        m = ModelInfo(id="harchos-llama-3.3-70b", name="HarchOS LLaMA 3.3 70B")
        assert m.id == "harchos-llama-3.3-70b"
        assert m.name == "HarchOS LLaMA 3.3 70B"
        assert m.owned_by == "harchos"
        assert m.type == "chat"

    def test_repr(self) -> None:
        m = ModelInfo(id="harchos-llama-3.3-70b", name="LLaMA", type="chat")
        assert "harchos-llama-3.3-70b" in repr(m)


class TestModelListModel:
    """Tests for ModelList type model."""

    def test_empty(self) -> None:
        ml = ModelList()
        assert len(ml) == 0
        assert list(ml) == []

    def test_with_data(self) -> None:
        ml = ModelList(data=[
            ModelInfo(id="model-1", name="Model 1"),
            ModelInfo(id="model-2", name="Model 2"),
        ])
        assert len(ml) == 2
        assert ml.data[0].id == "model-1"


class TestChatCompletionResponseModel:
    """Tests for ChatCompletionResponse type model."""

    def test_content_property(self) -> None:
        resp = ChatCompletionResponse(
            choices=[
                ChatChoice(message=ChatMessage(role="assistant", content="Hello!"))
            ]
        )
        assert resp.content == "Hello!"

    def test_content_empty_choices(self) -> None:
        resp = ChatCompletionResponse()
        assert resp.content is None

    def test_with_carbon_footprint(self) -> None:
        resp = ChatCompletionResponse(
            model="harchos-llama-3.3-70b",
            choices=[ChatChoice(message=ChatMessage(role="assistant", content="Hi"))],
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            carbon_footprint=CarbonFootprint(
                gco2=0.12, hub_region="morocco",
                renewable_percentage=75.0, grid_intensity_gco2_kwh=120.0,
            ),
        )
        assert resp.carbon_footprint.gco2 == 0.12


class TestCompletionResponseModel:
    """Tests for CompletionResponse type model."""

    def test_basic_creation(self) -> None:
        resp = CompletionResponse(
            model="harchos-llama-3.3-70b",
            choices=[CompletionChoice(text="Hello world")],
        )
        assert resp.choices[0].text == "Hello world"


class TestUsageModel:
    """Tests for Usage type model."""

    def test_defaults(self) -> None:
        u = Usage()
        assert u.prompt_tokens == 0
        assert u.completion_tokens == 0
        assert u.total_tokens == 0

    def test_custom(self) -> None:
        u = Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        assert u.total_tokens == 15


class TestWorkloadModel:
    """Tests for Workload type model."""

    def test_basic_creation(self) -> None:
        wl = Workload(id="wl_abc123", name="test-workload")
        assert wl.id == "wl_abc123"
        assert wl.name == "test-workload"
        assert wl.status == "pending"
        assert wl.type == "training"

    def test_with_spec(self) -> None:
        wl = Workload(
            id="wl_abc123",
            name="test-workload",
            spec=WorkloadSpec(name="test-workload", gpu_count=4),
        )
        assert wl.spec is not None
        assert wl.spec.gpu_count == 4

    def test_repr(self) -> None:
        wl = Workload(id="wl_abc123", name="test", status="running")
        r = repr(wl)
        assert "wl_abc123" in r
        assert "running" in r


class TestWorkloadSpecModel:
    """Tests for WorkloadSpec type model."""

    def test_defaults(self) -> None:
        spec = WorkloadSpec(name="test")
        assert spec.type == "training"
        assert spec.gpu_count == 1
        assert spec.cpu_cores == 1
        assert spec.priority == "normal"

    def test_min_name_length(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkloadSpec(name="")


class TestHubModel:
    """Tests for Hub type model."""

    def test_basic_creation(self) -> None:
        hub = Hub(id="hub_123", name="morocco-primary", region="morocco")
        assert hub.id == "hub_123"
        assert hub.region == "morocco"
        assert hub.status == "ready"

    def test_with_capacity(self) -> None:
        hub = Hub(
            id="hub_123", name="morocco-primary", region="morocco",
            capacity=HubCapacity(total_gpus=16, available_gpus=8),
        )
        assert hub.capacity is not None
        assert hub.capacity.gpu_utilization == 0.5

    def test_hub_capacity_utilization_zero_gpus(self) -> None:
        cap = HubCapacity(total_gpus=0, available_gpus=0)
        assert cap.gpu_utilization == 0.0

    def test_repr(self) -> None:
        hub = Hub(id="hub_123", name="test", region="morocco")
        assert "hub_123" in repr(hub)


class TestHubListModel:
    """Tests for HubList type model."""

    def test_empty(self) -> None:
        hl = HubList()
        assert len(hl) == 0

    def test_with_data(self) -> None:
        hl = HubList(items=[
            Hub(id="hub_1", name="hub1", region="morocco"),
            Hub(id="hub_2", name="hub2", region="france"),
        ], total=2)
        assert len(hl) == 2


class TestCarbonIntensityModel:
    """Tests for CarbonIntensity type model."""

    def test_is_green(self) -> None:
        ci = CarbonIntensity(
            zone="MA", carbon_intensity_gco2_kwh=100.0, renewable_percentage=80.0,
        )
        assert ci.is_green is True

    def test_is_not_green(self) -> None:
        ci = CarbonIntensity(
            zone="US", carbon_intensity_gco2_kwh=400.0, renewable_percentage=20.0,
        )
        assert ci.is_green is False

    def test_repr(self) -> None:
        ci = CarbonIntensity(
            zone="MA", carbon_intensity_gco2_kwh=100.0, renewable_percentage=80.0,
        )
        r = repr(ci)
        assert "GREEN" in r


class TestCarbonOptimalHubModel:
    """Tests for CarbonOptimalHub type model."""

    def test_is_deferred(self) -> None:
        hub = CarbonOptimalHub(
            action="defer",
            carbon_intensity_gco2_kwh=100.0,
            renewable_percentage=80.0,
            defer_hours=3.5,
        )
        assert hub.is_deferred is True

    def test_is_not_deferred(self) -> None:
        hub = CarbonOptimalHub(
            action="schedule",
            carbon_intensity_gco2_kwh=100.0,
            renewable_percentage=80.0,
        )
        assert hub.is_deferred is False


class TestPricingPlanModel:
    """Tests for PricingPlan type model."""

    def test_basic_creation(self) -> None:
        plan = PricingPlan(
            id="plan_1", name="Community A100",
            gpu_type="a100", price_per_gpu_hour=2.50,
            price_per_cpu_core_hour=0.10,
        )
        assert plan.gpu_type == "a100"
        assert plan.currency == "USD"


class TestCostEstimateModel:
    """Tests for CostEstimate type model."""

    def test_basic_creation(self) -> None:
        ce = CostEstimate(
            gpu_count=2, gpu_type="a100", hours=4.0,
            estimated_total=20.0,
        )
        assert ce.gpu_count == 2
        assert ce.estimated_total == 20.0


class TestUserInfoModel:
    """Tests for UserInfo type model."""

    def test_basic_creation(self) -> None:
        ui = UserInfo(id="usr_123", email="test@harchos.ai")
        assert ui.id == "usr_123"
        assert ui.plan == "community"

    def test_repr(self) -> None:
        ui = UserInfo(id="usr_123", email="test@harchos.ai")
        r = repr(ui)
        assert "usr_123" in r


class TestAPIKeyInfoModel:
    """Tests for APIKeyInfo type model."""

    def test_basic_creation(self) -> None:
        ki = APIKeyInfo(id="key_123", name="test-key", prefix="hsk_abcd")
        assert ki.revoked is False

    def test_repr(self) -> None:
        ki = APIKeyInfo(id="key_123", name="test-key", prefix="hsk_abcd")
        r = repr(ki)
        assert "key_123" in r


# ---------------------------------------------------------------------------
# InferenceResource tests
# ---------------------------------------------------------------------------

class TestInferenceResource:
    """Tests for the synchronous InferenceResource."""

    def test_client_has_inference(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "inference")
        assert isinstance(client.inference, InferenceResource)

    def test_inference_has_chat(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client.inference, "chat")
        assert hasattr(client.inference.chat, "completions")

    def test_inference_has_completions(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client.inference, "completions")

    def test_inference_has_models(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client.inference, "models")

    def test_models_list(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "object": "list",
            "data": [
                {"id": "harchos-llama-3.3-70b", "name": "LLaMA 3.3 70B", "owned_by": "harchos"},
            ],
        }
        resource = InferenceResource(client)
        result = resource.models.list()
        assert isinstance(result, ModelList)
        assert len(result) == 1
        assert result.data[0].id == "harchos-llama-3.3-70b"
        client.request.assert_called_once_with("GET", "/inference/models")

    def test_chat_completions_create(self) -> None:
        client = MagicMock(spec=HarchOS)
        client.request.return_value = {
            "id": "chatcmpl_abc",
            "object": "chat.completion",
            "model": "harchos-llama-3.3-70b",
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "Hello!"},
                 "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "carbon_footprint": {
                "gco2": 0.12, "hub_region": "morocco",
                "renewable_percentage": 75.0, "grid_intensity_gco2_kwh": 120.0,
            },
        }
        resource = InferenceResource(client)
        result = resource.chat.completions.create(
            model="harchos-llama-3.3-70b",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert isinstance(result, ChatCompletionResponse)
        assert result.content == "Hello!"
        assert result.carbon_footprint.gco2 == 0.12


class TestAsyncInferenceResource:
    """Tests for the asynchronous AsyncInferenceResource."""

    def test_async_client_has_inference(self) -> None:
        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert hasattr(client, "inference")
        assert isinstance(client.inference, AsyncInferenceResource)

    @pytest.mark.asyncio
    async def test_async_models_list(self) -> None:
        client = MagicMock(spec=AsyncHarchOS)
        client.request = AsyncMock(return_value={
            "object": "list",
            "data": [
                {"id": "model-1", "name": "Model 1"},
            ],
        })
        resource = AsyncInferenceResource(client)
        result = await resource.models.list()
        assert isinstance(result, ModelList)
        assert len(result) == 1
