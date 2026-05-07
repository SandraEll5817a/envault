"""Tests for envault.history module."""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path

from envault.history import (
    record_push,
    record_pull,
    get_history,
    clear_history,
)


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setenv("ENVAULT_HISTORY_PATH", str(history_file))
    yield history_file


def test_record_push_returns_dict():
    entry = record_push("prod", "s3")
    assert entry["action"] == "push"
    assert entry["key"] == "prod"
    assert entry["backend"] == "s3"
    assert "timestamp" in entry


def test_record_pull_returns_dict():
    entry = record_pull("staging", "gcs", version="v2")
    assert entry["action"] == "pull"
    assert entry["key"] == "staging"
    assert entry["version"] == "v2"


def test_record_push_writes_to_file(isolated_history):
    record_push("prod", "s3")
    data = json.loads(isolated_history.read_text())
    assert len(data) == 1
    assert data[0]["action"] == "push"


def test_multiple_records_appended(isolated_history):
    record_push("prod", "s3")
    record_pull("prod", "s3")
    record_push("dev", "s3")
    data = json.loads(isolated_history.read_text())
    assert len(data) == 3


def test_get_history_returns_all():
    record_push("prod", "s3")
    record_pull("dev", "gcs")
    entries = get_history()
    assert len(entries) == 2


def test_get_history_filter_by_key():
    record_push("prod", "s3")
    record_push("dev", "s3")
    record_pull("prod", "s3")
    entries = get_history(key="prod")
    assert len(entries) == 2
    assert all(e["key"] == "prod" for e in entries)


def test_get_history_filter_by_action():
    record_push("prod", "s3")
    record_pull("prod", "s3")
    record_push("dev", "s3")
    entries = get_history(action="push")
    assert len(entries) == 2
    assert all(e["action"] == "push" for e in entries)


def test_get_history_limit():
    for i in range(10):
        record_push(f"key{i}", "s3")
    entries = get_history(limit=3)
    assert len(entries) == 3


def test_get_history_empty_file():
    entries = get_history()
    assert entries == []


def test_clear_history_all():
    record_push("prod", "s3")
    record_pull("dev", "gcs")
    removed = clear_history()
    assert removed == 2
    assert get_history() == []


def test_clear_history_by_key():
    record_push("prod", "s3")
    record_push("dev", "s3")
    record_pull("prod", "s3")
    removed = clear_history(key="prod")
    assert removed == 2
    remaining = get_history()
    assert len(remaining) == 1
    assert remaining[0]["key"] == "dev"
