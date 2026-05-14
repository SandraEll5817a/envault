"""Tests for envault.env_diff_report."""

from __future__ import annotations

import pytest

from envault.env_diff_report import build_report, DiffReport


OLD_ENV = """DB_HOST=localhost
DB_PORT=5432
SECRET=old_secret
"""

NEW_ENV = """DB_HOST=localhost
DB_PORT=5433
API_KEY=abc123
"""


def test_build_report_returns_diff_report():
    report = build_report(OLD_ENV, NEW_ENV)
    assert isinstance(report, DiffReport)


def test_build_report_detects_added():
    report = build_report(OLD_ENV, NEW_ENV)
    assert "API_KEY" in report.added


def test_build_report_detects_removed():
    report = build_report(OLD_ENV, NEW_ENV)
    assert "SECRET" in report.removed


def test_build_report_detects_changed():
    report = build_report(OLD_ENV, NEW_ENV)
    assert "DB_PORT" in report.changed


def test_build_report_unchanged_key_not_in_any_list():
    report = build_report(OLD_ENV, NEW_ENV)
    assert "DB_HOST" not in report.added
    assert "DB_HOST" not in report.removed
    assert "DB_HOST" not in report.changed


def test_has_changes_true_when_differences():
    report = build_report(OLD_ENV, NEW_ENV)
    assert report.has_changes is True


def test_has_changes_false_when_identical():
    report = build_report(OLD_ENV, OLD_ENV)
    assert report.has_changes is False


def test_render_no_changes_message():
    report = build_report(OLD_ENV, OLD_ENV)
    output = report.render()
    assert "No changes detected" in output


def test_render_shows_added_key():
    report = build_report(OLD_ENV, NEW_ENV)
    output = report.render()
    assert "+ API_KEY" in output


def test_render_shows_removed_key():
    report = build_report(OLD_ENV, NEW_ENV)
    output = report.render()
    assert "- SECRET" in output


def test_render_shows_changed_key():
    report = build_report(OLD_ENV, NEW_ENV)
    output = report.render()
    assert "~ DB_PORT" in output


def test_render_show_values_reveals_new_value():
    report = build_report(OLD_ENV, NEW_ENV)
    output = report.render(show_values=True)
    assert "abc123" in output


def test_render_show_values_reveals_old_and_new_for_changed():
    report = build_report(OLD_ENV, NEW_ENV)
    output = report.render(show_values=True)
    assert "5432" in output
    assert "5433" in output


def test_render_summary_line_counts():
    report = build_report(OLD_ENV, NEW_ENV)
    output = report.render()
    assert "1 added" in output
    assert "1 removed" in output
    assert "1 changed" in output


def test_build_report_custom_labels():
    report = build_report(OLD_ENV, NEW_ENV, env_name="staging", old_label="v1", new_label="v2")
    output = report.render()
    assert "staging" in output
    assert "v1" in output
    assert "v2" in output
