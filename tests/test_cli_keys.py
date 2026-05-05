"""Tests for the keys CLI commands."""

import pytest
from click.testing import CliRunner
from envault.cli_keys import keys_group
from envault.keys import set_key


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated_keystore(tmp_path, monkeypatch):
    keystore = tmp_path / "keys.json"
    monkeypatch.setenv("ENVAULT_KEYSTORE", str(keystore))
    return keystore


def test_keys_set_and_list(runner):
    result = runner.invoke(keys_group, ["set", "prod", "--passphrase", "mysecret"])
    assert result.exit_code == 0
    assert "Key 'prod' saved" in result.output

    result = runner.invoke(keys_group, ["list"])
    assert result.exit_code == 0
    assert "prod" in result.output


def test_keys_get_existing(runner):
    runner.invoke(keys_group, ["set", "staging", "--passphrase", "stgpass"])
    result = runner.invoke(keys_group, ["get", "staging"])
    assert result.exit_code == 0
    assert "stgpass" in result.output


def test_keys_get_missing(runner):
    result = runner.invoke(keys_group, ["get", "ghost"])
    assert result.exit_code != 0


def test_keys_list_empty(runner):
    result = runner.invoke(keys_group, ["list"])
    assert result.exit_code == 0
    assert "No keys stored" in result.output


def test_keys_delete_existing(runner):
    runner.invoke(keys_group, ["set", "temp", "--passphrase", "temppass"])
    result = runner.invoke(keys_group, ["delete", "temp", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output

    result = runner.invoke(keys_group, ["get", "temp"])
    assert result.exit_code != 0


def test_keys_delete_missing(runner):
    result = runner.invoke(keys_group, ["delete", "nope", "--yes"])
    assert result.exit_code != 0


def test_keys_set_overwrites(runner):
    runner.invoke(keys_group, ["set", "prod", "--passphrase", "first"])
    runner.invoke(keys_group, ["set", "prod", "--passphrase", "second"])
    result = runner.invoke(keys_group, ["get", "prod"])
    assert "second" in result.output
