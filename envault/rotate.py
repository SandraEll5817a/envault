"""Key rotation: re-encrypt stored .env files with a new passphrase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envault.crypto import reencrypt
from envault.storage import StorageBackend
from envault.audit import record_event


@dataclass
class RotationResult:
    key: str
    success: bool
    error: Optional[str] = None


def rotate_key(
    backend: StorageBackend,
    key: str,
    old_passphrase: str,
    new_passphrase: str,
) -> RotationResult:
    """Download, re-encrypt, and re-upload a single object."""
    try:
        ciphertext = backend.download(key)
        if ciphertext is None:
            return RotationResult(key=key, success=False, error="object not found")

        new_ciphertext = reencrypt(ciphertext, old_passphrase, new_passphrase)
        backend.upload(key, new_ciphertext)

        record_event(action="rotate", key=key, success=True)
        return RotationResult(key=key, success=True)
    except Exception as exc:  # noqa: BLE001
        record_event(action="rotate", key=key, success=False, detail=str(exc))
        return RotationResult(key=key, success=False, error=str(exc))


def rotate_all(
    backend: StorageBackend,
    keys: list[str],
    old_passphrase: str,
    new_passphrase: str,
) -> list[RotationResult]:
    """Rotate every key in *keys* and return per-key results."""
    return [
        rotate_key(backend, k, old_passphrase, new_passphrase)
        for k in keys
    ]
