"""Generate human-readable diff reports between two .env file versions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envault.diff import EnvDiff, compute_diff


@dataclass
class DiffReport:
    diff: EnvDiff
    env_name: str = "default"
    old_label: str = "remote"
    new_label: str = "local"
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def render(self, show_values: bool = False) -> str:
        lines = [f"Diff report for '{self.env_name}' ({self.old_label} → {self.new_label})"]
        lines.append("-" * 60)

        if not self.has_changes:
            lines.append("  No changes detected.")
            return "\n".join(lines)

        for key in sorted(self.added):
            val = f" = {self.diff.local.get(key, '')}" if show_values else ""
            lines.append(f"  + {key}{val}")

        for key in sorted(self.removed):
            val = f" = {self.diff.remote.get(key, '')}" if show_values else ""
            lines.append(f"  - {key}{val}")

        for key in sorted(self.changed):
            if show_values:
                old = self.diff.remote.get(key, "")
                new = self.diff.local.get(key, "")
                lines.append(f"  ~ {key}: {old!r} → {new!r}")
            else:
                lines.append(f"  ~ {key}")

        lines.append("-" * 60)
        lines.append(
            f"  {len(self.added)} added, {len(self.removed)} removed, {len(self.changed)} changed"
        )
        return "\n".join(lines)


def build_report(
    old_content: str,
    new_content: str,
    env_name: str = "default",
    old_label: str = "remote",
    new_label: str = "local",
) -> DiffReport:
    """Compute a DiffReport between two raw .env strings."""
    diff = compute_diff(old_content, new_content)
    return DiffReport(
        diff=diff,
        env_name=env_name,
        old_label=old_label,
        new_label=new_label,
        added=list(diff.added),
        removed=list(diff.removed),
        changed=list(diff.changed),
    )
