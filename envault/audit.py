"""Audit log for tracking push/pull operations on .env files."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_AUDIT_LOG_PATH = Path.home() / ".envault" / "audit.log"


def _get_log_path() -> Path:
    """Return the audit log path, respecting ENVAULT_AUDIT_LOG env var."""
    custom = os.environ.get("ENVAULT_AUDIT_LOG")
    return Path(custom) if custom else DEFAULT_AUDIT_LOG_PATH


def record_event(
    action: str,
    env_key: str,
    backend: str,
    user: Optional[str] = None,
    success: bool = True,
    detail: Optional[str] = None,
) -> dict:
    """Record an audit event and append it to the log file.

    Args:
        action: One of 'push', 'pull', 'check'.
        env_key: The remote key / path used in the storage backend.
        backend: Backend type, e.g. 's3' or 'gcs'.
        user: Optional username or email to associate with the event.
        success: Whether the operation succeeded.
        detail: Optional extra detail or error message.

    Returns:
        The event dict that was recorded.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "env_key": env_key,
        "backend": backend,
        "user": user or os.environ.get("USER", "unknown"),
        "success": success,
        "detail": detail,
    }

    log_path = _get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")

    return event


def read_events(limit: int = 50) -> list:
    """Read the most recent audit events.

    Args:
        limit: Maximum number of events to return (most recent first).

    Returns:
        List of event dicts.
    """
    log_path = _get_log_path()
    if not log_path.exists():
        return []

    with log_path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()

    events = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return events[-limit:][::-1]
