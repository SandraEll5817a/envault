"""Snapshot management: save and compare local .env snapshots."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_SNAPSHOT_DIR = Path.home() / ".envault" / "snapshots"


def _get_snapshot_path(env_key: str) -> Path:
    safe = env_key.replace("/", "__")
    return _SNAPSHOT_DIR / f"{safe}.json"


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass
class Snapshot:
    env_key: str
    checksum: str
    timestamp: float
    size: int
    extra: dict = field(default_factory=dict)


def save_snapshot(env_key: str, content: bytes, extra: Optional[dict] = None) -> Snapshot:
    """Persist a snapshot record for the given env_key."""
    _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap = Snapshot(
        env_key=env_key,
        checksum=_checksum(content),
        timestamp=time.time(),
        size=len(content),
        extra=extra or {},
    )
    path = _get_snapshot_path(env_key)
    path.write_text(json.dumps({
        "env_key": snap.env_key,
        "checksum": snap.checksum,
        "timestamp": snap.timestamp,
        "size": snap.size,
        "extra": snap.extra,
    }))
    return snap


def load_snapshot(env_key: str) -> Optional[Snapshot]:
    """Load the most recent snapshot for env_key, or None if absent."""
    path = _get_snapshot_path(env_key)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Snapshot(
        env_key=data["env_key"],
        checksum=data["checksum"],
        timestamp=data["timestamp"],
        size=data["size"],
        extra=data.get("extra", {}),
    )


def has_changed(env_key: str, content: bytes) -> bool:
    """Return True if content differs from the stored snapshot."""
    snap = load_snapshot(env_key)
    if snap is None:
        return True
    return snap.checksum != _checksum(content)


def delete_snapshot(env_key: str) -> bool:
    """Remove snapshot for env_key. Returns True if it existed."""
    path = _get_snapshot_path(env_key)
    if path.exists():
        path.unlink()
        return True
    return False
