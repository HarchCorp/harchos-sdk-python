"""HarchOS CLI — Command-line interface for sovereign AI infrastructure.

Usage::

    harchos status          # Check API health and connectivity
    harchos carbon MA       # Real-time carbon intensity for Morocco
    harchos hubs            # List sovereign compute hubs
    harchos workloads       # List running workloads
    harchos models          # List available AI models
    harchos optimize        # Run carbon-aware scheduling optimizer
    harchos green-windows   # Find green scheduling windows
    harchos config show     # Show current configuration
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import __version__


def _get_client(api_key: Optional[str] = None, base_url: Optional[str] = None):
    """Create a HarchOSClient from args or environment."""
    from .client import HarchOSClient

    kwargs: Dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url

    if not kwargs.get("api_key") and not os.environ.get("HARCHOS_API_KEY"):
        print(
            "Error: No API key provided. Set HARCHOS_API_KEY or use --api-key\n"
            "  export HARCHOS_API_KEY=hsk_your_key_here\n"
            "  harchos --api-key hsk_your_key_here status"
        )
        sys.exit(1)

    return HarchOSClient(**kwargs)


def _format_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> str:
    """Format data as a simple text table."""
    if title:
        lines = [f"\n  {title}", "  " + "=" * len(title)]
    else:
        lines = []

    # Calculate column widths
    all_rows = [headers] + rows
    widths = [max(len(str(row[i])) for row in all_rows) for i in range(len(headers))]

    # Header
    header_line = "  ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    separator = "  ".join("-" * w for w in widths)

    lines.append("  " + header_line)
    lines.append("  " + separator)

    # Rows
    for row in rows:
        line = "  ".join(str(v).ljust(w) for v, w in zip(row, widths))
        lines.append("  " + line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> None:
    """Check HarchOS API health and connectivity."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            health = client.health()
            print(f"\n  HarchOS API Status")
            print(f"  {'=' * 30}")
            print(f"  Status:   {health.status}")
            if hasattr(health, "version") and health.version:
                print(f"  Version:  {health.version}")
            if hasattr(health, "region") and health.region:
                print(f"  Region:   {health.region}")
            print(f"  SDK:      v{__version__}")
            print(f"  URL:      {client.config.base_url}")
            print()
    except Exception as e:
        print(f"  Error connecting to HarchOS API: {e}")
        sys.exit(1)


def cmd_carbon(args: argparse.Namespace) -> None:
    """Get carbon intensity for a zone."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            if args.zone:
                zone_data = client.carbon.get_intensity(args.zone)
                print(f"\n  Carbon Intensity: {zone_data.zone}")
                print(f"  {'=' * 35}")
                print(f"  Zone:             {zone_data.zone}")
                print(f"  Intensity:        {zone_data.carbon_intensity_gco2_kwh} gCO2/kWh")
                if hasattr(zone_data, "renewable_percentage") and zone_data.renewable_percentage is not None:
                    print(f"  Renewable:        {zone_data.renewable_percentage:.1f}%")
                if hasattr(zone_data, "fossil_percentage") and zone_data.fossil_percentage is not None:
                    print(f"  Fossil:           {zone_data.fossil_percentage:.1f}%")
                if hasattr(zone_data, "updated_at") and zone_data.updated_at:
                    print(f"  Updated:          {zone_data.updated_at}")
                print()
            else:
                # List all zones
                zones = client.carbon.list_intensities()
                rows = []
                for z in zones.zones if hasattr(zones, "zones") else [zones]:
                    intensity = getattr(z, "carbon_intensity_gco2_kwh", "N/A")
                    renewable = getattr(z, "renewable_percentage", None)
                    renewable_str = f"{renewable:.1f}%" if renewable is not None else "N/A"
                    rows.append([z.zone, str(intensity), renewable_str])

                if rows:
                    print(_format_table(
                        ["Zone", "gCO2/kWh", "Renewable"],
                        rows,
                        title="Carbon Intensity by Zone",
                    ))
                    print()
                else:
                    print("  No carbon intensity data available.")
    except Exception as e:
        print(f"  Error fetching carbon data: {e}")
        sys.exit(1)


def cmd_hubs(args: argparse.Namespace) -> None:
    """List sovereign compute hubs."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            hubs = client.hubs.list()
            rows = []
            for hub in hubs.items if hasattr(hubs, "items") else hubs:
                name = hub.spec.name if hasattr(hub, "spec") else getattr(hub, "name", "N/A")
                status = hub.status if hasattr(hub, "status") else "N/A"
                region = hub.spec.region if hasattr(hub, "spec") and hasattr(hub.spec, "region") else getattr(hub, "region", "N/A")
                gpu_count = "N/A"
                if hasattr(hub, "capacity") and hub.capacity:
                    gpu_count = str(getattr(hub.capacity, "gpu_total", getattr(hub.capacity, "total_gpus", "N/A")))
                rows.append([name, status, region, gpu_count])

            if rows:
                print(_format_table(
                    ["Hub", "Status", "Region", "GPUs"],
                    rows,
                    title="Sovereign Compute Hubs",
                ))
                total = getattr(hubs, "total", len(rows))
                print(f"\n  Total: {total} hubs\n")
            else:
                print("  No hubs found.")
    except Exception as e:
        print(f"  Error fetching hubs: {e}")
        sys.exit(1)


def cmd_workloads(args: argparse.Namespace) -> None:
    """List workloads."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            status_filter = getattr(args, "status", None)
            kwargs = {}
            if status_filter:
                kwargs["status"] = status_filter
            workloads = client.workloads.list(**kwargs)

            rows = []
            for wl in workloads.items if hasattr(workloads, "items") else workloads:
                name = wl.metadata.name if hasattr(wl, "metadata") else getattr(wl, "name", "N/A")
                wl_status = wl.status if hasattr(wl, "status") else "N/A"
                wl_type = wl.spec.type if hasattr(wl, "spec") and hasattr(wl.spec, "type") else getattr(wl, "type", "N/A")
                wl_id = wl.metadata.id if hasattr(wl, "metadata") else getattr(wl, "id", "N/A")
                rows.append([wl_id[:16], name, wl_type, wl_status])

            if rows:
                print(_format_table(
                    ["ID", "Name", "Type", "Status"],
                    rows,
                    title="Workloads",
                ))
                total = getattr(workloads, "total", len(rows))
                print(f"\n  Total: {total} workloads\n")
            else:
                print("  No workloads found.")
    except Exception as e:
        print(f"  Error fetching workloads: {e}")
        sys.exit(1)


def cmd_models(args: argparse.Namespace) -> None:
    """List available AI models."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            models = client.models.list()
            rows = []
            for m in models.items if hasattr(models, "items") else models:
                name = m.spec.name if hasattr(m, "spec") else getattr(m, "name", "N/A")
                task = m.spec.task if hasattr(m, "spec") and hasattr(m.spec, "task") else getattr(m, "task", "N/A")
                status = m.status if hasattr(m, "status") else "N/A"
                framework = ""
                if hasattr(m, "spec") and hasattr(m.spec, "framework"):
                    framework = m.spec.framework or ""
                rows.append([name, task, str(status), framework])

            if rows:
                print(_format_table(
                    ["Model", "Task", "Status", "Framework"],
                    rows,
                    title="Available AI Models",
                ))
                total = getattr(models, "total", len(rows))
                print(f"\n  Total: {total} models\n")
            else:
                print("  No models found.")
    except Exception as e:
        print(f"  Error fetching models: {e}")
        sys.exit(1)


def cmd_optimize(args: argparse.Namespace) -> None:
    """Run carbon-aware scheduling optimizer."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            result = client.carbon.optimize(
                workload_name=args.name,
                workload_type=getattr(args, "type", "training"),
                gpu_count=getattr(args, "gpus", 1),
                gpu_type=getattr(args, "gpu_type", None),
                carbon_aware=True,
                carbon_max_gco2=getattr(args, "max_carbon", None),
                region=getattr(args, "region", None),
                estimated_duration_hours=getattr(args, "duration", 1.0),
            )

            print(f"\n  Carbon-Aware Optimization Result")
            print(f"  {'=' * 35}")
            print(f"  Workload:    {result.workload_name}")
            print(f"  Action:      {result.action}")
            if hasattr(result, "recommended_hub") and result.recommended_hub:
                print(f"  Hub:         {result.recommended_hub}")
            if hasattr(result, "carbon_intensity_gco2_kwh") and result.carbon_intensity_gco2_kwh is not None:
                print(f"  Intensity:   {result.carbon_intensity_gco2_kwh} gCO2/kWh")
            if hasattr(result, "carbon_saved_kg") and result.carbon_saved_kg is not None:
                print(f"  CO2 Saved:   {result.carbon_saved_kg} kg")
            if hasattr(result, "defer_hours") and result.defer_hours is not None:
                print(f"  Defer:       {result.defer_hours} hours")
            if hasattr(result, "reason") and result.reason:
                print(f"  Reason:      {result.reason}")
            print()
    except Exception as e:
        print(f"  Error running optimizer: {e}")
        sys.exit(1)


def cmd_green_windows(args: argparse.Namespace) -> None:
    """Find green scheduling windows."""
    try:
        client = _get_client(args.api_key, args.base_url)
        with client:
            region = getattr(args, "region", "morocco")
            windows = client.energy.get_green_windows(region=region)

            rows = []
            for w in windows:
                start = getattr(w, "start", "N/A")
                end = getattr(w, "end", "N/A")
                renewable = getattr(w, "renewable_percentage", 0)
                co2 = getattr(w, "estimated_co2_grams_per_kwh", "N/A")
                rows.append([str(start), str(end), f"{renewable:.1f}%" if isinstance(renewable, (int, float)) else str(renewable), str(co2)])

            if rows:
                print(_format_table(
                    ["Start", "End", "Renewable", "gCO2/kWh"],
                    rows,
                    title=f"Green Scheduling Windows ({region})",
                ))
                print()
            else:
                print(f"  No green windows found for region '{region}'.")
    except Exception as e:
        print(f"  Error fetching green windows: {e}")
        sys.exit(1)


def cmd_config(args: argparse.Namespace) -> None:
    """Show or manage SDK configuration."""
    subcmd = getattr(args, "config_action", "show")

    if subcmd == "show":
        from .config import HarchOSConfig

        config_kwargs: Dict[str, Any] = {}
        api_key = os.environ.get("HARCHOS_API_KEY")
        base_url = os.environ.get("HARCHOS_BASE_URL")
        if api_key:
            config_kwargs["api_key"] = api_key
        if base_url:
            config_kwargs["base_url"] = base_url
        config = HarchOSConfig(**config_kwargs)

        print(f"\n  HarchOS SDK Configuration")
        print(f"  {'=' * 30}")
        print(f"  Base URL:     {config.base_url}")
        print(f"  Region:       {config.region}")
        print(f"  Sovereignty:  {config.sovereignty}")
        print(f"  Carbon-aware: {config.carbon_aware}")
        print(f"  Timeout:      {config.timeout}s")
        print(f"  Max retries:  {config.max_retries}")
        print(f"  API Key:      {'***' + config.api_key[-4:] if config.api_key else 'NOT SET'}")
        print(f"  SDK Version:  v{__version__}")
        print()

    elif subcmd == "set":
        if not args.key or not args.value:
            print("  Usage: harchos config set KEY VALUE")
            print("  Keys: api_key, base_url, region, sovereignty, timeout")
            sys.exit(1)
        key_map = {
            "api_key": "HARCHOS_API_KEY",
            "base_url": "HARCHOS_BASE_URL",
            "region": "HARCHOS_REGION",
            "sovereignty": "HARCHOS_SOVEREIGNTY",
            "timeout": "HARCHOS_TIMEOUT",
        }
        env_var = key_map.get(args.key)
        if not env_var:
            print(f"  Unknown config key: {args.key}")
            print(f"  Valid keys: {', '.join(key_map.keys())}")
            sys.exit(1)
        os.environ[env_var] = args.value
        print(f"  Set {args.key} = {args.value}")
        print(f"  (Environment variable: {env_var})")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="harchos",
        description="HarchOS CLI — The Operating System for Sovereign AI Infrastructure",
        epilog=(
            "Set HARCHOS_API_KEY environment variable or use --api-key flag.\n"
            "Docs: https://docs.harchos.io  |  PyPI: https://pypi.org/project/harchos/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"harchos v{__version__}",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="HarchOS API key (or set HARCHOS_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override API base URL (or set HARCHOS_BASE_URL env var)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    sub_status = subparsers.add_parser("status", help="Check API health and connectivity")
    sub_status.set_defaults(func=cmd_status)

    # carbon
    sub_carbon = subparsers.add_parser("carbon", help="Get carbon intensity data")
    sub_carbon.add_argument("zone", nargs="?", default=None, help="Zone code (e.g. MA, FR, DE). Omit for all zones.")
    sub_carbon.set_defaults(func=cmd_carbon)

    # hubs
    sub_hubs = subparsers.add_parser("hubs", help="List sovereign compute hubs")
    sub_hubs.set_defaults(func=cmd_hubs)

    # workloads
    sub_workloads = subparsers.add_parser("workloads", help="List workloads")
    sub_workloads.add_argument("--status", "-s", default=None, help="Filter by status (running, pending, completed)")
    sub_workloads.set_defaults(func=cmd_workloads)

    # models
    sub_models = subparsers.add_parser("models", help="List available AI models")
    sub_models.set_defaults(func=cmd_models)

    # optimize
    sub_optimize = subparsers.add_parser("optimize", help="Run carbon-aware scheduling optimizer")
    sub_optimize.add_argument("--name", "-n", required=True, help="Workload name")
    sub_optimize.add_argument("--type", "-t", default="training", help="Workload type (default: training)")
    sub_optimize.add_argument("--gpus", "-g", type=int, default=1, help="GPU count (default: 1)")
    sub_optimize.add_argument("--gpu-type", default=None, help="GPU type (e.g. A100, H100)")
    sub_optimize.add_argument("--max-carbon", type=float, default=None, help="Max carbon intensity in gCO2/kWh")
    sub_optimize.add_argument("--region", "-r", default=None, help="Preferred region")
    sub_optimize.add_argument("--duration", "-d", type=float, default=1.0, help="Estimated duration in hours")
    sub_optimize.set_defaults(func=cmd_optimize)

    # green-windows
    sub_green = subparsers.add_parser("green-windows", help="Find green scheduling windows")
    sub_green.add_argument("--region", "-r", default="morocco", help="Region (default: morocco)")
    sub_green.set_defaults(func=cmd_green_windows)

    # config
    sub_config = subparsers.add_parser("config", help="Show or manage configuration")
    sub_config_sub = sub_config.add_subparsers(dest="config_action")
    sub_config_show = sub_config_sub.add_parser("show", help="Show current configuration")
    sub_config_show.set_defaults(func=cmd_config)
    sub_config_set = sub_config_sub.add_parser("set", help="Set a configuration value")
    sub_config_set.add_argument("key", nargs="?", default=None, help="Config key")
    sub_config_set.add_argument("value", nargs="?", default=None, help="Config value")
    sub_config_set.set_defaults(func=cmd_config)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for the harchos CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
