"""CLI commands for inspecting and managing envault environment locks."""

import click
from envault.lock import read_lock, release_lock, is_locked, _get_lock_dir


@click.group(name="lock")
def lock_group():
    """Manage environment locks."""


@lock_group.command("status")
@click.argument("env_name")
def lock_status(env_name: str):
    """Show the lock status for an environment."""
    info = read_lock(env_name)
    if info is None:
        click.echo(f"No lock found for '{env_name}'.")
        return

    alive = is_locked(env_name)
    status = "ACTIVE" if alive else "STALE"
    click.echo(f"Lock status : {status}")
    click.echo(f"PID         : {info['pid']}")
    click.echo(f"Acquired at : {info['acquired_at']:.2f}")


@lock_group.command("release")
@click.argument("env_name")
@click.option("--force", is_flag=True, help="Release even if the lock is held by another process.")
def lock_release(env_name: str, force: bool):
    """Release a lock for an environment."""
    if not force and is_locked(env_name):
        click.echo(
            f"Lock for '{env_name}' is held by an active process. Use --force to override.",
            err=True,
        )
        raise SystemExit(1)

    released = release_lock(env_name)
    if released:
        click.echo(f"Lock for '{env_name}' released.")
    else:
        click.echo(f"No lock found for '{env_name}'.")


@lock_group.command("list")
def lock_list():
    """List all current environment locks."""
    lock_dir = _get_lock_dir()
    lock_files = sorted(lock_dir.glob("*.lock"))

    if not lock_files:
        click.echo("No locks found.")
        return

    for lf in lock_files:
        env_name = lf.stem
        alive = is_locked(env_name)
        status = "ACTIVE" if alive else "STALE"
        click.echo(f"{env_name:<30} {status}")
