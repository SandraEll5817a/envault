"""Lock mechanism to prevent concurrent envault operations on the same environment."""

import os
import json
import time
from pathlib import Path
from typing import Optional


def _get_lock_dir() -> Path:
    base = Path(os.environ.get("ENVAULT_HOME", Path.home() / ".envault"))
    lock_dir = base / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir


def _lock_path(env_name: str) -> Path:
    safe_name = env_name.replace("/", "_").replace("\\", "_")
    return _get_lock_dir() / f"{safe_name}.lock"


def acquire_lock(env_name: str, timeout: int = 30) -> bool:
    """Attempt to acquire a lock for the given environment name.

    Returns True if the lock was acquired, False if it timed out.
    """
    path = _lock_path(env_name)
    deadline = time.time() + timeout

    while time.time() < deadline:
        if not path.exists():
            payload = {"pid": os.getpid(), "acquired_at": time.time()}
            try:
                path.write_text(json.dumps(payload))
                return True
            except OSError:
                pass
        else:
            info = read_lock(env_name)
            if info and not _pid_alive(info["pid"]):
                path.unlink(missing_ok=True)
                continue
        time.sleep(0.2)

    return False


def release_lock(env_name: str) -> bool:
    """Release the lock for the given environment. Returns True if released."""
    path = _lock_path(env_name)
    if path.exists():
        path.unlink(missing_ok=True)
        return True
    return False


def read_lock(env_name: str) -> Optional[dict]:
    """Return lock metadata if a lock exists, otherwise None."""
    path = _lock_path(env_name)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def is_locked(env_name: str) -> bool:
    """Return True if a live lock exists for the given environment."""
    info = read_lock(env_name)
    if info is None:
        return False
    return _pid_alive(info["pid"])


def _pid_alive(pid: int) -> bool:
    """Check whether a process with the given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
