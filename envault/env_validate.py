"""Value-level validation for .env files (type hints, regex patterns, allowed values)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Schema entry: each key maps to a dict of optional constraints
# e.g. {"PORT": {"type": "int", "required": True}, "ENV": {"allowed": ["dev", "prod"]}}
Schema = Dict[str, Dict]


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

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
        if self.ok and not self.issues:
            return "All values valid."
        parts = []
        if self.error_count:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning(s)")
        return ", ".join(parts) + "."


def _parse_env(content: str) -> Dict[str, str]:
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


def validate_schema(content: str, schema: Schema) -> ValidationResult:
    """Validate env content against a schema of constraints."""
    result = ValidationResult()
    env = _parse_env(content)

    for key, rules in schema.items():
        required = rules.get("required", False)
        value: Optional[str] = env.get(key)

        if value is None:
            if required:
                result.issues.append(ValidationIssue(key, "required key is missing", "error"))
            continue

        # Type check
        expected_type = rules.get("type")
        if expected_type == "int":
            try:
                int(value)
            except ValueError:
                result.issues.append(ValidationIssue(key, f"expected integer, got {value!r}", "error"))
        elif expected_type == "bool":
            if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                result.issues.append(ValidationIssue(key, f"expected boolean, got {value!r}", "error"))
        elif expected_type == "url":
            if not re.match(r"^https?://", value):
                result.issues.append(ValidationIssue(key, f"expected URL starting with http(s)://, got {value!r}", "error"))

        # Pattern check
        pattern = rules.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            result.issues.append(ValidationIssue(key, f"value {value!r} does not match pattern {pattern!r}", "error"))

        # Allowed values
        allowed = rules.get("allowed")
        if allowed and value not in allowed:
            result.issues.append(ValidationIssue(key, f"value {value!r} not in allowed set {allowed}", "error"))

        # Warn on empty
        if value == "" and rules.get("warn_empty", False):
            result.issues.append(ValidationIssue(key, "value is empty", "warning"))

    return result
