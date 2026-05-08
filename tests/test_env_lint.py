"""Tests for envault.env_lint and envault.cli_lint."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.env_lint import lint, LintIssue
from envault.cli_lint import lint_group


# ---------------------------------------------------------------------------
# Unit tests for lint()
# ---------------------------------------------------------------------------

def test_lint_clean_file():
    content = "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n"
    result = lint(content)
    assert result.ok
    assert result.issues == []
    assert result.summary() == "No issues found."


def test_lint_duplicate_key():
    content = "KEY=a\nKEY=b\n"
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_lint_empty_value_warning():
    content = "SOME_VAR=\n"
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "W003" in codes
    assert result.ok  # only a warning


def test_lint_invalid_line_no_equals():
    content = "NOTAVALIDLINE\n"
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "E001" in codes
    assert not result.ok


def test_lint_empty_key():
    content = "=value\n"
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "E002" in codes


def test_lint_key_with_space():
    content = "MY KEY=value\n"
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "E003" in codes


def test_lint_unmatched_quote():
    content = 'DB_PASS="unmatched\n'
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_lint_placeholder_sensitive_key():
    content = "API_KEY=changeme\n"
    result = lint(content)
    codes = [i.code for i in result.issues]
    assert "W004" in codes


def test_lint_comments_and_blanks_ignored():
    content = "# This is a comment\n\nKEY=value\n"
    result = lint(content)
    assert result.issues == []


def test_lint_counts():
    content = "INVALID\nKEY=\nKEY=dup\n"
    result = lint(content)
    assert result.error_count >= 1
    assert result.warning_count >= 1


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


def test_cli_lint_check_clean(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\nOTHER=123\n")
    result = runner.invoke(lint_group, ["check", str(env_file)])
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_cli_lint_check_with_error(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("NOTVALID\n")
    result = runner.invoke(lint_group, ["check", str(env_file)])
    assert result.exit_code == 1


def test_cli_lint_check_strict_exits_on_warning(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("EMPTY_VAR=\n")
    result = runner.invoke(lint_group, ["check", "--strict", str(env_file)])
    assert result.exit_code == 1


def test_cli_lint_check_quiet_suppresses_output(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("NOTVALID\n")
    result = runner.invoke(lint_group, ["check", "--quiet", str(env_file)])
    assert result.output.strip() == ""
    assert result.exit_code == 1


def test_cli_lint_show_filter_warning(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=\nBAD LINE\n")
    result = runner.invoke(lint_group, ["show", "--severity", "warning", str(env_file)])
    assert result.exit_code == 0
    assert "W003" in result.output
    assert "E001" not in result.output


def test_cli_lint_show_no_issues(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")
    result = runner.invoke(lint_group, ["show", str(env_file)])
    assert "No issues to display" in result.output
