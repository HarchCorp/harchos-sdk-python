"""Example: Green scheduling windows and energy monitoring.

Find the best time to run GPU-heavy workloads when renewable
energy is at its peak. Save CO2 and money.
"""

import asyncio
from harchos import HarchOSClient


async def main():
    async with HarchOSClient(
        api_key="hsk_your_api_key_here",
        carbon_aware=True,
    ) as client:
        # 1. Get green scheduling windows for Morocco
        windows = await client.energy.async_get_green_windows(
            region="morocco",
            min_renewable_percentage=60.0,
        )

        print("Green Scheduling Windows:")
        print("-" * 60)
        for w in windows[:5]:
            renewable = getattr(w, "renewable_percentage", 0)
            co2 = getattr(w, "estimated_co2_grams_per_kwh", "N/A")
            start = getattr(w, "start", "N/A")
            end = getattr(w, "end", "N/A")
            print(f"  {start} → {end}")
            print(f"    Renewable: {renewable:.1f}%  |  CO2: {co2} g/kWh")

        # 2. Get carbon forecast for next 24h
        forecast = await client.carbon.async_get_forecast("MA", hours=24)
        print(f"\nCarbon Forecast (MA, 24h):")
        print("-" * 60)
        if hasattr(forecast, "forecast_points") and forecast.forecast_points:
            for point in forecast.forecast_points[:8]:
                intensity = getattr(point, "carbon_intensity_gco2_kwh", "N/A")
                dt = getattr(point, "datetime", "N/A")
                print(f"  {dt}: {intensity} gCO2/kWh")

        # 3. Get carbon dashboard
        dashboard = await client.carbon.async_get_dashboard()
        print(f"\nCarbon Dashboard:")
        print("-" * 60)
        if hasattr(dashboard, "metrics"):
            metrics = dashboard.metrics
            print(f"  Total CO2 saved: {getattr(metrics, 'total_carbon_saved_kg', 'N/A')} kg")
            print(f"  Green schedules: {getattr(metrics, 'green_schedules_count', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
