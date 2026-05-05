<div align="center">

# HarchOS SDK for Python

[![PyPI version](https://img.shields.io/pypi/v/harchos.svg)](https://pypi.org/project/harchos/)
[![Python versions](https://img.shields.io/pypi/pyversions/harchos.svg)](https://pypi.org/project/harchos/)
[![License](https://img.shields.io/github/license/HarchCorp/harchos-sdk-python.svg)](https://github.com/HarchCorp/harchos-sdk-python/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/harchos.svg)](https://pypi.org/project/harchos/)

**The Operating System for Sovereign AI Infrastructure**

Carbon-aware GPU orchestration with built-in sovereignty enforcement.

[Install](#installation) · [Quick Start](#quick-start) · [CLI](#cli) · [Examples](#examples) · [API Reference](#api-reference)

</div>

---

## Why HarchOS?

| Feature | Modal | Replicate | Together | **HarchOS** |
|---------|-------|-----------|----------|-------------|
| Carbon-Aware Scheduling | ❌ | ❌ | ❌ | **✅** |
| Data Sovereignty | ❌ | ❌ | ❌ | **✅** |
| Green Window Detection | ❌ | ❌ | ❌ | **✅** |
| Carbon Budget Enforcement | ❌ | ❌ | ❌ | **✅** |
| Sovereign Compute Hubs | ❌ | ❌ | ❌ | **✅** |
| CLI | ✅ | ✅ | ✅ | **✅** |
| PyPI Package | ✅ | ✅ | ✅ | **✅** |
| Async Support | ✅ | ❌ | ✅ | **✅** |

HarchOS is the **only** GPU orchestration platform with native carbon-aware scheduling and sovereignty enforcement. Every API call respects data residency constraints and carbon budgets by default.

---

## Installation

```bash
pip install harchos
```

For development:

```bash
pip install harchos[dev]
```

---

## Quick Start

### 30-Second Setup

```python
from harchos import HarchOSClient

# Create client with sovereign defaults
# region="morocco", sovereignty="strict", carbon_aware=True
client = HarchOSClient(api_key="hsk_your_api_key_here")

with client:
    # Health check
    health = client.health()
    print(f"Status: {health.status}")

    # Carbon intensity (exclusive feature!)
    carbon = client.carbon.get_intensity("MA")
    print(f"Morocco: {carbon.carbon_intensity_gco2_kwh} gCO2/kWh")

    # List sovereign hubs
    hubs = client.hubs.list()
    print(f"Hubs: {hubs.total}")

    # Available models
    models = client.models.list()
    print(f"Models: {models.total}")
```

### From Environment Variables

```bash
export HARCHOS_API_KEY="hsk_..."
export HARCHOS_REGION="morocco"
export HARCHOS_SOVEREIGNTY="strict"
```

```python
from harchos import HarchOSClient

client = HarchOSClient.from_env()
```

### Async Usage

```python
import asyncio
from harchos import HarchOSClient

async def main():
    async with HarchOSClient(api_key="hsk_...") as client:
        workloads = await client.workloads.async_list()
        carbon = await client.carbon.async_get_intensity("MA")

asyncio.run(main())
```

---

## CLI

The `harchos` command-line tool gives you instant access to your infrastructure:

```bash
# Install
pip install harchos

# Set API key
export HARCHOS_API_KEY="hsk_..."

# Check API status
harchos status

# Carbon intensity for Morocco
harchos carbon MA

# Carbon intensity for all zones
harchos carbon

# List sovereign compute hubs
harchos hubs

# List workloads
harchos workloads
harchos workloads --status running

# List AI models
harchos models

# Run carbon-aware optimizer
harchos optimize --name "training-job" --gpus 4 --gpu-type A100 --region morocco

# Find green scheduling windows
harchos green-windows --region morocco

# Show configuration
harchos config show

# Override API key or URL
harchos --api-key hsk_... status
harchos --base-url https://custom.api/v1 status
```

---

## Examples

| Example | Description |
|---------|-------------|
| [`quickstart.py`](examples/quickstart.py) | 30-second setup guide |
| [`basic_usage.py`](examples/basic_usage.py) | Sync usage with all resources |
| [`async_streaming.py`](examples/async_streaming.py) | Async + SSE streaming |
| [`carbon_aware_scheduling.py`](examples/carbon_aware_scheduling.py) | Carbon-aware GPU scheduling |
| [`sovereign_deployment.py`](examples/sovereign_deployment.py) | Strict data residency |
| [`green_windows_monitoring.py`](examples/green_windows_monitoring.py) | Green scheduling windows |
| [`hubs_and_pricing.py`](examples/hubs_and_pricing.py) | Hub discovery and pricing |
| [`cli_usage.sh`](examples/cli_usage.sh) | CLI command examples |

---

## API Reference

### Carbon-Aware Scheduling

The feature that sets HarchOS apart — native carbon-aware GPU orchestration:

```python
# Real-time carbon intensity
intensity = client.carbon.get_intensity("MA")  # Morocco

# Find the greenest hub for your workload
optimal = client.carbon.optimal_hub(
    region="morocco",
    gpu_count=4,
    gpu_type="A100",
    carbon_max_gco2=100,
)

# Full carbon-aware optimization
result = client.carbon.optimize(
    workload_name="gpt4-fine-tune",
    workload_type="training",
    gpu_count=4,
    gpu_type="A100",
    carbon_aware=True,
    carbon_max_gco2=80,
    region="morocco",
    estimated_duration_hours=6.0,
)

# Carbon intensity forecast
forecast = client.carbon.get_forecast("MA", hours=24)

# Carbon dashboard
dashboard = client.carbon.get_dashboard()
```

### Sovereignty & Data Residency

```python
from harchos import WorkloadSpec, WorkloadType, DataResidencyPolicy, ComputePriority
from harchos.models.sovereignty import SovereigntyLevel

spec = WorkloadSpec(
    name="sovereign-training",
    type=WorkloadType.TRAINING,
    priority=ComputePriority.HIGH,
    sovereignty_level=SovereigntyLevel.STRICT,
    data_residency=DataResidencyPolicy(
        allowed_regions=["morocco"],
        data_classification="restricted",
        encryption_at_rest=True,
        encryption_in_transit=True,
        key_management_region="morocco",
    ),
    carbon_budget_grams=5000.0,
)
```

### Workloads

```python
# List workloads with filters
workloads = client.workloads.list(status="running", workload_type="training")

# Get specific workload
wl = client.workloads.get("wl_abc123")

# Cancel / pause / resume
client.workloads.cancel("wl_abc123")
client.workloads.pause("wl_abc123")
client.workloads.resume("wl_abc123")
```

### Hubs

```python
# List sovereign compute hubs
hubs = client.hubs.list(region="morocco")

# Hub capacity
capacity = client.hubs.capacity("hub_xyz789")
print(f"GPU utilization: {capacity.gpu_utilization:.0%}")
```

### Models

```python
# List AI models
models = client.models.list(task="text_generation")

# Deploy / undeploy
client.models.deploy("mdl_def456", hub_id="hub_xyz789")
client.models.undeploy("mdl_def456")
```

### Energy & Green Windows

```python
# Energy report
report = client.energy.get_report("wl_abc123")
print(f"CO2: {report.consumption.co2_grams}g")

# Green scheduling windows
windows = client.energy.get_green_windows(region="morocco")
for w in windows:
    print(f"Green: {w.start} - {w.end} ({w.renewable_percentage}% renewable)")
```

### Streaming

```python
async with HarchOSClient(api_key="hsk_...") as client:
    async for event in client.stream(
        "POST", "/models/mdl_xxx/inference",
        json={"prompt": "Hello", "stream": True}
    ):
        print(event)
```

### Pagination

```python
# Auto-paginate through all hubs
for hub in client.paginate(client.hubs.list):
    print(hub.spec.name)

# Async pagination
async for hub in client.async_paginate(client.hubs.async_list):
    print(hub.spec.name)
```

### Error Handling

```python
from harchos import (
    HarchOSClient,
    RateLimitError,
    NotFoundError,
    SovereigntyError,
    CarbonBudgetExceededError,
)

try:
    wl = client.workloads.get("nonexistent")
except NotFoundError:
    print("Not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except SovereigntyError as e:
    print(f"Sovereignty violation: {e}")
except CarbonBudgetExceededError as e:
    print(f"Carbon budget exceeded: {e.actual_grams}g > {e.budget_grams}g")
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HARCHOS_API_KEY` | — | API key (required) |
| `HARCHOS_BASE_URL` | `https://harchos-api-production.up.railway.app/v1` | API base URL |
| `HARCHOS_REGION` | `morocco` | Data residency region |
| `HARCHOS_SOVEREIGNTY` | `strict` | Sovereignty level |
| `HARCHOS_TIMEOUT` | `30` | Request timeout (seconds) |
| `HARCHOS_MAX_RETRIES` | `3` | Max retry attempts |

### Named Profiles

```python
# Save current config as a profile
client.config.save_as_profile("production")

# Load from profile
from harchos import HarchOSConfig
config = HarchOSConfig.from_profile("production")
```

Profiles are stored in `~/.harchos/profiles.json`.

---

## Requirements

- Python 3.9+
- httpx >= 0.25.0
- pydantic >= 2.0.0

---

## Development

```bash
# Clone
git clone https://github.com/HarchCorp/harchos-sdk-python.git
cd harchos-sdk-python

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## Links

- [HarchOS Documentation](https://docs.harchos.io)
- [API Reference](https://api.harchos.io/docs)
- [PyPI Package](https://pypi.org/project/harchos/)
- [GitHub Repository](https://github.com/HarchCorp/harchos-sdk-python)
- [Report Issues](https://github.com/HarchCorp/harchos-sdk-python/issues)

---

<div align="center">

**Built with 🌍 by HarchCorp — Sovereign AI Infrastructure for Africa and Beyond**

</div>
