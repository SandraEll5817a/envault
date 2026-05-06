"""CLI commands for generating and verifying share tokens."""

import os

import click

from envault.share import create_token, verify_token

_DEFAULT_TTL = 3600


@click.group("share")
def share_group():
    """Generate and verify time-limited share tokens."""


@share_group.command("create")
@click.argument("bucket")
@click.argument("key")
@click.option(
    "--ttl",
    default=_DEFAULT_TTL,
    show_default=True,
    help="Token lifetime in seconds.",
)
@click.option(
    "--secret",
    envvar="ENVAULT_SHARE_SECRET",
    required=True,
    help="Signing secret (or set ENVAULT_SHARE_SECRET).",
)
def share_create(bucket: str, key: str, ttl: int, secret: str):
    """Create a signed share token for BUCKET/KEY."""
    token = create_token(bucket, key, secret, ttl=ttl)
    click.echo(token)


@share_group.command("verify")
@click.argument("token")
@click.option(
    "--secret",
    envvar="ENVAULT_SHARE_SECRET",
    required=True,
    help="Signing secret (or set ENVAULT_SHARE_SECRET).",
)
def share_verify(token: str, secret: str):
    """Verify a share token and display its claims."""
    result = verify_token(token, secret)
    if result is None:
        click.echo("Invalid or expired token.", err=True)
        raise SystemExit(1)
    click.echo(f"bucket    : {result.bucket}")
    click.echo(f"key       : {result.key}")
    click.echo(f"token_id  : {result.token_id}")
    import datetime
    exp = datetime.datetime.utcfromtimestamp(result.expires_at).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    click.echo(f"expires_at: {exp}")
    click.echo("Status    : valid")
