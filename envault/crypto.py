"""Encryption and decryption utilities for envault using Fernet symmetric encryption."""

import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
ITERATIONS = 390000


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a passphrase and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    raw_key = kdf.derive(passphrase.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """Encrypt plaintext bytes using a passphrase.

    Returns salt + encrypted payload as raw bytes.
    """
    salt = os.urandom(SALT_SIZE)
    key = derive_key(passphrase, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext)
    return salt + encrypted


def decrypt(ciphertext: bytes, passphrase: str) -> bytes:
    """Decrypt ciphertext bytes using a passphrase.

    Expects the format produced by `encrypt`: salt + encrypted payload.

    Raises:
        ValueError: If decryption fails due to a wrong passphrase or corrupt data.
    """
    if len(ciphertext) <= SALT_SIZE:
        raise ValueError("Ciphertext is too short to be valid.")

    salt = ciphertext[:SALT_SIZE]
    payload = ciphertext[SALT_SIZE:]
    key = derive_key(passphrase, salt)
    fernet = Fernet(key)

    try:
        return fernet.decrypt(payload)
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid passphrase or corrupted data.") from exc
