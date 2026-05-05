# HarchOS Python SDK v0.3.0

The official Python SDK for **HarchOS** — The Operating System for Sovereign AI Infrastructure.

## Features

- 🧠 **OpenAI-Compatible Inference** — `chat.completions.create()` and `completions.create()` with familiar interfaces
- 🌿 **Built-in Carbon Tracking** — Every response includes `carbon_footprint` with gCO2, hub region, renewable %
- 📡 **SSE Streaming** — Stream chat completions with `stream=True`
- 🔄 **Automatic Retries** — Exponential backoff with jitter on 429, 500, 502, 503
- ⚡ **Async Support** — `AsyncHarchOS` with full async/await interface
- 🎯 **Carbon Tracker** — Context manager to track total CO2 across multiple requests
- 📊 **Carbon Optimization** — Find the greenest hub, forecast carbon intensity, optimize workloads
- 🔑 **API Key Management** — Create, revoke, and inspect API keys
- 🖥️ **CLI** — Command-line interface for common operations
- 🛡️ **Type Safety** — Full Pydantic models for all responses

## Installation

```bash
pip install harchos

# With CLI support
pip install harchos[cli]

# With pandas support
pip install harchos[pandas]
```

## Quick Start

### Synchronous Client

```python
from harchos import HarchOS

client = HarchOS(api_key="hsk_...")

# Chat completion
response = client.inference.chat.completions.create(
    model="harchos-llama-3.3-70b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)

print(response.choices[0].message.content)

# Carbon tracking is built-in!
print(f"Carbon: {response.carbon_footprint.gco2}g CO2")
print(f"Renewable: {response.carbon_footprint.renewable_percentage}%")
print(f"Hub: {response.carbon_footprint.hub_region}")
```

### Async Client

```python
from harchos import AsyncHarchOS

async with AsyncHarchOS(api_key="hsk_...") as client:
    response = await client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.content)
```

### Streaming

```python
# Sync streaming
for chunk in client.inference.chat.completions.create(
    model="harchos-llama-3.3-70b",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True,
):
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# The final chunk includes carbon data
# chunk.carbon_footprint.gco2
```

### Carbon Tracker (Unique to HarchOS)

Track total carbon emissions across multiple inference requests:

```python
with client.carbon.tracker() as tracker:
    r1 = client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "Hello"}],
    )
    r2 = client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "How are you?"}],
    )
    for r in [r1, r2]:
        tracker.record(
            gco2=r.carbon_footprint.gco2,
            region=r.carbon_footprint.hub_region,
        )

print(f"Total CO2: {tracker.total_gco2}g")
print(f"Average per request: {tracker.avg_gco2_per_request:.2f}g")
print(f"Regions used: {tracker.regions}")
```

### Carbon Optimization

```python
# Get real-time carbon intensity
intensity = client.carbon.intensity(zone="MA")
print(f"Morocco: {intensity.carbon_intensity_gco2_kwh} gCO2/kWh")

# Find the greenest hub
optimal = client.carbon.optimal_hub(gpu_count=4, gpu_type="a100")
print(f"Best hub: {optimal.recommended_hub_name}")
print(f"Carbon saved: {optimal.estimated_carbon_saved_kg} kg")

# Get carbon forecast
forecast = client.carbon.forecast(zone="MA")
print(f"Green windows: {len(forecast.green_windows)}")

# Run carbon-aware optimization
result = client.carbon.optimize(
    workload_name="my-training-job",
    gpu_count=4,
    carbon_aware=True,
)
print(f"Action: {result.action}, Hub: {result.selected_hub_name}")
```

### Workloads

```python
# Create a workload
workload = client.workloads.create(
    name="my-training-job",
    type="training",
    gpu_count=4,
    gpu_type="a100",
    carbon_budget_grams=500.0,
)

# List workloads
workloads = client.workloads.list(status="running")

# Get a specific workload
wl = client.workloads.get("wl_123")

# Update a workload
updated = client.workloads.update("wl_123", priority="high")

# Delete a workload
client.workloads.delete("wl_123")
```

### Hubs

```python
# List hubs
hubs = client.hubs.list(region="morocco")

# Get a specific hub
hub = client.hubs.get("hub_123")
print(f"Hub: {hub.name}, Region: {hub.region}, GPUs: {hub.capacity.total_gpus}")
```

### Pricing

```python
# Estimate costs
estimate = client.pricing.estimate(
    gpu_count=4,
    gpu_type="a100",
    hours=24.0,
    region="morocco",
)
print(f"Estimated total: ${estimate.estimated_total} {estimate.currency}")

# List pricing plans
plans = client.pricing.plans(region="morocco")
```

### Auth

```python
# Get user info
user = client.auth.me()
print(f"User: {user.email}, Plan: {user.plan}")

# Create an API key
new_key = client.auth.create_api_key("my-ci-key")

# Revoke an API key
client.auth.revoke_api_key("key_123")
```

### Model Catalog

```python
models = client.inference.models.list()
for model in models:
    print(f"{model.id} — {model.type} (context: {model.context_length})")
```

### Error Handling

```python
from harchos import HarchOS, RateLimitError, AuthenticationError, NotFoundError

client = HarchOS(api_key="hsk_...")

try:
    response = client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "Hello"}],
    )
except RateLimitError as e:
    print(f"Rate limited! Code: {e.code}, Retry after: {e.retry_after}s")
    print(f"Docs: {e.doc_url}")
except AuthenticationError as e:
    print(f"Auth failed: {e.title} — {e.detail}")
except NotFoundError as e:
    print(f"Not found: {e.detail}")
```

## CLI

```bash
# Install CLI support
pip install harchos[cli]

# Set your API key
export HARCHOS_API_KEY=hsk_...

# Run inference
harchos inference --model harchos-llama-3.3-70b --message "Hello"

# Check carbon intensity
harchos carbon MA

# List workloads
harchos workloads

# List hubs
harchos hubs

# Show user info
harchos whoami

# Show version
harchos version
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `HARCHOS_API_KEY` | API key (starts with `hsk_`) | — |
| `HARCHOS_BASE_URL` | API base URL | `https://api.harchos.ai/v1` |
| `HARCHOS_TIMEOUT` | Request timeout in seconds | `30` |
| `HARCHOS_MAX_RETRIES` | Max retry attempts | `3` |

### Programmatic Configuration

```python
from harchos import HarchOS, Config

config = Config(
    api_key="hsk_...",
    base_url="https://api.harchos.ai/v1",
    timeout=60.0,
    max_retries=5,
)

client = HarchOS(config=config)
```

## API Reference

### Client Methods

| Method | Description |
|---|---|
| `client.inference.chat.completions.create(...)` | Chat completion (OpenAI-compatible) |
| `client.inference.completions.create(...)` | Text completion |
| `client.inference.models.list()` | List available models |
| `client.workloads.create(...)` | Create a workload |
| `client.workloads.list(...)` | List workloads |
| `client.workloads.get(id)` | Get a workload |
| `client.workloads.update(id, ...)` | Update a workload |
| `client.workloads.delete(id)` | Delete a workload |
| `client.hubs.list(...)` | List hubs |
| `client.hubs.get(id)` | Get a hub |
| `client.carbon.intensity(zone)` | Get carbon intensity |
| `client.carbon.optimize(...)` | Carbon-aware optimization |
| `client.carbon.forecast(zone)` | Carbon forecast |
| `client.carbon.dashboard()` | Carbon dashboard |
| `client.carbon.optimal_hub(...)` | Find greenest hub |
| `client.carbon.tracker()` | Carbon tracking context manager |
| `client.pricing.estimate(...)` | Cost estimation |
| `client.pricing.plans()` | List pricing plans |
| `client.auth.me()` | Get user info |
| `client.auth.create_api_key(name)` | Create API key |
| `client.auth.revoke_api_key(id)` | Revoke API key |

### Exception Hierarchy

```
HarchOSError
├── AuthenticationError   (E0401)
├── RateLimitError        (E0429)
├── NotFoundError         (E0404)
├── ValidationError       (E0400)
└── InferenceError        (E0500)
```

Each error has `.code`, `.title`, `.detail`, and `.doc_url` attributes.

## License

Apache-2.0
