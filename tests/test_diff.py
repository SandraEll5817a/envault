"""Tests for envault.diff module."""

import pytest
from envault.diff import compute_diff, _parse_env, EnvDiff


LOCAL = """# local env
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=abc123
OLD_VAR=remove_me
"""

REMOTE = """# remote env
DB_HOST=prod.example.com
DB_PORT=5432
SECRET_KEY=abc123
NEW_VAR=hello
"""


def test_parse_env_basic():
    content = "FOO=bar\nBAZ=qux\n"
    result = _parse_env(content)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments_and_blanks():
    content = "# comment\n\nFOO=bar\n"
    result = _parse_env(content)
    assert result == {"FOO": "bar"}


def test_parse_env_handles_equals_in_value():
    content = "TOKEN=abc=def==\n"
    result = _parse_env(content)
    assert result == {"TOKEN": "abc=def=="}


def test_parse_env_skips_lines_without_equals():
    content = "NOEQUALS\nFOO=bar\n"
    result = _parse_env(content)
    assert result == {"FOO": "bar"}


def test_compute_diff_added():
    diff = compute_diff(LOCAL, REMOTE)
    assert "NEW_VAR" in diff.added


def test_compute_diff_removed():
    diff = compute_diff(LOCAL, REMOTE)
    assert "OLD_VAR" in diff.removed


def test_compute_diff_changed():
    diff = compute_diff(LOCAL, REMOTE)
    keys_changed = [k for k, _, _ in diff.changed]
    assert "DB_HOST" in keys_changed


def test_compute_diff_unchanged():
    diff = compute_diff(LOCAL, REMOTE)
    assert "DB_PORT" in diff.unchanged
    assert "SECRET_KEY" in diff.unchanged


def test_has_changes_true():
    diff = compute_diff(LOCAL, REMOTE)
    assert diff.has_changes is True


def test_has_changes_false():
    diff = compute_diff(LOCAL, LOCAL)
    assert diff.has_changes is False


def test_summary_no_changes():
    diff = compute_diff(LOCAL, LOCAL)
    assert diff.summary() == "No differences found."


def test_summary_contains_keys():
    diff = compute_diff(LOCAL, REMOTE)
    summary = diff.summary()
    assert "NEW_VAR" in summary
    assert "OLD_VAR" in summary
    assert "DB_HOST" in summary


def test_compute_diff_empty_files():
    diff = compute_diff("", "")
    assert not diff.has_changes
    assert diff.summary() == "No differences found."
