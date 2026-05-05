"""HarchOS CLI — Command-line interface for sovereign AI infrastructure.

Usage::

    harchos inference chat --model harchos-llama-3.3-70b --message "Hello"
    harchos carbon intensity --zone MA
    harchos workloads list
    harchos hubs list
    harchos whoami
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

try:
    import typer
except ImportError:
    # Fallback: if typer is not installed, provide a stub
    typer = None  # type: ignore


def _get_client():
    """Create a HarchOS client from args or environment."""
    from .._client import HarchOS

    api_key = os.environ.get("HARCHOS_API_KEY")
    base_url = os.environ.get("HARCHOS_BASE_URL")

    if not api_key:
        typer.echo(
            "Error: No API key provided. Set HARCHOS_API_KEY or use --api-key\n"
            "  export HARCHOS_API_KEY=hsk_your_key_here",
            err=True,
        )
        raise typer.Exit(code=1)

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return HarchOS(**kwargs)


def _format_table(headers: list[str], rows: list[list[str]], title: Optional[str] = None) -> str:
    """Format data as a simple text table."""
    lines: list[str] = []
    if title:
        lines.append(f"\n  {title}")
        lines.append("  " + "=" * len(title))

    all_rows = [headers] + rows
    widths = [max(len(str(row[i])) for row in all_rows) for i in range(len(headers))]

    header_line = "  ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    separator = "  ".join("-" * w for w in widths)
    lines.append("  " + header_line)
    lines.append("  " + separator)

    for row in rows:
        line = "  ".join(str(v).ljust(w) for v, w in zip(row, widths))
        lines.append("  " + line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Build the Typer app (if typer is available)
# ---------------------------------------------------------------------------

if typer is not None:
    app = typer.Typer(
        name="harchos",
        help="HarchOS CLI — The Operating System for Sovereign AI Infrastructure",
        no_args_is_help=True,
    )

    # Common options
    _API_KEY_OPTION = typer.Option(None, "--api-key", envvar="HARCHOS_API_KEY", help="API key")
    _BASE_URL_OPTION = typer.Option(None, "--base-url", envvar="HARCHOS_BASE_URL", help="API base URL")

    # --- inference chat ---
    @app.command("inference")
    def inference_cmd(
        ctx: typer.Context,
        model: str = typer.Option("harchos-llama-3.3-70b", "--model", "-m", help="Model ID"),
        message: str = typer.Option("Hello", "--message", "-M", help="Chat message"),
        stream: bool = typer.Option(False, "--stream", "-s", help="Stream response"),
        max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Max tokens"),
        api_key: Optional[str] = _API_KEY_OPTION,
    ) -> None:
        """Run an inference chat completion."""
        if api_key:
            os.environ["HARCHOS_API_KEY"] = api_key
        try:
            client = _get_client()
            with client:
                if stream:
                    for chunk in client.inference.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": message}],
                        stream=True,
                        **({"max_tokens": max_tokens} if max_tokens else {}),
                    ):
                        if chunk.choices and chunk.choices[0].delta.content:
                            typer.echo(chunk.choices[0].delta.content, nl=False)
                    typer.echo()  # Final newline
                else:
                    response = client.inference.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": message}],
                        **({"max_tokens": max_tokens} if max_tokens else {}),
                    )
                    if response.content:
                        typer.echo(response.content)
                    if response.carbon_footprint:
                        typer.echo(
                            f"\n  🌿 Carbon: {response.carbon_footprint.gco2:.2f}g CO2 "
                            f"({response.carbon_footprint.renewable_percentage:.0f}% renewable, "
                            f"hub: {response.carbon_footprint.hub_region})",
                            err=True,
                        )
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

    # --- carbon intensity ---
    @app.command("carbon")
    def carbon_cmd(
        zone: str = typer.Argument("MA", help="Zone code (e.g. MA, FR, DE)"),
        api_key: Optional[str] = _API_KEY_OPTION,
    ) -> None:
        """Get carbon intensity for a zone."""
        if api_key:
            os.environ["HARCHOS_API_KEY"] = api_key
        try:
            client = _get_client()
            with client:
                intensity = client.carbon.intensity(zone=zone)
                typer.echo(f"\n  Carbon Intensity: {intensity.zone}")
                typer.echo(f"  {'=' * 35}")
                typer.echo(f"  Zone:             {intensity.zone}")
                typer.echo(f"  Intensity:        {intensity.carbon_intensity_gco2_kwh} gCO2/kWh")
                typer.echo(f"  Renewable:        {intensity.renewable_percentage:.1f}%")
                if intensity.fossil_percentage:
                    typer.echo(f"  Fossil:           {intensity.fossil_percentage:.1f}%")
                tag = "GREEN" if intensity.is_green else "FOSSIL"
                typer.echo(f"  Status:           {tag}")
                typer.echo()
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

    # --- workloads list ---
    @app.command("workloads")
    def workloads_cmd(
        status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
        api_key: Optional[str] = _API_KEY_OPTION,
    ) -> None:
        """List workloads."""
        if api_key:
            os.environ["HARCHOS_API_KEY"] = api_key
        try:
            client = _get_client()
            with client:
                kwargs = {}
                if status:
                    kwargs["status"] = status
                workloads = client.workloads.list(**kwargs)
                rows = []
                for wl in workloads.items:
                    rows.append([
                        wl.id[:16] if len(wl.id) > 16 else wl.id,
                        wl.name,
                        wl.type,
                        wl.status,
                    ])
                if rows:
                    typer.echo(_format_table(
                        ["ID", "Name", "Type", "Status"],
                        rows,
                        title="Workloads",
                    ))
                    typer.echo(f"\n  Total: {workloads.total} workloads\n")
                else:
                    typer.echo("  No workloads found.")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

    # --- hubs list ---
    @app.command("hubs")
    def hubs_cmd(
        region: Optional[str] = typer.Option(None, "--region", "-r", help="Filter by region"),
        api_key: Optional[str] = _API_KEY_OPTION,
    ) -> None:
        """List sovereign compute hubs."""
        if api_key:
            os.environ["HARCHOS_API_KEY"] = api_key
        try:
            client = _get_client()
            with client:
                kwargs = {}
                if region:
                    kwargs["region"] = region
                hubs = client.hubs.list(**kwargs)
                rows = []
                for hub in hubs.items:
                    ci = f"{hub.carbon_intensity_gco2_kwh:.0f}" if hub.carbon_intensity_gco2_kwh else "N/A"
                    renewable = f"{hub.renewable_percentage:.0f}%" if hub.renewable_percentage else "N/A"
                    gpus = str(hub.capacity.total_gpus) if hub.capacity else "N/A"
                    rows.append([hub.name, hub.region, hub.status, gpus, ci, renewable])
                if rows:
                    typer.echo(_format_table(
                        ["Hub", "Region", "Status", "GPUs", "gCO2/kWh", "Renewable"],
                        rows,
                        title="Sovereign Compute Hubs",
                    ))
                    typer.echo(f"\n  Total: {hubs.total} hubs\n")
                else:
                    typer.echo("  No hubs found.")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

    # --- whoami ---
    @app.command("whoami")
    def whoami_cmd(
        api_key: Optional[str] = _API_KEY_OPTION,
    ) -> None:
        """Show information about the authenticated user."""
        if api_key:
            os.environ["HARCHOS_API_KEY"] = api_key
        try:
            client = _get_client()
            with client:
                user = client.auth.me()
                typer.echo(f"\n  User Info")
                typer.echo(f"  {'=' * 30}")
                typer.echo(f"  ID:     {user.id}")
                typer.echo(f"  Email:  {user.email}")
                typer.echo(f"  Name:   {user.name or 'N/A'}")
                typer.echo(f"  Plan:   {user.plan}")
                if user.created_at:
                    typer.echo(f"  Since:  {user.created_at}")
                typer.echo()
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

    # --- version ---
    @app.command("version")
    def version_cmd() -> None:
        """Show the SDK version."""
        from .._client import __version__
        typer.echo(f"harchos v{__version__}")

    def main() -> None:
        """Entry point for the harchos CLI."""
        app()

else:
    # Fallback when typer is not installed — use argparse
    import argparse

    def _cmd_inference(args: argparse.Namespace) -> None:
        """Run inference chat."""
        from .._client import HarchOS

        kwargs = {}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        elif not os.environ.get("HARCHOS_API_KEY"):
            print("Error: Set HARCHOS_API_KEY or use --api-key", file=sys.stderr)
            sys.exit(1)
        client = HarchOS(**kwargs)
        with client:
            response = client.inference.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": args.message}],
            )
            if response.content:
                print(response.content)

    def _cmd_carbon(args: argparse.Namespace) -> None:
        """Get carbon intensity."""
        from .._client import HarchOS

        kwargs = {}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        client = HarchOS(**kwargs)
        with client:
            intensity = client.carbon.intensity(zone=args.zone)
            print(f"Zone: {intensity.zone}, Intensity: {intensity.carbon_intensity_gco2_kwh} gCO2/kWh")

    def _cmd_workloads(args: argparse.Namespace) -> None:
        """List workloads."""
        from .._client import HarchOS

        kwargs = {}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        client = HarchOS(**kwargs)
        with client:
            workloads = client.workloads.list()
            for wl in workloads.items:
                print(f"  {wl.id[:16]}  {wl.name}  {wl.type}  {wl.status}")
            print(f"\n  Total: {workloads.total}")

    def _cmd_hubs(args: argparse.Namespace) -> None:
        """List hubs."""
        from .._client import HarchOS

        kwargs = {}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        client = HarchOS(**kwargs)
        with client:
            hubs = client.hubs.list()
            for hub in hubs.items:
                print(f"  {hub.name}  {hub.region}  {hub.status}")

    def _cmd_whoami(args: argparse.Namespace) -> None:
        """Show user info."""
        from .._client import HarchOS

        kwargs = {}
        if args.api_key:
            kwargs["api_key"] = args.api_key
        client = HarchOS(**kwargs)
        with client:
            user = client.auth.me()
            print(f"  ID: {user.id}, Email: {user.email}, Plan: {user.plan}")

    def main() -> None:
        """Entry point for the harchos CLI (argparse fallback)."""
        from .._client import __version__

        parser = argparse.ArgumentParser(
            prog="harchos",
            description="HarchOS CLI — The Operating System for Sovereign AI Infrastructure",
        )
        parser.add_argument("--version", "-V", action="version", version=f"harchos v{__version__}")
        parser.add_argument("--api-key", default=None, help="API key")

        subparsers = parser.add_subparsers(dest="command")

        # inference
        sub_inf = subparsers.add_parser("inference", help="Run inference")
        sub_inf.add_argument("--model", "-m", default="harchos-llama-3.3-70b")
        sub_inf.add_argument("--message", "-M", default="Hello")
        sub_inf.set_defaults(func=_cmd_inference)

        # carbon
        sub_carbon = subparsers.add_parser("carbon", help="Carbon intensity")
        sub_carbon.add_argument("zone", nargs="?", default="MA")
        sub_carbon.set_defaults(func=_cmd_carbon)

        # workloads
        sub_wl = subparsers.add_parser("workloads", help="List workloads")
        sub_wl.set_defaults(func=_cmd_workloads)

        # hubs
        sub_hubs = subparsers.add_parser("hubs", help="List hubs")
        sub_hubs.set_defaults(func=_cmd_hubs)

        # whoami
        sub_who = subparsers.add_parser("whoami", help="Show user info")
        sub_who.set_defaults(func=_cmd_whoami)

        args = parser.parse_args()
        if not args.command:
            parser.print_help()
            sys.exit(0)
        args.func(args)
