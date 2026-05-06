"""Shareable, time-limited access tokens for envault objects."""

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

_DEFAULT_TTL = 3600  # 1 hour


@dataclass
class ShareToken:
    bucket: str
    key: str
    issued_at: float
    expires_at: float
    token_id: str

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "bucket": self.bucket,
            "key": self.key,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "token_id": self.token_id,
        }


def _sign(payload: bytes, secret: bytes) -> str:
    sig = hmac.new(secret, payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode()


def create_token(
    bucket: str,
    key: str,
    secret: str,
    ttl: int = _DEFAULT_TTL,
) -> str:
    """Create a signed, time-limited share token."""
    now = time.time()
    token_id = base64.urlsafe_b64encode(os.urandom(12)).decode()
    payload = {
        "bucket": bucket,
        "key": key,
        "issued_at": now,
        "expires_at": now + ttl,
        "token_id": token_id,
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    b64_payload = base64.urlsafe_b64encode(payload_bytes).decode()
    signature = _sign(payload_bytes, secret.encode())
    return f"{b64_payload}.{signature}"


def verify_token(token_str: str, secret: str) -> Optional[ShareToken]:
    """Verify a share token. Returns ShareToken or None if invalid/expired."""
    try:
        b64_payload, signature = token_str.rsplit(".", 1)
        payload_bytes = base64.urlsafe_b64decode(b64_payload)
        expected_sig = _sign(payload_bytes, secret.encode())
        if not hmac.compare_digest(signature, expected_sig):
            return None
        data = json.loads(payload_bytes)
        token = ShareToken(
            bucket=data["bucket"],
            key=data["key"],
            issued_at=data["issued_at"],
            expires_at=data["expires_at"],
            token_id=data["token_id"],
        )
        if token.is_expired():
            return None
        return token
    except Exception:
        return None
