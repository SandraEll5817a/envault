"""Main CLI entry point for envault."""

import os
import click
from envault.storage import S3Backend, GCSBackend
from envault.crypto import encrypt, decrypt
from envault.audit import record_event
from envault.cli_audit import audit_log
from envault.cli_keys import keys_group


def get_backend():
    backend = os.environ.get("ENVAULT_BACKEND", "s3").lower()
    bucket = os.environ.get("ENVAULT_BUCKET", "")
    prefix = os.environ.get("ENVAULT_PREFIX", "envault")
    if backend == "s3":
        return S3Backend(bucket=bucket, prefix=prefix)
    elif backend == "gcs":
        return GCSBackend(bucket=bucket, prefix=prefix)
    else:
        raise click.ClickException(f"Unknown backend: {backend}")


@click.group()
def cli():
    """envault — securely sync .env files via encrypted cloud storage."""
    pass


@cli.command()
@click.argument("env_file", default=".env")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--key", "remote_key", default="default", help="Remote object key name.")
def push(env_file, passphrase, remote_key):
    """Encrypt and upload a .env file."""
    try:
        with open(env_file, "rb") as f:
            plaintext = f.read()
        ciphertext = encrypt(plaintext, passphrase)
        backend = get_backend()
        backend.upload(remote_key, ciphertext)
        record_event(action="push", key=remote_key, success=True)
        click.echo(f"Pushed '{env_file}' as '{remote_key}'.")
    except Exception as e:
        record_event(action="push", key=remote_key, success=False, error=str(e))
        raise click.ClickException(str(e))


@cli.command()
@click.argument("env_file", default=".env")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--key", "remote_key", default="default", help="Remote object key name.")
def pull(env_file, passphrase, remote_key):
    """Download and decrypt a .env file."""
    try:
        backend = get_backend()
        if not backend.exists(remote_key):
            raise click.ClickException(f"Remote key '{remote_key}' not found.")
        ciphertext = backend.download(remote_key)
        plaintext = decrypt(ciphertext, passphrase)
        with open(env_file, "wb") as f:
            f.write(plaintext)
        record_event(action="pull", key=remote_key, success=True)
        click.echo(f"Pulled '{remote_key}' to '{env_file}'.")
    except click.ClickException:
        raise
    except Exception as e:
        record_event(action="pull", key=remote_key, success=False, error=str(e))
        raise click.ClickException(str(e))


@cli.command()
@click.option("--key", "remote_key", default="default")
def check(remote_key):
    """Check whether a remote .env file exists."""
    backend = get_backend()
    if backend.exists(remote_key):
        click.echo(f"'{remote_key}' exists in remote storage.")
    else:
        click.echo(f"'{remote_key}' does not exist in remote storage.")


cli.add_command(audit_log)
cli.add_command(keys_group)
