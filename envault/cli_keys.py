"""CLI commands for managing named passphrases in the local keystore."""

import click
from envault.keys import set_key, get_key, delete_key, list_keys


@click.group("keys")
def keys_group():
    """Manage named encryption passphrases."""
    pass


@keys_group.command("set")
@click.argument("name")
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Passphrase to store (prompted if omitted).",
)
def keys_set(name: str, passphrase: str):
    """Store a named passphrase in the local keystore."""
    set_key(name, passphrase)
    click.echo(f"Key '{name}' saved.")


@keys_group.command("get")
@click.argument("name")
def keys_get(name: str):
    """Print a stored passphrase by name."""
    value = get_key(name)
    if value is None:
        click.echo(f"Key '{name}' not found.", err=True)
        raise SystemExit(1)
    click.echo(value)


@keys_group.command("delete")
@click.argument("name")
@click.confirmation_option(prompt=f"Are you sure you want to delete this key?")
def keys_delete(name: str):
    """Delete a named passphrase from the keystore."""
    removed = delete_key(name)
    if removed:
        click.echo(f"Key '{name}' deleted.")
    else:
        click.echo(f"Key '{name}' not found.", err=True)
        raise SystemExit(1)


@keys_group.command("list")
def keys_list():
    """List all stored key names."""
    names = list_keys()
    if not names:
        click.echo("No keys stored.")
    else:
        for name in names:
            click.echo(name)
