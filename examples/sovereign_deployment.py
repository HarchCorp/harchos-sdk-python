"""Example: Sovereign AI deployment with strict data residency.

Deploy workloads that MUST stay within Morocco — data never
leaves the country. This is HarchOS's unique sovereignty feature.
"""

from harchos import (
    HarchOSClient,
    WorkloadSpec,
    WorkloadType,
    DataResidencyPolicy,
    ComputePriority,
)
from harchos.models.sovereignty import SovereigntyLevel

with HarchOSClient(
    api_key="hsk_your_api_key_here",
    region="morocco",
    sovereignty="strict",
    carbon_aware=True,
) as client:
    # Create a sovereign workload with strict data residency
    spec = WorkloadSpec(
        name="sovereign-llm-training",
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
        carbon_budget_grams=10000.0,  # Max 10kg CO2
        compute={
            "gpu_count": 8,
            "gpu_type": "H100",
            "cpu_cores": 32,
            "memory_gb": 128.0,
        },
    )

    print(f"Workload spec: {spec.name}")
    print(f"  Type:        {spec.type}")
    print(f"  Sovereignty: {spec.sovereignty_level}")
    print(f"  Regions:     {spec.data_residency.allowed_regions}")
    print(f"  Carbon max:  {spec.carbon_budget_grams}g CO2")
    print(f"  GPU:         {spec.compute.get('gpu_count')}x {spec.compute.get('gpu_type')}")

    # List running workloads
    workloads = client.workloads.list(status="running")
    print(f"\nRunning workloads: {workloads.total}")

    # Check sovereignty compliance
    for wl in workloads.items[:5]:
        print(f"  {wl.metadata.name}: {wl.status}")
