"""CLI commands for key rotation."""

from __future__ import annotations

import click

from envault.cli import get_backend
from envault.rotate import rotate_key, rotate_all


@click.group("rotate")
def rotate_group() -> None:
    """Rotate encryption passphrases for stored .env files."""


@rotate_group.command("one")
@click.argument("key")
@click.option("--old-pass", envvar="ENVAULT_OLD_PASS", prompt=True, hide_input=True)
@click.option("--new-pass", envvar="ENVAULT_NEW_PASS", prompt=True, hide_input=True)
@click.option("--backend", "backend_type", default="s3", show_default=True)
@click.option("--bucket", envvar="ENVAULT_BUCKET", required=True)
def rotate_one(
    key: str,
    old_pass: str,
    new_pass: str,
    backend_type: str,
    bucket: str,
) -> None:
    """Re-encrypt a single stored .env file with a new passphrase."""
    backend = get_backend(backend_type, bucket)
    result = rotate_key(backend, key, old_pass, new_pass)
    if result.success:
        click.echo(f"Rotated: {key}")
    else:
        click.echo(f"Failed to rotate {key}: {result.error}", err=True)
        raise SystemExit(1)


@rotate_group.command("all")
@click.argument("keys", nargs=-1, required=True)
@click.option("--old-pass", envvar="ENVAULT_OLD_PASS", prompt=True, hide_input=True)
@click.option("--new-pass", envvar="ENVAULT_NEW_PASS", prompt=True, hide_input=True)
@click.option("--backend", "backend_type", default="s3", show_default=True)
@click.option("--bucket", envvar="ENVAULT_BUCKET", required=True)
def rotate_all_cmd(
    keys: tuple[str, ...],
    old_pass: str,
    new_pass: str,
    backend_type: str,
    bucket: str,
) -> None:
    """Re-encrypt multiple stored .env files with a new passphrase."""
    backend = get_backend(backend_type, bucket)
    results = rotate_all(backend, list(keys), old_pass, new_pass)
    failed = [r for r in results if not r.success]
    for r in results:
        status = "OK" if r.success else f"FAIL ({r.error})"
        click.echo(f"  {r.key}: {status}")
    if failed:
        raise SystemExit(1)
