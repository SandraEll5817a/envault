"""Lint .env files for common issues: duplicate keys, suspicious values, missing quotes, etc."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LintIssue:
    line_number: int
    key: Optional[str]
    code: str
    message: str
    severity: str  # "error" | "warning"

    def __str__(self) -> str:
        loc = f"line {self.line_number}"
        key_part = f" [{self.key}]" if self.key else ""
        return f"{self.severity.upper()} {self.code}{key_part} @ {loc}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def summary(self) -> str:
        if not self.issues:
            return "No issues found."
        return (
            f"{self.error_count} error(s), {self.warning_count} warning(s) found."
        )


def lint(content: str) -> LintResult:
    """Lint the given .env file content and return a LintResult."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(content.splitlines(), start=1):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(LintIssue(
                line_number=lineno, key=None,
                code="E001", severity="error",
                message="Line is not a comment, blank, or valid KEY=VALUE assignment.",
            ))
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if not key:
            result.issues.append(LintIssue(
                line_number=lineno, key=None,
                code="E002", severity="error",
                message="Empty key before '='.",
            ))
            continue

        if " " in key:
            result.issues.append(LintIssue(
                line_number=lineno, key=key,
                code="E003", severity="error",
                message="Key contains whitespace.",
            ))

        if key in seen_keys:
            result.issues.append(LintIssue(
                line_number=lineno, key=key,
                code="W001", severity="warning",
                message=f"Duplicate key (first seen on line {seen_keys[key]}).",
            ))
        else:
            seen_keys[key] = lineno

        if value and value[0] in ("'", '"') and value[-1] != value[0]:
            result.issues.append(LintIssue(
                line_number=lineno, key=key,
                code="W002", severity="warning",
                message="Value appears to have an unmatched quote.",
            ))

        if not value:
            result.issues.append(LintIssue(
                line_number=lineno, key=key,
                code="W003", severity="warning",
                message="Key has an empty value.",
            ))

        lower_key = key.lower()
        if any(s in lower_key for s in ("password", "secret", "token", "api_key")):
            stripped = value.strip("'\"")
            if stripped in ("changeme", "TODO", "todo", "example", "placeholder", ""):
                result.issues.append(LintIssue(
                    line_number=lineno, key=key,
                    code="W004", severity="warning",
                    message="Sensitive key appears to have a placeholder value.",
                ))

    return result
