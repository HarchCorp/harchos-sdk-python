"""Example: Quickstart — Get running in 30 seconds.

The fastest way to start using HarchOS SDK.
"""

from harchos import HarchOSClient

# Option 1: Explicit API key
client = HarchOSClient(api_key="hsk_your_api_key_here")

# Option 2: From environment variable
# export HARCHOS_API_KEY=hsk_your_api_key_here
# client = HarchOSClient.from_env()

with client:
    # Health check
    health = client.health()
    print(f"HarchOS Status: {health.status}")

    # List hubs
    hubs = client.hubs.list()
    print(f"Available Hubs: {hubs.total}")

    # Check carbon intensity (HarchOS exclusive!)
    carbon = client.carbon.get_intensity("MA")
    print(f"Morocco Carbon: {carbon.carbon_intensity_gco2_kwh} gCO2/kWh")

    # List models
    models = client.models.list()
    print(f"Available Models: {models.total}")

print("\nDone! Explore more at https://docs.harchos.io")
