"""CLI commands for linting .env files."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .env_lint import lint


@click.group("lint")
def lint_group() -> None:
    """Lint .env files for common issues."""


@lint_group.command("check")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress output; rely on exit code only.",
)
def lint_check(env_file: str, strict: bool, quiet: bool) -> None:
    """Check ENV_FILE for lint issues."""
    content = Path(env_file).read_text(encoding="utf-8")
    result = lint(content)

    if not quiet:
        for issue in result.issues:
            color = "red" if issue.severity == "error" else "yellow"
            click.echo(click.style(str(issue), fg=color))

        click.echo(result.summary())

    passed = result.ok if not strict else not result.issues
    if not passed:
        sys.exit(1)


@lint_group.command("show")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--severity",
    type=click.Choice(["error", "warning", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Filter issues by severity.",
)
def lint_show(env_file: str, severity: str) -> None:
    """Display lint issues for ENV_FILE with optional severity filter."""
    content = Path(env_file).read_text(encoding="utf-8")
    result = lint(content)

    issues = result.issues
    if severity != "all":
        issues = [i for i in issues if i.severity == severity]

    if not issues:
        click.echo(click.style("No issues to display.", fg="green"))
        return

    for issue in issues:
        color = "red" if issue.severity == "error" else "yellow"
        click.echo(click.style(str(issue), fg=color))

    click.echo(f"\nShowing {len(issues)} issue(s) (filter: {severity}).")
