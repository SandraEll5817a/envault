"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt, derive_key, SALT_SIZE


PASSPHRASE = "super-secret-passphrase"
SAMPLE_PLAINTEXT = b"DATABASE_URL=postgres://user:pass@localhost/db\nSECRET_KEY=abc123\n"


def test_encrypt_returns_bytes():
    result = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert isinstance(result, bytes)


def test_encrypted_length_greater_than_salt():
    result = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert len(result) > SALT_SIZE


def test_encrypt_decrypt_roundtrip():
    ciphertext = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    plaintext = decrypt(ciphertext, PASSPHRASE)
    assert plaintext == SAMPLE_PLAINTEXT


def test_encrypt_produces_different_ciphertext_each_time():
    """Each encryption should produce a unique ciphertext due to random salt."""
    ct1 = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    ct2 = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert ct1 != ct2


def test_decrypt_wrong_passphrase_raises():
    ciphertext = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(ciphertext, "wrong-passphrase")


def test_decrypt_corrupted_data_raises():
    ciphertext = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    corrupted = ciphertext[:SALT_SIZE] + b"\x00" * (len(ciphertext) - SALT_SIZE)
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSPHRASE)


def test_decrypt_too_short_raises():
    with pytest.raises(ValueError, match="too short"):
        decrypt(b"short", PASSPHRASE)


def test_derive_key_same_inputs_same_output():
    salt = b"\x01" * 16
    key1 = derive_key(PASSPHRASE, salt)
    key2 = derive_key(PASSPHRASE, salt)
    assert key1 == key2


def test_derive_key_different_salts_different_keys():
    salt1 = b"\x01" * 16
    salt2 = b"\x02" * 16
    assert derive_key(PASSPHRASE, salt1) != derive_key(PASSPHRASE, salt2)
