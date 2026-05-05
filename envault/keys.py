"""Key management: generate, store, and retrieve named passphrases."""

import json
import os
import stat
from pathlib import Path
from typing import Optional

DEFAULT_KEYSTORE_PATH = Path.home() / ".envault" / "keys.json"


def _get_keystore_path() -> Path:
    path = Path(os.environ.get("ENVAULT_KEYSTORE", DEFAULT_KEYSTORE_PATH))
    return path


def _load_keystore(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_keystore(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    # Restrict permissions to owner only (600)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def set_key(name: str, passphrase: str, keystore_path: Optional[Path] = None) -> None:
    """Store a named passphrase in the keystore."""
    path = keystore_path or _get_keystore_path()
    data = _load_keystore(path)
    data[name] = passphrase
    _save_keystore(path, data)


def get_key(name: str, keystore_path: Optional[Path] = None) -> Optional[str]:
    """Retrieve a named passphrase from the keystore."""
    path = keystore_path or _get_keystore_path()
    data = _load_keystore(path)
    return data.get(name)


def delete_key(name: str, keystore_path: Optional[Path] = None) -> bool:
    """Delete a named passphrase. Returns True if it existed."""
    path = keystore_path or _get_keystore_path()
    data = _load_keystore(path)
    if name in data:
        del data[name]
        _save_keystore(path, data)
        return True
    return False


def list_keys(keystore_path: Optional[Path] = None) -> list:
    """Return all stored key names."""
    path = keystore_path or _get_keystore_path()
    data = _load_keystore(path)
    return list(data.keys())
