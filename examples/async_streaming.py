"""Example: Async usage with streaming support."""

import asyncio
from datetime import datetime

from harchos import (
    HarchOSClient,
    WorkloadSpec,
    WorkloadType,
    DataResidencyPolicy,
    ComputePriority,
)
from harchos.models.sovereignty import SovereigntyLevel


async def main() -> None:
    """Demonstrate async operations with the HarchOS SDK."""

    # Create an async client with custom sovereignty settings
    async with HarchOSClient(
        api_key="hsk_your_api_key_here",
        region="morocco",
        sovereignty="strict",
        carbon_aware=True,
    ) as client:
        # Health check
        health = await client.async_health()
        print(f"HarchOS Health: {health.status}")

        # Create a sovereign workload
        spec = WorkloadSpec(
            name="gpt4-fine-tune",
            type=WorkloadType.FINE_TUNING,
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
            compute={
                "gpu_count": 4,
                "gpu_type": "a100",
                "cpu_cores": 16,
                "memory_gb": 64.0,
            },
        )
        print(f"\nCreating workload: {spec.name}")

        # List workloads
        workloads = await client.workloads.async_list(status="running")
        print(f"Running workloads: {workloads.total}")

        # Get green scheduling windows
        windows = await client.energy.async_get_green_windows(
            region="morocco",
            min_renewable_percentage=60.0,
        )
        print(f"\nGreen scheduling windows ({len(windows)}):")
        for window in windows:
            print(
                f"  {window.start.strftime('%H:%M')}-{window.end.strftime('%H:%M')} "
                f"({window.renewable_percentage:.0f}% renewable, "
                f"{window.estimated_co2_grams_per_kwh:.0f}g CO2/kWh)"
            )

        # Stream inference (example)
        print("\nStreaming inference:")
        try:
            async for event in client.stream(
                "POST",
                "/models/mdl_example/inference",
                json={"prompt": "Explain sovereign AI", "stream": True},
            ):
                if isinstance(event, dict):
                    text = event.get("text", "")
                    if text:
                        print(text, end="", flush=True)
            print()
        except Exception as e:
            print(f"Streaming not available: {e}")


if __name__ == "__main__":
    asyncio.run(main())
