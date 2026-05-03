# HarchOS SDK for Python

[![PyPI version](https://img.shields.io/pypi/v/harchos.svg)](https://pypi.org/project/harchos/)
[![Python versions](https://img.shields.io/pypi/pyversions/harchos.svg)](https://pypi.org/project/harchos/)
[![License](https://img.shields.io/github/license/HarchCorp/harchos-sdk-python.svg)](https://github.com/HarchCorp/harchos-sdk-python/blob/main/LICENSE)
[![CI](https://github.com/HarchCorp/harchos-sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/HarchCorp/harchos-sdk-python/actions/workflows/ci.yml)

**The Official Python SDK for HarchOS** — The Operating System for Sovereign AI Infrastructure.

## Features

- 🌍 **Sovereign Defaults** — `region="morocco"`, `sovereignty="strict"`, `carbon_aware=True` out of the box
- ⚡ **Async & Sync** — Full support for both `async/await` and synchronous patterns
- 🔄 **Smart Retries** — Exponential backoff with jitter, rate-limit awareness, and carbon-aware scheduling
- 🔐 **Authentication** — API key and bearer token support with automatic refresh
- 📊 **Streaming** — SSE (Server-Sent Events) streaming with async generators
- 🏗️ **Typed Models** — Pydantic v2 models with validators for all resource types
- 🌱 **Carbon-Aware** — Built-in energy monitoring and green scheduling windows
- 🛡️ **Sovereignty Enforcement** — Data residency policies, carbon budgets, compliance frameworks

## Installation

```bash
pip install harchos
```

For development dependencies:

```bash
pip install harchos[dev]
```

## Quick Start

### Synchronous Usage

```python
from harchos import HarchOSClient

with HarchOSClient(api_key="hsk_your_api_key_here") as client:
    # List workloads
    workloads = client.workloads.list()
    for wl in workloads.items:
        print(f"{wl.metadata.name}: {wl.status}")

    # Check API health
    health = client.health()
    print(f"API status: {health.status}")
```

### Asynchronous Usage

```python
import asyncio
from harchos import HarchOSClient

async def main():
    async with HarchOSClient(api_key="hsk_your_api_key_here") as client:
        # List workloads
        workloads = await client.workloads.async_list()
        for wl in workloads.items:
            print(f"{wl.metadata.name}: {wl.status}")

        # Create a workload
        from harchos import WorkloadSpec, WorkloadType

        spec = WorkloadSpec(
            name="my-training-job",
            type=WorkloadType.TRAINING,
            compute={"gpu_count": 4, "gpu_type": "a100"},
        )
        workload = await client.workloads.async_create(spec)

asyncio.run(main())
```

### Configuration

```python
from harchos import HarchOSClient

# Custom region and sovereignty level
client = HarchOSClient(
    api_key="hsk_...",
    region="uae",
    sovereignty="moderate",
    carbon_aware=True,
    timeout=60.0,
    max_retries=5,
)

# Or use a named profile
client = HarchOSClient(profile="production")
```

### Environment Variables

Set configuration via environment variables prefixed with `HARCHOS_`:

```bash
export HARCHOS_API_KEY="hsk_..."
export HARCHOS_REGION="morocco"
export HARCHOS_SOVEREIGNTY="strict"
```

## Resource Modules

### Workloads

```python
# List workloads with filters
workloads = client.workloads.list(
    status="running",
    workload_type="training",
    hub_id="hub_xyz789",
)

# Get a specific workload
wl = client.workloads.get("wl_abc123")

# Cancel a workload
client.workloads.cancel("wl_abc123")

# Pause and resume
client.workloads.pause("wl_abc123")
client.workloads.resume("wl_abc123")
```

### Models

```python
# List AI models
models = client.models.list(task="text_generation")

# Deploy a model
client.models.deploy("mdl_def456", hub_id="hub_xyz789")

# Undeploy
client.models.undeploy("mdl_def456")
```

### Hubs

```python
# List sovereign compute hubs
hubs = client.hubs.list(region="morocco")

# Get hub capacity
capacity = client.hubs.capacity("hub_xyz789")
print(f"GPU utilization: {capacity.gpu_utilization:.0%}")

# Scale a hub
client.hubs.scale("hub_xyz789", target_gpu_count=24)
```

### Energy

```python
# Get energy report for a resource
report = client.energy.get_report("wl_abc123")
print(f"CO2: {report.consumption.co2_grams}g")

# Get green scheduling windows
windows = client.energy.get_green_windows(region="morocco")
for w in windows:
    print(f"Green window: {w.start} - {w.end} ({w.renewable_percentage}% renewable)")
```

## Sovereignty & Carbon

HarchOS is built for sovereign AI infrastructure. Every operation respects data
residency constraints and carbon budgets:

```python
from harchos import WorkloadSpec, WorkloadType, DataResidencyPolicy

# Create a workload with strict sovereignty
spec = WorkloadSpec(
    name="sovereign-training",
    type=WorkloadType.TRAINING,
    sovereignty_level="strict",
    data_residency=DataResidencyPolicy(
        allowed_regions=["morocco"],
        data_classification="restricted",
        encryption_at_rest=True,
    ),
    carbon_budget_grams=5000.0,
)
```

## Streaming

```python
async with HarchOSClient(api_key="hsk_...") as client:
    async for event in client.stream("POST", "/models/mdl_xxx/inference", json={"prompt": "Hello"}):
        print(event)
```

## Error Handling

```python
from harchos import HarchOSClient, RateLimitError, NotFoundError, SovereigntyError

try:
    wl = client.workloads.get("nonexistent")
except NotFoundError:
    print("Workload not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except SovereigntyError as e:
    print(f"Sovereignty violation: {e}")
```

## Requirements

- Python 3.9+
- httpx >= 0.25.0
- pydantic >= 2.0.0

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Links

- [HarchOS Documentation](https://docs.harchos.io)
- [API Reference](https://api.harchos.io/docs)
- [PyPI Package](https://pypi.org/project/harchos/)
