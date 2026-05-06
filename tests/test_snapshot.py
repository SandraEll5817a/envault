"""Tests for envault.snapshot and envault.cli_snapshot."""

from __future__ import annotations

import json
import time

import pytest
from click.testing import CliRunner

from envault.snapshot import (
    save_snapshot,
    load_snapshot,
    has_changed,
    delete_snapshot,
    _checksum,
)
from envault.cli_snapshot import snapshot_group


@pytest.fixture(autouse=True)
def isolated_snapshots(tmp_path, monkeypatch):
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    import envault.snapshot as sm
    monkeypatch.setattr(sm, "_SNAPSHOT_DIR", snap_dir)
    import envault.cli_snapshot as cs
    monkeypatch.setattr(cs, "_SNAPSHOT_DIR", snap_dir)
    yield snap_dir


CONTENT = b"KEY=value\nSECRET=abc\n"


def test_save_snapshot_returns_snapshot():
    snap = save_snapshot("myapp/prod", CONTENT)
    assert snap.env_key == "myapp/prod"
    assert snap.checksum == _checksum(CONTENT)
    assert snap.size == len(CONTENT)


def test_load_snapshot_roundtrip():
    save_snapshot("myapp/prod", CONTENT, extra={"pushed_by": "alice"})
    snap = load_snapshot("myapp/prod")
    assert snap is not None
    assert snap.checksum == _checksum(CONTENT)
    assert snap.extra["pushed_by"] == "alice"


def test_load_snapshot_missing_returns_none():
    assert load_snapshot("nonexistent/key") is None


def test_has_changed_no_snapshot():
    assert has_changed("fresh/key", CONTENT) is True


def test_has_changed_same_content():
    save_snapshot("app/dev", CONTENT)
    assert has_changed("app/dev", CONTENT) is False


def test_has_changed_different_content():
    save_snapshot("app/dev", CONTENT)
    assert has_changed("app/dev", b"OTHER=1\n") is True


def test_delete_snapshot_existing():
    save_snapshot("app/staging", CONTENT)
    assert delete_snapshot("app/staging") is True
    assert load_snapshot("app/staging") is None


def test_delete_snapshot_missing():
    assert delete_snapshot("ghost/key") is False


# --- CLI tests ---

@pytest.fixture
def runner():
    return CliRunner()


def test_cli_show_existing(runner):
    save_snapshot("app/prod", CONTENT)
    result = runner.invoke(snapshot_group, ["show", "app/prod"])
    assert result.exit_code == 0
    assert "checksum" in result.output
    assert "app/prod" in result.output


def test_cli_show_missing(runner):
    result = runner.invoke(snapshot_group, ["show", "missing/key"])
    assert result.exit_code != 0
    assert "No snapshot" in result.output


def test_cli_list(runner):
    save_snapshot("app/prod", CONTENT)
    save_snapshot("app/dev", CONTENT)
    result = runner.invoke(snapshot_group, ["list"])
    assert result.exit_code == 0
    assert "app/prod" in result.output
    assert "app/dev" in result.output


def test_cli_delete_existing(runner):
    save_snapshot("app/prod", CONTENT)
    result = runner.invoke(snapshot_group, ["delete", "app/prod"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_cli_delete_missing(runner):
    result = runner.invoke(snapshot_group, ["delete", "ghost/key"])
    assert result.exit_code != 0
