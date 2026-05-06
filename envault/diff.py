"""Utilities for comparing local and remote .env file contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def _parse_env(content: str) -> Dict[str, str]:
    """Parse .env file content into a key-value dict, ignoring comments/blanks."""
    result: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


@dataclass
class EnvDiff:
    """Represents the diff between a local and remote .env file."""

    added: List[str] = field(default_factory=list)       # keys only in remote
    removed: List[str] = field(default_factory=list)     # keys only in local
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, local_val, remote_val)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key in self.added:
            lines.append(f"  + {key}  (new in remote)")
        for key in self.removed:
            lines.append(f"  - {key}  (not in remote)")
        for key, local_val, remote_val in self.changed:
            lines.append(f"  ~ {key}  local={local_val!r} -> remote={remote_val!r}")
        if not lines:
            return "No differences found."
        return "\n".join(lines)


def compute_diff(local_content: str, remote_content: str) -> EnvDiff:
    """Compute the diff between local and remote .env content strings."""
    local = _parse_env(local_content)
    remote = _parse_env(remote_content)

    all_keys = set(local) | set(remote)
    diff = EnvDiff()

    for key in sorted(all_keys):
        in_local = key in local
        in_remote = key in remote

        if in_remote and not in_local:
            diff.added.append(key)
        elif in_local and not in_remote:
            diff.removed.append(key)
        elif local[key] != remote[key]:
            diff.changed.append((key, local[key], remote[key]))
        else:
            diff.unchanged.append(key)

    return diff
