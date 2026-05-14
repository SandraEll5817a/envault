"""CLI commands for displaying diff reports between local and remote .env files."""

from __future__ import annotations

import click

from envault.cli import get_backend
from envault.crypto import decrypt
from envault.env_diff_report import build_report


@click.group(name="diff")
def diff_group() -> None:
    """Show differences between local and remote .env files."""


@diff_group.command(name="show")
@click.argument("env_name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", required=True, help="Decryption passphrase.")
@click.option("--file", "env_file", default=".env", show_default=True, help="Local .env file path.")
@click.option("--show-values", is_flag=True, default=False, help="Reveal key values in output.")
@click.option("--bucket", envvar="ENVAULT_BUCKET", required=True)
@click.option("--backend", envvar="ENVAULT_BACKEND", default="s3", show_default=True, type=click.Choice(["s3", "gcs"]))
def diff_show(
    env_name: str,
    passphrase: str,
    env_file: str,
    show_values: bool,
    bucket: str,
    backend: str,
) -> None:
    """Compare local ENV_NAME .env file against the remote version."""
    storage = get_backend(backend, bucket)

    if not storage.exists(env_name):
        click.echo(f"Remote key '{env_name}' not found.", err=True)
        raise SystemExit(1)

    try:
        local_content = open(env_file).read()
    except FileNotFoundError:
        click.echo(f"Local file '{env_file}' not found.", err=True)
        raise SystemExit(1)

    ciphertext = storage.download(env_name)
    try:
        remote_content = decrypt(ciphertext, passphrase).decode()
    except Exception:
        click.echo("Failed to decrypt remote file. Check your passphrase.", err=True)
        raise SystemExit(1)

    report = build_report(
        old_content=remote_content,
        new_content=local_content,
        env_name=env_name,
        old_label="remote",
        new_label="local",
    )
    click.echo(report.render(show_values=show_values))
    if report.has_changes:
        raise SystemExit(1)
