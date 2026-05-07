"""Track push/pull history for each environment key."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

APP_DIR = Path(os.environ.get("ENVAULT_HOME", Path.home() / ".envault"))
HISTORY_FILE = APP_DIR / "history.json"


def _get_history_path() -> Path:
    return Path(os.environ.get("ENVAULT_HISTORY_PATH", str(HISTORY_FILE)))


def _load_history() -> List[dict]:
    path = _get_history_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(entries: List[dict]) -> None:
    path = _get_history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_push(key: str, backend: str, version: Optional[str] = None) -> dict:
    """Record a push event for the given key."""
    entry = {
        "action": "push",
        "key": key,
        "backend": backend,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entries = _load_history()
    entries.append(entry)
    _save_history(entries)
    return entry


def record_pull(key: str, backend: str, version: Optional[str] = None) -> dict:
    """Record a pull event for the given key."""
    entry = {
        "action": "pull",
        "key": key,
        "backend": backend,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entries = _load_history()
    entries.append(entry)
    _save_history(entries)
    return entry


def get_history(key: Optional[str] = None, action: Optional[str] = None, limit: int = 50) -> List[dict]:
    """Return history entries, optionally filtered by key and/or action."""
    entries = _load_history()
    if key:
        entries = [e for e in entries if e.get("key") == key]
    if action:
        entries = [e for e in entries if e.get("action") == action]
    return entries[-limit:]


def clear_history(key: Optional[str] = None) -> int:
    """Clear history. If key is given, only remove entries for that key.
    Returns number of entries removed."""
    entries = _load_history()
    if key:
        remaining = [e for e in entries if e.get("key") != key]
    else:
        remaining = []
    removed = len(entries) - len(remaining)
    _save_history(remaining)
    return removed
