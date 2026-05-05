"""Tests for envault.keys key management module."""

import pytest
from pathlib import Path
from envault.keys import set_key, get_key, delete_key, list_keys


@pytest.fixture
def keystore(tmp_path):
    return tmp_path / "test_keys.json"


def test_set_and_get_key(keystore):
    set_key("prod", "supersecret", keystore_path=keystore)
    assert get_key("prod", keystore_path=keystore) == "supersecret"


def test_get_missing_key_returns_none(keystore):
    assert get_key("nonexistent", keystore_path=keystore) is None


def test_set_key_overwrites_existing(keystore):
    set_key("prod", "first", keystore_path=keystore)
    set_key("prod", "second", keystore_path=keystore)
    assert get_key("prod", keystore_path=keystore) == "second"


def test_list_keys_empty(keystore):
    assert list_keys(keystore_path=keystore) == []


def test_list_keys_multiple(keystore):
    set_key("prod", "pass1", keystore_path=keystore)
    set_key("staging", "pass2", keystore_path=keystore)
    keys = list_keys(keystore_path=keystore)
    assert set(keys) == {"prod", "staging"}


def test_delete_existing_key(keystore):
    set_key("prod", "secret", keystore_path=keystore)
    result = delete_key("prod", keystore_path=keystore)
    assert result is True
    assert get_key("prod", keystore_path=keystore) is None


def test_delete_missing_key_returns_false(keystore):
    result = delete_key("ghost", keystore_path=keystore)
    assert result is False


def test_keystore_file_permissions(keystore):
    import stat as stat_mod
    set_key("prod", "secret", keystore_path=keystore)
    mode = keystore.stat().st_mode
    # Only owner read/write should be set
    assert bool(mode & stat_mod.S_IRUSR)
    assert bool(mode & stat_mod.S_IWUSR)
    assert not bool(mode & stat_mod.S_IRGRP)
    assert not bool(mode & stat_mod.S_IROTH)


def test_keystore_created_in_parent_dir(tmp_path):
    nested = tmp_path / "deep" / "nested" / "keys.json"
    set_key("x", "y", keystore_path=nested)
    assert nested.exists()
