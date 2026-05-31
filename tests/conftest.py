"""Shared test fixtures for the HarchOS SDK v0.3 test suite."""

from __future__ import annotations

import os
from typing import Any, Dict, Generator

import pytest

from harchos._config import Config
from harchos._client import HarchOS, AsyncHarchOS


# ---------------------------------------------------------------------------
# Configuration fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_config() -> Config:
    """Return a default Config with test API key."""
    return Config(api_key="hsk_testapikey1234567890")


@pytest.fixture
def custom_config() -> Config:
    """Return a Config with custom settings."""
    return Config(
        api_key="hsk_testapikey1234567890",
        base_url="https://custom.api.harchos.ai/v1",
        timeout=60.0,
        max_retries=5,
        default_headers={"X-Custom": "test"},
    )


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sync_client() -> HarchOS:
    """Return a synchronous HarchOS client with test config."""
    return HarchOS(api_key="hsk_testapikey1234567890")


@pytest.fixture
def async_client() -> AsyncHarchOS:
    """Return an AsyncHarchOS client with test config."""
    return AsyncHarchOS(api_key="hsk_testapikey1234567890")


# ---------------------------------------------------------------------------
# Sample data fixtures (v0.3 API response shapes)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_workload_data() -> Dict[str, Any]:
    """Return sample workload API response data matching v0.3 types."""
    return {
        "id": "wl_abc123",
        "name": "gpt4-training-run",
        "type": "training",
        "status": "running",
        "spec": {
            "name": "gpt4-training-run",
            "type": "training",
            "gpu_count": 4,
            "gpu_type": "a100",
            "cpu_cores": 16,
            "memory_gb": 64.0,
            "priority": "high",
            "carbon_budget_grams": 5000.0,
        },
        "hub_id": "hub_xyz789",
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:31:00Z",
    }


@pytest.fixture
def sample_hub_data() -> Dict[str, Any]:
    """Return sample hub API response data matching v0.3 types."""
    return {
        "id": "hub_xyz789",
        "name": "morocco-primary",
        "region": "morocco",
        "status": "ready",
        "tier": "enterprise",
        "capacity": {
            "total_gpus": 16,
            "available_gpus": 8,
            "total_cpu_cores": 256,
            "available_cpu_cores": 128,
            "total_memory_gb": 2048.0,
            "available_memory_gb": 1024.0,
        },
        "active_workloads": 4,
        "carbon_intensity_gco2_kwh": 120.0,
        "renewable_percentage": 75.0,
    }


@pytest.fixture
def sample_carbon_intensity_data() -> Dict[str, Any]:
    """Return sample carbon intensity API response data."""
    return {
        "zone": "MA",
        "zone_name": "Morocco",
        "carbon_intensity_gco2_kwh": 150.0,
        "renewable_percentage": 65.0,
        "fossil_percentage": 35.0,
        "updated_at": "2024-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Return sample user info API response data."""
    return {
        "id": "usr_abc123",
        "email": "test@harchos.ai",
        "name": "Test User",
        "plan": "community",
        "created_at": "2024-01-10T08:00:00Z",
    }


@pytest.fixture
def sample_api_key_data() -> Dict[str, Any]:
    """Return sample API key info response data."""
    return {
        "id": "key_abc123",
        "name": "test-key",
        "prefix": "hsk_abcd",
        "created_at": "2024-01-10T08:00:00Z",
        "revoked": False,
    }


@pytest.fixture
def sample_model_data() -> Dict[str, Any]:
    """Return sample model info response data."""
    return {
        "id": "harchos-llama-3.3-70b",
        "name": "HarchOS LLaMA 3.3 70B",
        "owned_by": "harchos",
        "type": "chat",
        "context_length": 8192,
    }


@pytest.fixture
def sample_chat_completion_data() -> Dict[str, Any]:
    """Return sample chat completion response data."""
    return {
        "id": "chatcmpl_abc123",
        "object": "chat.completion",
        "created": 1705312000,
        "model": "harchos-llama-3.3-70b",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello! How can I help?"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        "carbon_footprint": {
            "gco2_per_request": 0.12,
            "hub_region": "morocco",
            "renewable_percentage": 75.0,
            "carbon_intensity_gco2_kwh": 120.0,
        },
    }


# ---------------------------------------------------------------------------
# Environment fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove HARCHOS_ environment variables for the test duration."""
    harchos_vars = [k for k in os.environ if k.startswith("HARCHOS_")]
    saved = {k: os.environ.pop(k) for k in harchos_vars}
    yield
    os.environ.update(saved)
    for k in harchos_vars:
        if k not in saved:
            os.environ.pop(k, None)
