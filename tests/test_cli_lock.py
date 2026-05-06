"""Tests for envault.cli_lock."""

import os
import json
import time
import pytest
from click.testing import CliRunner
from unittest.mock import patch

import envault.lock as lock_module
from envault.cli_lock import lock_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated_locks(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


def test_lock_status_no_lock(runner):
    result = runner.invoke(lock_group, ["status", "myenv"])
    assert result.exit_code == 0
    assert "No lock found" in result.output


def test_lock_status_active(runner):
    lock_module.acquire_lock("myenv")
    result = runner.invoke(lock_group, ["status", "myenv"])
    assert result.exit_code == 0
    assert "ACTIVE" in result.output
    assert str(os.getpid()) in result.output
    lock_module.release_lock("myenv")


def test_lock_status_stale(runner):
    path = lock_module._lock_path("stale")
    path.write_text(json.dumps({"pid": 99999999, "acquired_at": time.time()}))
    with patch.object(lock_module, "_pid_alive", return_value=False):
        result = runner.invoke(lock_group, ["status", "stale"])
    assert "STALE" in result.output


def test_lock_release_existing(runner):
    lock_module.acquire_lock("myenv")
    result = runner.invoke(lock_group, ["release", "--force", "myenv"])
    assert result.exit_code == 0
    assert "released" in result.output


def test_lock_release_nonexistent(runner):
    result = runner.invoke(lock_group, ["release", "--force", "ghost"])
    assert result.exit_code == 0
    assert "No lock found" in result.output


def test_lock_release_active_without_force(runner):
    lock_module.acquire_lock("myenv")
    result = runner.invoke(lock_group, ["release", "myenv"])
    assert result.exit_code != 0
    assert "active process" in result.output
    lock_module.release_lock("myenv")


def test_lock_list_empty(runner):
    result = runner.invoke(lock_group, ["list"])
    assert result.exit_code == 0
    assert "No locks found" in result.output


def test_lock_list_shows_locks(runner):
    lock_module.acquire_lock("env-a")
    lock_module.acquire_lock("env-b")
    result = runner.invoke(lock_group, ["list"])
    assert "env-a" in result.output
    assert "env-b" in result.output
    lock_module.release_lock("env-a")
    lock_module.release_lock("env-b")
