"""Tests for envault.audit module."""

import json
import os
from pathlib import Path

import pytest

from envault.audit import record_event, read_events


@pytest.fixture(autouse=True)
def isolated_audit_log(tmp_path, monkeypatch):
    """Redirect audit log to a temp file for each test."""
    log_file = tmp_path / "audit.log"
    monkeypatch.setenv("ENVAULT_AUDIT_LOG", str(log_file))
    return log_file


def test_record_event_returns_dict():
    event = record_event("push", "myproject/.env", "s3")
    assert isinstance(event, dict)
    assert event["action"] == "push"
    assert event["env_key"] == "myproject/.env"
    assert event["backend"] == "s3"
    assert event["success"] is True


def test_record_event_writes_to_log(isolated_audit_log):
    record_event("pull", "myproject/.env", "gcs", user="alice")
    lines = isolated_audit_log.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["user"] == "alice"
    assert data["action"] == "pull"


def test_record_event_appends_multiple(isolated_audit_log):
    record_event("push", "proj/.env", "s3")
    record_event("pull", "proj/.env", "s3")
    record_event("check", "proj/.env", "s3")
    lines = isolated_audit_log.read_text().strip().splitlines()
    assert len(lines) == 3


def test_record_event_failure_flag():
    event = record_event("push", "proj/.env", "s3", success=False, detail="Access denied")
    assert event["success"] is False
    assert event["detail"] == "Access denied"


def test_read_events_empty_when_no_log():
    events = read_events()
    assert events == []


def test_read_events_returns_most_recent_first(isolated_audit_log):
    for i in range(5):
        record_event("push", f"proj/{i}/.env", "s3")
    events = read_events(limit=5)
    assert len(events) == 5
    # Most recent (index 4) should be first
    assert events[0]["env_key"] == "proj/4/.env"


def test_read_events_respects_limit(isolated_audit_log):
    for i in range(10):
        record_event("push", f"proj/{i}/.env", "s3")
    events = read_events(limit=3)
    assert len(events) == 3


def test_record_event_includes_timestamp():
    event = record_event("check", "proj/.env", "s3")
    assert "timestamp" in event
    assert "T" in event["timestamp"]  # ISO format check
