"""CLI commands for .env template validation."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_template import validate_files


@click.group("template")
def template_group() -> None:
    """Validate .env files against a template."""


@template_group.command("check")
@click.argument("env_file", default=".env", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--template",
    "template_file",
    default=None,
    type=click.Path(path_type=Path),
    help="Path to .env.template (defaults to <env_file>.template).",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Fail when extra keys exist in the env file.",
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress output on success.")
def template_check(
    env_file: Path,
    template_file: Path | None,
    strict: bool,
    quiet: bool,
) -> None:
    """Check ENV_FILE against its template for missing or extra keys."""
    try:
        result = validate_files(env_file, template_path=template_file, strict=strict)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.ok:
        if not quiet:
            click.echo(click.style("\u2713 All keys match the template.", fg="green"))
        raise SystemExit(0)

    click.echo(click.style(result.summary(), fg="red"), err=True)
    raise SystemExit(1)


@template_group.command("show")
@click.argument("env_file", default=".env", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--template",
    "template_file",
    default=None,
    type=click.Path(path_type=Path),
    help="Path to .env.template (defaults to <env_file>.template).",
)
@click.option("--strict", is_flag=True, default=False)
def template_show(
    env_file: Path,
    template_file: Path | None,
    strict: bool,
) -> None:
    """Show a diff-style summary between ENV_FILE and its template."""
    try:
        result = validate_files(env_file, template_path=template_file, strict=strict)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
