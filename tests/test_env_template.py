"""Tests for envault.env_template and envault.cli_template."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.env_template import TemplateResult, validate, validate_files
from envault.cli_template import template_group

# ---------------------------------------------------------------------------
# Unit tests – validate()
# ---------------------------------------------------------------------------

TEMPLATE = "DB_URL=\nSECRET_KEY=\nDEBUG=\n"
FULL_ENV = "DB_URL=postgres://localhost/db\nSECRET_KEY=s3cr3t\nDEBUG=true\n"
MISSING_ENV = "DB_URL=postgres://localhost/db\nDEBUG=true\n"  # missing SECRET_KEY
EXTRA_ENV = FULL_ENV + "EXTRA_VAR=oops\n"


def test_validate_all_present() -> None:
    result = validate(FULL_ENV, TEMPLATE)
    assert result.ok
    assert result.missing == []
    assert result.extra == []


def test_validate_missing_key() -> None:
    result = validate(MISSING_ENV, TEMPLATE)
    assert not result.ok
    assert "SECRET_KEY" in result.missing


def test_validate_extra_key_non_strict_ignored() -> None:
    result = validate(EXTRA_ENV, TEMPLATE, strict=False)
    assert result.ok  # extra keys are fine without strict
    assert result.extra == []


def test_validate_extra_key_strict_fails() -> None:
    result = validate(EXTRA_ENV, TEMPLATE, strict=True)
    assert not result.ok
    assert "EXTRA_VAR" in result.extra


def test_summary_ok_message() -> None:
    result = TemplateResult()
    assert "match" in result.summary()


def test_summary_lists_missing_and_extra() -> None:
    result = TemplateResult(missing=["FOO"], extra=["BAR"])
    summary = result.summary()
    assert "FOO" in summary
    assert "BAR" in summary


# ---------------------------------------------------------------------------
# validate_files()
# ---------------------------------------------------------------------------

def test_validate_files_roundtrip(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    tmpl = tmp_path / ".env.template"
    env.write_text(FULL_ENV)
    tmpl.write_text(TEMPLATE)
    result = validate_files(env, template_path=tmpl)
    assert result.ok


def test_validate_files_default_template_path(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    tmpl = tmp_path / ".env.template"  # auto-discovered
    env.write_text(FULL_ENV)
    tmpl.write_text(TEMPLATE)
    result = validate_files(env)  # no explicit template_path
    assert result.ok


def test_validate_files_missing_template_raises(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(FULL_ENV)
    with pytest.raises(FileNotFoundError):
        validate_files(env)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_check_success(runner: CliRunner, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    tmpl = tmp_path / ".env.template"
    env.write_text(FULL_ENV)
    tmpl.write_text(TEMPLATE)
    result = runner.invoke(template_group, ["check", str(env), "--template", str(tmpl)])
    assert result.exit_code == 0
    assert "match" in result.output


def test_cli_check_missing_key_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    tmpl = tmp_path / ".env.template"
    env.write_text(MISSING_ENV)
    tmpl.write_text(TEMPLATE)
    result = runner.invoke(template_group, ["check", str(env), "--template", str(tmpl)])
    assert result.exit_code != 0


def test_cli_check_quiet_no_output_on_success(runner: CliRunner, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    tmpl = tmp_path / ".env.template"
    env.write_text(FULL_ENV)
    tmpl.write_text(TEMPLATE)
    result = runner.invoke(template_group, ["check", str(env), "--template", str(tmpl), "--quiet"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_cli_show_summary(runner: CliRunner, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    tmpl = tmp_path / ".env.template"
    env.write_text(MISSING_ENV)
    tmpl.write_text(TEMPLATE)
    result = runner.invoke(template_group, ["show", str(env), "--template", str(tmpl)])
    assert "SECRET_KEY" in result.output
