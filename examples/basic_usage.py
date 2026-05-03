"""Example: Basic synchronous usage of the HarchOS SDK."""

from harchos import HarchOSClient, WorkloadSpec, WorkloadType

# Create a client with sovereign defaults
# region="morocco", sovereignty="strict", carbon_aware=True
with HarchOSClient(api_key="hsk_your_api_key_here") as client:
    # Check API health
    health = client.health()
    print(f"HarchOS API Status: {health.status}")
    print(f"Version: {health.version}")
    print(f"Region: {health.region}")

    # List workloads
    workloads = client.workloads.list()
    print(f"\nFound {workloads.total} workloads:")
    for wl in workloads.items:
        print(f"  - {wl.metadata.name} ({wl.status})")

    # List models
    models = client.models.list()
    print(f"\nFound {models.total} models:")
    for model in models.items:
        print(f"  - {model.spec.name} [{model.spec.task}]")

    # List hubs
    hubs = client.hubs.list()
    print(f"\nFound {hubs.total} hubs:")
    for hub in hubs.items:
        print(f"  - {hub.spec.name} ({hub.status})")
        if hub.capacity:
            print(f"    GPU utilization: {hub.capacity.gpu_utilization:.0%}")

    # Get energy report
    if workloads.items:
        wl_id = workloads.items[0].metadata.id
        try:
            report = client.energy.get_report(wl_id)
            print(f"\nEnergy report for {wl_id}:")
            print(f"  CO2: {report.consumption.co2_grams}g")
            print(f"  PUE: {report.consumption.pue}")
            print(f"  Renewable: {report.consumption.renewable_fraction:.0%}")
        except Exception as e:
            print(f"Energy report unavailable: {e}")
