import json
import os
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from app import config
from app.client import BeszelClient

console = Console()


def get_client() -> BeszelClient:
    base_url = os.environ.get("BESZEL_URL") or config.get_url()
    if not base_url:
        console.print("[red]Error: No Beszel URL configured. Run 'beszel login' first.[/red]")
        raise SystemExit(1)
    token = os.environ.get("BESZEL_TOKEN") or config.get_token()
    return BeszelClient(base_url, token)


@click.group()
def main() -> None:
    """Beszel CLI - Manage your Beszel server monitoring from the command line."""


# === Authentication ===


@main.command()
@click.option("--url", "-s", help="Beszel hub URL")
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password", hide_input=True)
def login(url: str | None, email: str | None, password: str | None) -> None:
    """Login and save credentials."""
    if not url:
        current_url = config.get_url()
        if current_url:
            url = click.prompt("Beszel URL", default=current_url)
        else:
            url = click.prompt("Beszel URL (e.g. https://beszel.example.com)")
    config.set_url(url)

    if not email:
        email = click.prompt("Email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    client = BeszelClient(url)
    token = client.login(email, password)
    client.close()

    config.set_token(token)
    console.print("[green]Login successful![/green]")
    console.print(f"Config saved to {config.CONFIG_FILE}")


@main.command()
def logout() -> None:
    """Clear saved credentials."""
    config.clear_config()
    console.print("[green]Logged out - credentials cleared[/green]")


@main.command("config-show")
def config_show() -> None:
    """Show current configuration."""
    console.print(f"[bold]Config file:[/bold] {config.CONFIG_FILE}")
    url = config.get_url()
    console.print(f"[bold]URL:[/bold] {url or '[dim]not set[/dim]'}")
    token = config.get_token()
    if token:
        console.print(f"[bold]Token:[/bold] {token[:20]}...")
    else:
        console.print("[bold]Token:[/bold] [dim]not set[/dim]")


@main.command("config-set-url")
@click.argument("url")
def config_set_url(url: str) -> None:
    """Set the Beszel hub URL."""
    config.set_url(url)
    console.print(f"[green]URL set to {url}[/green]")


@main.command("whoami")
def whoami() -> None:
    """Show current user info."""
    with get_client() as client:
        user = client.get_current_user()
        console.print(f"[bold]Email:[/bold] {user.get('email')}")
        console.print(f"[bold]Name:[/bold] {user.get('name')}")
        console.print(f"[bold]ID:[/bold] {user.get('id')}")
        console.print(f"[bold]Role:[/bold] {user.get('role', 'user')}")


# === Systems ===


@main.command()
@click.option("--filter", "-f", "filter_expr", default="", help="PocketBase filter expression")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def systems(filter_expr: str, json_output: bool) -> None:
    """List all monitored systems."""
    with get_client() as client:
        sys_list = client.get_systems(filter_expr)
        if json_output:
            console.print(json.dumps(sys_list, indent=2, default=str))
            return
        table = Table(title="Systems")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Host", style="dim")
        table.add_column("Port", style="dim")
        table.add_column("Status", style="bold")
        for sys in sys_list:
            status = sys.get("status", "unknown")
            status_style = "green" if status == "up" else "red" if status == "down" else "yellow"
            table.add_row(
                str(sys.get("id")),
                str(sys.get("name")),
                str(sys.get("host", "")),
                str(sys.get("port", "")),
                f"[{status_style}]{status}[/{status_style}]",
            )
        console.print(table)


@main.command("system")
@click.argument("system_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def system_show(system_id: str, json_output: bool) -> None:
    """Show system details."""
    with get_client() as client:
        sys = client.get_system(system_id)
        if json_output:
            console.print(json.dumps(sys, indent=2, default=str))
            return
        status = sys.get("status", "unknown")
        status_style = "green" if status == "up" else "red" if status == "down" else "yellow"
        console.print(f"[bold cyan]System: {sys.get('name')}[/bold cyan]")
        console.print(f"[bold]ID:[/bold] {sys.get('id')}")
        console.print(f"[bold]Host:[/bold] {sys.get('host')}")
        console.print(f"[bold]Port:[/bold] {sys.get('port')}")
        console.print(f"[bold]Status:[/bold] [{status_style}]{status}[/{status_style}]")

        info = sys.get("info", {}) or {}
        if info:
            console.print(f"\n[bold]System Info:[/bold]")
            if info.get("h"):
                console.print(f"  Hostname: {info['h']}")
            if info.get("m"):
                console.print(f"  CPU Model: {info['m']}")
            if info.get("c"):
                console.print(f"  Cores: {info['c']} ({info.get('t', '')} threads)")
            if info.get("k"):
                console.print(f"  Kernel: {info['k']}")
            if info.get("v"):
                console.print(f"  Agent Version: {info['v']}")
            if info.get("cpu") is not None:
                console.print(f"  CPU: {info['cpu']:.1f}%")
            if info.get("mp") is not None:
                console.print(f"  Memory: {info['mp']:.1f}%")
            if info.get("dp") is not None:
                console.print(f"  Disk: {info['dp']:.1f}%")


@main.command("system-update")
@click.argument("system_id")
@click.option("--name", "-n", help="New name")
@click.option("--host", help="New host")
@click.option("--port", type=int, help="New port")
def system_update(system_id: str, name: str | None, host: str | None, port: int | None) -> None:
    """Update a system."""
    with get_client() as client:
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if host:
            data["host"] = host
        if port:
            data["port"] = port
        if not data:
            console.print("[yellow]No updates provided[/yellow]")
            return
        sys = client.update_system(system_id, data)
        console.print(f"[green]Updated system:[/green] {sys.get('name')}")


@main.command("system-delete")
@click.argument("system_id")
@click.confirmation_option(prompt="Are you sure you want to delete this system?")
def system_delete(system_id: str) -> None:
    """Delete a system."""
    with get_client() as client:
        client.delete_system(system_id)
        console.print("[green]System deleted[/green]")


# === System Stats ===


@main.command("stats")
@click.argument("system_id")
@click.option("--type", "-t", "record_type", default="1m", type=click.Choice(["1m", "10m", "20m", "120m", "480m"]))
@click.option("--limit", "-l", default=10, help="Number of records to show")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def stats(system_id: str, record_type: str, limit: int, json_output: bool) -> None:
    """Show system stats history."""
    with get_client() as client:
        records = client.get_system_stats(system_id, record_type, limit)
        if json_output:
            console.print(json.dumps(records, indent=2, default=str))
            return
        if not records:
            console.print("[dim]No stats found[/dim]")
            return
        table = Table(title=f"System Stats ({record_type})")
        table.add_column("Time", style="dim")
        table.add_column("CPU %", style="cyan")
        table.add_column("Mem %", style="green")
        table.add_column("Disk %", style="yellow")
        table.add_column("Mem Used", style="dim")
        table.add_column("BW Sent/s", style="dim")
        table.add_column("BW Recv/s", style="dim")
        for rec in records:
            s = rec.get("stats", {}) or {}
            bw = s.get("b", [0, 0])
            table.add_row(
                str(rec.get("created", "")),
                f"{s.get('cpu', 0):.1f}",
                f"{s.get('mp', 0):.1f}",
                f"{s.get('dp', 0):.1f}",
                f"{s.get('mu', 0):.2f} GB",
                _format_bytes(bw[0] if len(bw) > 0 else 0) + "/s",
                _format_bytes(bw[1] if len(bw) > 1 else 0) + "/s",
            )
        console.print(table)


# === Containers ===


@main.command()
@click.argument("system_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def containers(system_id: str, json_output: bool) -> None:
    """List containers for a system."""
    with get_client() as client:
        container_list = client.get_containers(system_id)
        if json_output:
            console.print(json.dumps(container_list, indent=2, default=str))
            return
        if not container_list:
            console.print("[dim]No containers found[/dim]")
            return
        table = Table(title="Containers")
        table.add_column("Name", style="green")
        table.add_column("CPU %", style="cyan")
        table.add_column("Memory", style="yellow")
        table.add_column("Status", style="dim")
        table.add_column("Image", style="dim", max_width=40)
        for c in container_list:
            mem_mb = c.get("memory", 0)
            table.add_row(
                str(c.get("name", "")),
                f"{c.get('cpu', 0):.2f}",
                f"{mem_mb:.0f} MB" if mem_mb else "0 MB",
                str(c.get("status", "")),
                str(c.get("image", "")),
            )
        console.print(table)


# === Alerts ===


@main.command()
@click.option("--system", "-s", "system_id", default="", help="Filter by system ID")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def alerts(system_id: str, json_output: bool) -> None:
    """List alerts."""
    with get_client() as client:
        alert_list = client.get_alerts(system_id)
        if json_output:
            console.print(json.dumps(alert_list, indent=2, default=str))
            return
        if not alert_list:
            console.print("[dim]No alerts found[/dim]")
            return
        table = Table(title="Alerts")
        table.add_column("ID", style="cyan")
        table.add_column("System", style="green")
        table.add_column("Name", style="bold")
        table.add_column("Value", style="yellow")
        table.add_column("Triggered", style="dim")
        for alert in alert_list:
            expanded = alert.get("expand", {}) or {}
            system_name = ""
            if expanded.get("system"):
                system_name = expanded["system"].get("name", "")
            table.add_row(
                str(alert.get("id", "")),
                system_name or str(alert.get("system", "")),
                str(alert.get("name", "")),
                str(alert.get("value", "")),
                str(alert.get("triggered", "")),
            )
        console.print(table)


@main.command("alert-delete")
@click.argument("alert_id")
@click.confirmation_option(prompt="Are you sure you want to delete this alert?")
def alert_delete(alert_id: str) -> None:
    """Delete an alert."""
    with get_client() as client:
        client.delete_alert(alert_id)
        console.print("[green]Alert deleted[/green]")


# === Alert History ===


@main.command("alert-history")
@click.option("--limit", "-l", default=50, help="Number of records to show")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def alert_history(limit: int, json_output: bool) -> None:
    """Show alert history."""
    with get_client() as client:
        history = client.get_alert_history(limit)
        if json_output:
            console.print(json.dumps(history, indent=2, default=str))
            return
        if not history:
            console.print("[dim]No alert history found[/dim]")
            return
        table = Table(title="Alert History")
        table.add_column("ID", style="cyan")
        table.add_column("Created", style="dim")
        table.add_column("User", style="green")
        for entry in history:
            table.add_row(
                str(entry.get("id", "")),
                str(entry.get("created", "")),
                str(entry.get("user", "")),
            )
        console.print(table)


# === Generic Records ===


@main.command("records")
@click.argument("collection")
@click.option("--filter", "-f", "filter_expr", default="", help="PocketBase filter expression")
@click.option("--sort", "-s", "sort_expr", default="", help="Sort expression (e.g. -created)")
@click.option("--limit", "-l", default=30, help="Number of records")
@click.option("--expand", "-e", default="", help="Relations to expand")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def records(collection: str, filter_expr: str, sort_expr: str, limit: int, expand: str, json_output: bool) -> None:
    """List records from any PocketBase collection."""
    with get_client() as client:
        result = client.list_records(collection, per_page=limit, sort=sort_expr, filter_expr=filter_expr, expand=expand)
        items = result.get("items", [])
        if json_output:
            console.print(json.dumps(items, indent=2, default=str))
            return
        if not items:
            console.print("[dim]No records found[/dim]")
            return
        # Auto-detect columns from first record
        first = items[0]
        columns = [k for k in first if not isinstance(first[k], (dict, list))][:8]
        table = Table(title=f"{collection} ({result.get('totalItems', '?')} total)")
        for col in columns:
            table.add_column(col, style="cyan" if col == "id" else "")
        for item in items:
            table.add_row(*[str(item.get(col, "")) for col in columns])
        console.print(table)


@main.command("record")
@click.argument("collection")
@click.argument("record_id")
@click.option("--expand", "-e", default="", help="Relations to expand")
def record_show(collection: str, record_id: str, expand: str) -> None:
    """Show a single record from any collection."""
    with get_client() as client:
        rec = client.get_record(collection, record_id, expand=expand)
        console.print(json.dumps(rec, indent=2, default=str))


# === Helpers ===


def _format_bytes(value: float | int) -> str:
    """Format bytes into human-readable form."""
    if not value:
        return "0 B"
    value = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


if __name__ == "__main__":
    main()
