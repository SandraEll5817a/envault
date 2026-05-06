"""Main CLI entry-point for envault."""

from __future__ import annotations

import click

from envault.storage import S3Backend, GCSBackend, StorageBackend
from envault.crypto import encrypt, decrypt
from envault.audit import record_event


def get_backend(backend_type: str, bucket: str) -> StorageBackend:
    """Instantiate the requested storage backend."""
    if backend_type == "s3":
        return S3Backend(bucket)
    if backend_type == "gcs":
        return GCSBackend(bucket)
    raise click.BadParameter(f"Unknown backend: {backend_type}")


@click.group()
def cli() -> None:
    """envault — securely sync .env files via encrypted cloud storage."""


@cli.command()
@click.argument("key")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--backend", "backend_type", default="s3", show_default=True)
@click.option("--bucket", envvar="ENVAULT_BUCKET", required=True)
def push(
    key: str,
    env_file: str,
    passphrase: str,
    backend_type: str,
    bucket: str,
) -> None:
    """Encrypt and upload a .env file."""
    backend = get_backend(backend_type, bucket)
    with open(env_file, "rb") as fh:
        plaintext = fh.read()
    ciphertext = encrypt(plaintext, passphrase)
    backend.upload(key, ciphertext)
    record_event(action="push", key=key, success=True)
    click.echo(f"Pushed {env_file} → {key}")


@cli.command()
@click.argument("key")
@click.argument("dest", type=click.Path())
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--backend", "backend_type", default="s3", show_default=True)
@click.option("--bucket", envvar="ENVAULT_BUCKET", required=True)
def pull(
    key: str,
    dest: str,
    passphrase: str,
    backend_type: str,
    bucket: str,
) -> None:
    """Download and decrypt a .env file."""
    backend = get_backend(backend_type, bucket)
    ciphertext = backend.download(key)
    if ciphertext is None:
        record_event(action="pull", key=key, success=False, detail="not found")
        click.echo(f"Error: {key} not found in bucket.", err=True)
        raise SystemExit(1)
    plaintext = decrypt(ciphertext, passphrase)
    with open(dest, "wb") as fh:
        fh.write(plaintext)
    record_event(action="pull", key=key, success=True)
    click.echo(f"Pulled {key} → {dest}")


@cli.command()
@click.argument("key")
@click.option("--backend", "backend_type", default="s3", show_default=True)
@click.option("--bucket", envvar="ENVAULT_BUCKET", required=True)
def check(key: str, backend_type: str, bucket: str) -> None:
    """Check whether a key exists in the bucket."""
    backend = get_backend(backend_type, bucket)
    if backend.exists(key):
        click.echo(f"{key} exists.")
    else:
        click.echo(f"{key} does not exist.")


# Register sub-command groups from other modules
from envault.cli_audit import audit_log  # noqa: E402
from envault.cli_keys import keys_group  # noqa: E402
from envault.cli_rotate import rotate_group  # noqa: E402

cli.add_command(audit_log)
cli.add_command(keys_group, name="keys")
cli.add_command(rotate_group, name="rotate")
