"""Tests for envault.lock."""

import os
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch

import envault.lock as lock_module
from envault.lock import acquire_lock, release_lock, read_lock, is_locked


@pytest.fixture(autouse=True)
def isolated_locks(tmp_path, monkeypatch):
    """Redirect lock files to a temporary directory."""
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


def test_acquire_lock_creates_file():
    assert acquire_lock("myenv")
    info = read_lock("myenv")
    assert info is not None
    assert info["pid"] == os.getpid()


def test_release_lock_removes_file():
    acquire_lock("myenv")
    assert release_lock("myenv") is True
    assert read_lock("myenv") is None


def test_release_nonexistent_lock_returns_false():
    assert release_lock("ghost") is False


def test_is_locked_returns_true_for_self():
    acquire_lock("myenv")
    assert is_locked("myenv") is True


def test_is_locked_returns_false_after_release():
    acquire_lock("myenv")
    release_lock("myenv")
    assert is_locked("myenv") is False


def test_stale_lock_is_cleared_on_acquire(tmp_path):
    """A lock from a dead PID should be cleared and re-acquired."""
    dead_pid = 99999999
    path = lock_module._lock_path("stale")
    path.write_text(json.dumps({"pid": dead_pid, "acquired_at": time.time()}))

    with patch.object(lock_module, "_pid_alive", return_value=False):
        result = acquire_lock("stale", timeout=2)

    assert result is True
    info = read_lock("stale")
    assert info["pid"] == os.getpid()


def test_acquire_lock_timeout_returns_false():
    """If the lock is held by an 'alive' process, acquisition should time out."""
    acquire_lock("busy")
    with patch.object(lock_module, "_pid_alive", return_value=True):
        result = acquire_lock("busy", timeout=1)
    assert result is False
    release_lock("busy")


def test_read_lock_returns_none_for_missing():
    assert read_lock("nonexistent") is None
