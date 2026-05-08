"""Merge two .env files with conflict detection and resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ConflictStrategy(str, Enum):
    OURS = "ours"       # Keep local value on conflict
    THEIRS = "theirs"   # Use remote value on conflict
    ERROR = "error"     # Raise on any conflict


@dataclass
class MergeConflict:
    key: str
    local_value: str
    remote_value: str

    def __str__(self) -> str:
        return (
            f"  {self.key}:\n"
            f"    local:  {self.local_value}\n"
            f"    remote: {self.remote_value}"
        )


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)
    added_from_remote: List[str] = field(default_factory=list)
    added_from_local: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines = []
        if self.added_from_remote:
            lines.append(f"Added from remote ({len(self.added_from_remote)}): {', '.join(self.added_from_remote)}")
        if self.added_from_local:
            lines.append(f"Added from local ({len(self.added_from_local)}): {', '.join(self.added_from_local)}")
        if self.conflicts:
            lines.append(f"Conflicts ({len(self.conflicts)}):")
            for c in self.conflicts:
                lines.append(str(c))
        if not lines:
            lines.append("No changes or conflicts.")
        return "\n".join(lines)


def _parse_env(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _render_env(data: Dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(data.items())) + "\n"


def merge_env(
    local: str,
    remote: str,
    strategy: ConflictStrategy = ConflictStrategy.ERROR,
) -> Tuple[MergeResult, str]:
    """Merge two env strings. Returns (MergeResult, rendered merged string)."""
    local_map = _parse_env(local)
    remote_map = _parse_env(remote)

    merged: Dict[str, str] = {}
    conflicts: List[MergeConflict] = []
    added_from_remote: List[str] = []
    added_from_local: List[str] = []

    all_keys = set(local_map) | set(remote_map)

    for key in all_keys:
        in_local = key in local_map
        in_remote = key in remote_map

        if in_local and not in_remote:
            merged[key] = local_map[key]
            added_from_local.append(key)
        elif in_remote and not in_local:
            merged[key] = remote_map[key]
            added_from_remote.append(key)
        elif local_map[key] == remote_map[key]:
            merged[key] = local_map[key]
        else:
            conflict = MergeConflict(key, local_map[key], remote_map[key])
            conflicts.append(conflict)
            if strategy == ConflictStrategy.ERROR:
                raise ValueError(f"Merge conflict on key '{key}': local={local_map[key]!r}, remote={remote_map[key]!r}")
            elif strategy == ConflictStrategy.OURS:
                merged[key] = local_map[key]
            else:
                merged[key] = remote_map[key]

    result = MergeResult(
        merged=merged,
        conflicts=conflicts,
        added_from_remote=added_from_remote,
        added_from_local=added_from_local,
    )
    return result, _render_env(merged)
