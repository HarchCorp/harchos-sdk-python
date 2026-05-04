"""Shared test fixtures for the HarchOS SDK test suite."""

from __future__ import annotations

import os
from typing import Any, Dict, Generator

import pytest

from harchos._http import HttpTransport
from harchos.auth import Authenticator
from harchos.config import HarchOSConfig

# ---------------------------------------------------------------------------
# Configuration fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_config() -> HarchOSConfig:
    """Return a default HarchOSConfig with sovereign defaults."""
    return HarchOSConfig(api_key="hsk_testapikey1234567890")


@pytest.fixture
def custom_config() -> HarchOSConfig:
    """Return a HarchOSConfig with custom settings."""
    return HarchOSConfig(
        api_key="hsk_testapikey1234567890",
        base_url="https://custom.api.harchos.io/v1",
        region="uae",
        sovereignty="moderate",
        carbon_aware=False,
        timeout=60.0,
        max_retries=5,
    )


# ---------------------------------------------------------------------------
# Authenticator fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def authenticator() -> Authenticator:
    """Return an Authenticator with a test API key."""
    return Authenticator(api_key="hsk_testapikey1234567890")


@pytest.fixture
def empty_authenticator() -> Authenticator:
    """Return an Authenticator with no credentials."""
    return Authenticator()


# ---------------------------------------------------------------------------
# Transport fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def transport(default_config: HarchOSConfig, authenticator: Authenticator) -> HttpTransport:
    """Return an HttpTransport with test config and auth."""
    return HttpTransport(config=default_config, auth=authenticator)


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_workload_data() -> Dict[str, Any]:
    """Return sample workload API response data."""
    return {
        "metadata": {
            "id": "wl_abc123",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z",
            "labels": {"team": "ml", "env": "prod"},
            "annotations": {},
        },
        "spec": {
            "name": "gpt4-training-run",
            "type": "training",
            "compute": {
                "gpu_count": 4,
                "gpu_type": "a100",
                "cpu_cores": 16,
                "memory_gb": 64.0,
                "storage_gb": 500.0,
            },
            "priority": "high",
            "sovereignty_level": "strict",
            "carbon_budget_grams": 5000.0,
        },
        "status": "running",
        "hub_id": "hub_xyz789",
        "started_at": "2024-01-15T10:31:00Z",
    }


@pytest.fixture
def sample_model_data() -> Dict[str, Any]:
    """Return sample model API response data."""
    return {
        "metadata": {
            "id": "mdl_def456",
            "created_at": "2024-01-10T08:00:00Z",
            "labels": {},
            "annotations": {},
        },
        "spec": {
            "name": "harchos-llm-v1",
            "framework": "pytorch",
            "task": "text_generation",
            "version": "1.0.0",
        },
        "status": "deployed",
        "framework": "pytorch",
        "task": "text_generation",
        "capabilities": {
            "max_context_length": 8192,
            "max_output_tokens": 2048,
            "supports_streaming": True,
        },
    }


@pytest.fixture
def sample_hub_data() -> Dict[str, Any]:
    """Return sample hub API response data."""
    return {
        "metadata": {
            "id": "hub_xyz789",
            "created_at": "2024-01-05T12:00:00Z",
            "labels": {"region": "morocco"},
            "annotations": {},
        },
        "spec": {
            "name": "morocco-primary",
            "region": "morocco",
            "tier": "enterprise",
            "gpu_types": ["a100", "h100"],
            "auto_scale": True,
            "min_gpu_count": 2,
            "max_gpu_count": 32,
        },
        "status": "ready",
        "capacity": {
            "total_gpus": 16,
            "available_gpus": 8,
            "total_cpu_cores": 256,
            "available_cpu_cores": 128,
            "total_memory_gb": 2048.0,
            "available_memory_gb": 1024.0,
            "total_storage_gb": 10000.0,
            "available_storage_gb": 5000.0,
        },
    }


@pytest.fixture
def sample_energy_data() -> Dict[str, Any]:
    """Return sample energy report API response data."""
    return {
        "resource_id": "wl_abc123",
        "resource_type": "workload",
        "region": "morocco",
        "consumption": {
            "kwh_consumed": 150.5,
            "co2_grams": 45.2,
            "pue": 1.15,
            "renewable_fraction": 0.65,
            "grid_intensity_gco2_kwh": 300.0,
            "period_start": "2024-01-15T10:00:00Z",
            "period_end": "2024-01-15T11:00:00Z",
        },
        "green_windows": [],
        "recommendations": ["Schedule heavy workloads between 10:00-14:00 for solar peak"],
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
