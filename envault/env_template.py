"""Template validation: compare a .env file against a .env.template file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _parse_keys(text: str) -> set[str]:
    """Return the set of variable names defined in *text*."""
    keys: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, *_ = stripped.split("=", 1)
            keys.add(key.strip())
    return keys


@dataclass
class TemplateResult:
    missing: list[str] = field(default_factory=list)   # in template, not in env
    extra: list[str] = field(default_factory=list)     # in env, not in template

    @property
    def ok(self) -> bool:
        return not self.missing and not self.extra

    def summary(self) -> str:
        lines: list[str] = []
        if self.missing:
            lines.append("Missing keys (required by template):")
            lines.extend(f"  - {k}" for k in sorted(self.missing))
        if self.extra:
            lines.append("Extra keys (not in template):")
            lines.extend(f"  + {k}" for k in sorted(self.extra))
        if not lines:
            return "All keys match the template."
        return "\n".join(lines)


def validate(
    env_text: str,
    template_text: str,
    strict: bool = False,
) -> TemplateResult:
    """Validate *env_text* against *template_text*.

    Parameters
    ----------
    env_text:
        Contents of the .env file.
    template_text:
        Contents of the .env.template file.
    strict:
        When *True*, extra keys (present in env but absent from template)
        are also treated as a validation problem.
    """
    env_keys = _parse_keys(env_text)
    template_keys = _parse_keys(template_text)

    missing = list(template_keys - env_keys)
    extra = list(env_keys - template_keys) if strict else []
    return TemplateResult(missing=missing, extra=extra)


def validate_files(
    env_path: Path,
    template_path: Optional[Path] = None,
    strict: bool = False,
) -> TemplateResult:
    """Convenience wrapper that reads files from disk."""
    if template_path is None:
        template_path = env_path.parent / (env_path.name + ".template")
    env_text = env_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")
    return validate(env_text, template_text, strict=strict)
