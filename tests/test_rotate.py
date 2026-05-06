"""Unit tests for envault.rotate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from envault.crypto import encrypt, decrypt
from envault.rotate import rotate_key, rotate_all, RotationResult


OLD_PASS = "old-secret"
NEW_PASS = "new-secret"
PLAINTEXT = b"API_KEY=abc123\nDB_URL=postgres://localhost/dev"


@pytest.fixture()
def backend_with_object():
    """Mock backend that holds one encrypted object."""
    ciphertext = encrypt(PLAINTEXT, OLD_PASS)
    store: dict[str, bytes] = {"prod/.env": ciphertext}

    backend = MagicMock()
    backend.download.side_effect = lambda k: store.get(k)
    backend.upload.side_effect = lambda k, v: store.update({k: v})
    return backend, store


def test_rotate_key_success(backend_with_object):
    backend, store = backend_with_object
    result = rotate_key(backend, "prod/.env", OLD_PASS, NEW_PASS)

    assert result.success is True
    assert result.error is None
    # The stored blob must now be decryptable with the NEW passphrase
    assert decrypt(store["prod/.env"], NEW_PASS) == PLAINTEXT


def test_rotate_key_old_pass_no_longer_works(backend_with_object):
    backend, store = backend_with_object
    rotate_key(backend, "prod/.env", OLD_PASS, NEW_PASS)

    with pytest.raises(Exception):
        decrypt(store["prod/.env"], OLD_PASS)


def test_rotate_key_missing_object():
    backend = MagicMock()
    backend.download.return_value = None

    result = rotate_key(backend, "missing/.env", OLD_PASS, NEW_PASS)

    assert result.success is False
    assert "not found" in (result.error or "")
    backend.upload.assert_not_called()


def test_rotate_key_wrong_passphrase(backend_with_object):
    backend, _ = backend_with_object
    result = rotate_key(backend, "prod/.env", "wrong-pass", NEW_PASS)

    assert result.success is False
    assert result.error is not None


def test_rotate_all_returns_results(backend_with_object):
    ciphertext_a = encrypt(b"A=1", OLD_PASS)
    ciphertext_b = encrypt(b"B=2", OLD_PASS)
    store = {"a/.env": ciphertext_a, "b/.env": ciphertext_b}

    backend = MagicMock()
    backend.download.side_effect = lambda k: store.get(k)
    backend.upload.side_effect = lambda k, v: store.update({k: v})

    results = rotate_all(backend, ["a/.env", "b/.env"], OLD_PASS, NEW_PASS)

    assert len(results) == 2
    assert all(r.success for r in results)
