"""Tests for the audit log CLI command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_audit import audit_log
from envault.audit import record_event


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated_audit_log(tmp_path, monkeypatch):
    log_file = tmp_path / "audit.log"
    monkeypatch.setenv("ENVAULT_AUDIT_LOG", str(log_file))
    return log_file


def test_audit_log_no_events(runner):
    result = runner.invoke(audit_log, [])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_audit_log_shows_events(runner):
    record_event("push", "myproject/.env", "s3", user="bob")
    record_event("pull", "myproject/.env", "s3", user="alice")
    result = runner.invoke(audit_log, [])
    assert result.exit_code == 0
    assert "push" in result.output
    assert "pull" in result.output
    assert "bob" in result.output
    assert "alice" in result.output


def test_audit_log_filter_by_action(runner):
    record_event("push", "proj/.env", "s3", user="carol")
    record_event("pull", "proj/.env", "s3", user="dave")
    result = runner.invoke(audit_log, ["--action", "push"])
    assert result.exit_code == 0
    assert "carol" in result.output
    assert "dave" not in result.output


def test_audit_log_filter_by_user(runner):
    record_event("push", "proj/.env", "s3", user="carol")
    record_event("push", "proj/.env", "s3", user="dave")
    result = runner.invoke(audit_log, ["--user", "carol"])
    assert result.exit_code == 0
    assert "carol" in result.output
    assert "dave" not in result.output


def test_audit_log_respects_limit(runner):
    for i in range(10):
        record_event("push", f"proj/{i}/.env", "s3", user="tester")
    result = runner.invoke(audit_log, ["--limit", "3"])
    assert result.exit_code == 0
    # Table rows: each row contains 'tester'; count occurrences
    assert result.output.count("tester") == 3


def test_audit_log_shows_failure_status(runner):
    record_event("push", "proj/.env", "s3", success=False, detail="Bucket not found")
    result = runner.invoke(audit_log, [])
    assert result.exit_code == 0
    assert "FAIL" in result.output
    assert "Bucket not found" in result.output
