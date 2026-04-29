"""Command-line interface for envault."""

import sys
import click
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.storage import S3Backend, GCSBackend


def get_backend(backend: str, bucket: str):
    """Instantiate the appropriate storage backend."""
    if backend == "s3":
        return S3Backend(bucket)
    elif backend == "gcs":
        return GCSBackend(bucket)
    else:
        raise click.BadParameter(f"Unknown backend '{backend}'. Choose 's3' or 'gcs'.")


@click.group()
def cli():
    """envault — securely sync .env files via encrypted cloud storage."""


@cli.command("push")
@click.argument("env_file", default=".env", type=click.Path(exists=True))
@click.option("--key", required=True, envvar="ENVAULT_KEY", help="Encryption passphrase.")
@click.option("--bucket", required=True, envvar="ENVAULT_BUCKET", help="Storage bucket name.")
@click.option("--backend", default="s3", show_default=True, envvar="ENVAULT_BACKEND", help="Storage backend (s3 or gcs).")
@click.option("--remote-path", default="envault/.env.enc", show_default=True, help="Remote object path.")
def push(env_file, key, bucket, backend, remote_path):
    """Encrypt and upload a .env file to cloud storage."""
    data = Path(env_file).read_bytes()
    ciphertext = encrypt(data, key)
    storage = get_backend(backend, bucket)
    storage.upload(remote_path, ciphertext)
    click.echo(f"✓ Pushed '{env_file}' → {backend}://{bucket}/{remote_path}")


@cli.command("pull")
@click.argument("env_file", default=".env", type=click.Path())
@click.option("--key", required=True, envvar="ENVAULT_KEY", help="Encryption passphrase.")
@click.option("--bucket", required=True, envvar="ENVAULT_BUCKET", help="Storage bucket name.")
@click.option("--backend", default="s3", show_default=True, envvar="ENVAULT_BACKEND", help="Storage backend (s3 or gcs).")
@click.option("--remote-path", default="envault/.env.enc", show_default=True, help="Remote object path.")
def pull(env_file, key, bucket, backend, remote_path):
    """Download and decrypt a .env file from cloud storage."""
    storage = get_backend(backend, bucket)
    if not storage.exists(remote_path):
        click.echo(f"✗ Remote file not found: {backend}://{bucket}/{remote_path}", err=True)
        sys.exit(1)
    ciphertext = storage.download(remote_path)
    plaintext = decrypt(ciphertext, key)
    Path(env_file).write_bytes(plaintext)
    click.echo(f"✓ Pulled {backend}://{bucket}/{remote_path} → '{env_file}'")


@cli.command("check")
@click.option("--bucket", required=True, envvar="ENVAULT_BUCKET", help="Storage bucket name.")
@click.option("--backend", default="s3", show_default=True, envvar="ENVAULT_BACKEND", help="Storage backend (s3 or gcs).")
@click.option("--remote-path", default="envault/.env.enc", show_default=True, help="Remote object path.")
def check(bucket, backend, remote_path):
    """Check whether a remote .env file exists."""
    storage = get_backend(backend, bucket)
    if storage.exists(remote_path):
        click.echo(f"✓ Found: {backend}://{bucket}/{remote_path}")
    else:
        click.echo(f"✗ Not found: {backend}://{bucket}/{remote_path}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
