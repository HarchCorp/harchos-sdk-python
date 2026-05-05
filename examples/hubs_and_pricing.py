"""Example: Hub discovery and pricing.

List sovereign compute hubs, check capacity, and estimate costs.
"""

from harchos import HarchOSClient

with HarchOSClient(api_key="hsk_your_api_key_here") as client:
    # 1. List all hubs
    hubs = client.hubs.list()
    print(f"Sovereign Compute Hubs ({hubs.total}):\n")

    for hub in hubs.items:
        name = hub.spec.name if hasattr(hub, "spec") else getattr(hub, "name", "N/A")
        region = hub.spec.region if hasattr(hub, "spec") and hasattr(hub.spec, "region") else "N/A"
        status = hub.status if hasattr(hub, "status") else "N/A"

        print(f"  {name} ({region})")
        print(f"    Status: {status}")

        if hasattr(hub, "capacity") and hub.capacity:
            cap = hub.capacity
            total_gpus = getattr(cap, "gpu_total", getattr(cap, "total_gpus", "N/A"))
            util = getattr(cap, "gpu_utilization", None)
            util_str = f"{util:.0%}" if util is not None else "N/A"
            print(f"    GPUs: {total_gpus}  |  Utilization: {util_str}")

        if hasattr(hub, "spec") and hasattr(hub.spec, "tier"):
            print(f"    Tier: {hub.spec.tier}")

        print()

    # 2. Get pricing
    pricing = client.pricing.list()
    if hasattr(pricing, "items") and pricing.items:
        print("Pricing Plans:")
        for plan in pricing.items[:5]:
            name = getattr(plan, "name", "N/A")
            gpu_price = getattr(plan, "gpu_price_per_hour", "N/A")
            print(f"  {name}: ${gpu_price}/GPU/hr")
    else:
        print("  Contact sales for custom pricing")
