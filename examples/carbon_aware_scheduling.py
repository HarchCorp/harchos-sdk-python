"""Example: Carbon-aware GPU scheduling.

Find the greenest hub and optimize workload scheduling
to minimize CO2 emissions — something no other GPU cloud
offers natively.
"""

from harchos import HarchOSClient

with HarchOSClient(api_key="hsk_your_api_key_here") as client:
    # 1. Check carbon intensity for Morocco
    ma = client.carbon.get_intensity("MA")
    print(f"Morocco carbon intensity: {ma.carbon_intensity_gco2_kwh} gCO2/kWh")
    if hasattr(ma, "renewable_percentage") and ma.renewable_percentage is not None:
        print(f"Renewable share: {ma.renewable_percentage:.1f}%")

    # 2. Find the greenest hub for 4x A100 training job
    optimal = client.carbon.optimal_hub(
        region="morocco",
        gpu_count=4,
        gpu_type="A100",
        carbon_max_gco2=100,
    )
    print(f"\nBest hub: {optimal.recommended_hub_name}")
    print(f"Carbon intensity: {optimal.carbon_intensity_gco2_kwh} gCO2/kWh")

    # 3. Run full optimization with carbon budget
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
    print(f"\nOptimization result:")
    print(f"  Action:    {result.action}")
    print(f"  Hub:       {getattr(result, 'recommended_hub', 'N/A')}")
    print(f"  CO2 saved: {getattr(result, 'carbon_saved_kg', 'N/A')} kg")
    if hasattr(result, "reason") and result.reason:
        print(f"  Reason:    {result.reason}")
