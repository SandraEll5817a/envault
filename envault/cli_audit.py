"""CLI commands for inspecting the envault audit log."""

import click
from rich.console import Console
from rich.table import Table

from envault.audit import read_events

console = Console()


@click.command("log")
@click.option(
    "--limit",
    "-n",
    default=20,
    show_default=True,
    help="Number of recent events to display.",
)
@click.option(
    "--action",
    type=click.Choice(["push", "pull", "check"], case_sensitive=False),
    default=None,
    help="Filter events by action type.",
)
@click.option(
    "--user",
    default=None,
    help="Filter events by username.",
)
def audit_log(limit: int, action, user):
    """Display the recent audit log of push/pull operations."""
    events = read_events(limit=limit * 3)  # fetch extra to allow filtering

    if action:
        events = [e for e in events if e.get("action") == action.lower()]
    if user:
        events = [e for e in events if e.get("user") == user]

    events = events[:limit]

    if not events:
        console.print("[yellow]No audit events found.[/yellow]")
        return

    table = Table(title="Envault Audit Log", show_lines=True)
    table.add_column("Timestamp", style="dim", no_wrap=True)
    table.add_column("Action", style="bold")
    table.add_column("Key")
    table.add_column("Backend")
    table.add_column("User")
    table.add_column("Status")
    table.add_column("Detail")

    for event in events:
        status = "[green]OK[/green]" if event.get("success") else "[red]FAIL[/red]"
        table.add_row(
            event.get("timestamp", "")[:19].replace("T", " "),
            event.get("action", ""),
            event.get("env_key", ""),
            event.get("backend", ""),
            event.get("user", ""),
            status,
            event.get("detail") or "",
        )

    console.print(table)
