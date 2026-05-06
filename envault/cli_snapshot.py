"""CLI commands for snapshot inspection."""

from __future__ import annotations

import time

import click

from envault.snapshot import load_snapshot, delete_snapshot, _SNAPSHOT_DIR


@click.group("snapshot")
def snapshot_group():
    """Inspect and manage local .env snapshots."""


@snapshot_group.command("show")
@click.argument("env_key")
def snapshot_show(env_key: str):
    """Show snapshot metadata for ENV_KEY."""
    snap = load_snapshot(env_key)
    if snap is None:
        click.echo(f"No snapshot found for '{env_key}'.")
        raise SystemExit(1)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(snap.timestamp))
    click.echo(f"env_key  : {snap.env_key}")
    click.echo(f"checksum : {snap.checksum}")
    click.echo(f"saved at : {ts}")
    click.echo(f"size     : {snap.size} bytes")
    if snap.extra:
        for k, v in snap.extra.items():
            click.echo(f"{k:<9}: {v}")


@snapshot_group.command("list")
def snapshot_list():
    """List all stored snapshots."""
    if not _SNAPSHOT_DIR.exists():
        click.echo("No snapshots stored.")
        return
    files = sorted(_SNAPSHOT_DIR.glob("*.json"))
    if not files:
        click.echo("No snapshots stored.")
        return
    for f in files:
        key = f.stem.replace("__", "/")
        click.echo(key)


@snapshot_group.command("delete")
@click.argument("env_key")
def snapshot_delete(env_key: str):
    """Delete the snapshot for ENV_KEY."""
    removed = delete_snapshot(env_key)
    if removed:
        click.echo(f"Snapshot for '{env_key}' deleted.")
    else:
        click.echo(f"No snapshot found for '{env_key}'.")
        raise SystemExit(1)
