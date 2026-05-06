"""Main CLI entry point for envault."""

import os
import click
from envault.storage import S3Backend, GCSBackend
from envault.crypto import encrypt, decrypt
from envault.audit import record_event
from envault.cli_audit import audit_log
from envault.cli_keys import keys_group
from envault.cli_rotate import rotate_group
from envault.cli_share import share_group
from envault.cli_snapshot import snapshot_group
from envault.cli_lock import lock_group


def get_backend():
    backend = os.environ.get("ENVAULT_BACKEND", "s3").lower()
    bucket = os.environ.get("ENVAULT_BUCKET", "")
    if backend == "s3":
        return S3Backend(bucket)
    elif backend == "gcs":
        return GCSBackend(bucket)
    else:
        raise click.ClickException(f"Unknown backend: {backend}")


@click.group()
def cli():
    """envault — securely sync .env files via encrypted cloud storage."""


@cli.command()
@click.argument("env_name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", required=True, hide_input=True)
@click.option("--file", "env_file", default=".env", show_default=True)
def push(env_name: str, passphrase: str, env_file: str):
    """Encrypt and upload a .env file."""
    try:
        plaintext = open(env_file, "rb").read()
    except FileNotFoundError:
        record_event("push", env_name, success=False)
        raise click.ClickException(f"File not found: {env_file}")

    ciphertext = encrypt(plaintext, passphrase)
    backend = get_backend()
    backend.upload(env_name, ciphertext)
    record_event("push", env_name, success=True)
    click.echo(f"Pushed '{env_file}' to '{env_name}'.")


@cli.command()
@click.argument("env_name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", required=True, hide_input=True)
@click.option("--file", "env_file", default=".env", show_default=True)
def pull(env_name: str, passphrase: str, env_file: str):
    """Download and decrypt a .env file."""
    backend = get_backend()
    if not backend.exists(env_name):
        record_event("pull", env_name, success=False)
        raise click.ClickException(f"Remote env '{env_name}' not found.")

    ciphertext = backend.download(env_name)
    try:
        plaintext = decrypt(ciphertext, passphrase)
    except Exception:
        record_event("pull", env_name, success=False)
        raise click.ClickException("Decryption failed. Wrong passphrase?")

    with open(env_file, "wb") as fh:
        fh.write(plaintext)
    record_event("pull", env_name, success=True)
    click.echo(f"Pulled '{env_name}' to '{env_file}'.")


@cli.command()
@click.argument("env_name")
def check(env_name: str):
    """Check whether a remote env exists."""
    backend = get_backend()
    if backend.exists(env_name):
        click.echo(f"'{env_name}' exists in remote storage.")
    else:
        click.echo(f"'{env_name}' does NOT exist in remote storage.")


cli.add_command(audit_log)
cli.add_command(keys_group, name="keys")
cli.add_command(rotate_group, name="rotate")
cli.add_command(share_group, name="share")
cli.add_command(snapshot_group, name="snapshot")
cli.add_command(lock_group, name="lock")
