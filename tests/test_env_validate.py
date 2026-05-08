"""Tests for envault.env_validate."""

import pytest
from envault.env_validate import validate_schema, ValidationResult, ValidationIssue


SIMPLE_ENV = """
PORT=8080
DEBUG=true
APP_ENV=production
DATABASE_URL=https://db.example.com/mydb
SECRET_KEY=abc123
"""


def test_validate_no_schema_issues():
    schema = {
        "PORT": {"type": "int", "required": True},
        "DEBUG": {"type": "bool"},
        "APP_ENV": {"allowed": ["development", "staging", "production"]},
    }
    result = validate_schema(SIMPLE_ENV, schema)
    assert result.ok
    assert result.error_count == 0


def test_validate_missing_required_key():
    schema = {"MISSING_KEY": {"required": True}}
    result = validate_schema(SIMPLE_ENV, schema)
    assert not result.ok
    assert result.error_count == 1
    assert any(i.key == "MISSING_KEY" for i in result.issues)


def test_validate_optional_missing_key_no_error():
    schema = {"OPTIONAL_KEY": {"required": False, "type": "int"}}
    result = validate_schema(SIMPLE_ENV, schema)
    assert result.ok


def test_validate_int_type_valid():
    result = validate_schema(SIMPLE_ENV, {"PORT": {"type": "int"}})
    assert result.ok


def test_validate_int_type_invalid():
    env = "PORT=not_a_number\n"
    result = validate_schema(env, {"PORT": {"type": "int"}})
    assert not result.ok
    assert result.error_count == 1


def test_validate_bool_type_valid():
    for val in ("true", "false", "1", "0", "yes", "no"):
        result = validate_schema(f"FLAG={val}\n", {"FLAG": {"type": "bool"}})
        assert result.ok, f"Expected {val!r} to be valid bool"


def test_validate_bool_type_invalid():
    result = validate_schema("FLAG=maybe\n", {"FLAG": {"type": "bool"}})
    assert not result.ok


def test_validate_url_type_valid():
    result = validate_schema(SIMPLE_ENV, {"DATABASE_URL": {"type": "url"}})
    assert result.ok


def test_validate_url_type_invalid():
    result = validate_schema("DATABASE_URL=ftp://bad\n", {"DATABASE_URL": {"type": "url"}})
    assert not result.ok


def test_validate_pattern_match():
    result = validate_schema("SECRET_KEY=abc123\n", {"SECRET_KEY": {"pattern": r"[a-z0-9]+"}})
    assert result.ok


def test_validate_pattern_no_match():
    result = validate_schema("SECRET_KEY=ABC!!!\n", {"SECRET_KEY": {"pattern": r"[a-z0-9]+"}})
    assert not result.ok


def test_validate_allowed_values_valid():
    result = validate_schema("APP_ENV=staging\n", {"APP_ENV": {"allowed": ["development", "staging", "production"]}})
    assert result.ok


def test_validate_allowed_values_invalid():
    result = validate_schema("APP_ENV=local\n", {"APP_ENV": {"allowed": ["development", "staging", "production"]}})
    assert not result.ok
    assert "not in allowed set" in result.issues[0].message


def test_validate_warn_empty_is_warning_not_error():
    result = validate_schema("API_KEY=\n", {"API_KEY": {"warn_empty": True}})
    assert result.ok  # warnings don't fail
    assert result.warning_count == 1
    assert result.error_count == 0


def test_summary_all_valid():
    result = validate_schema("PORT=3000\n", {"PORT": {"type": "int"}})
    assert result.summary() == "All values valid."


def test_summary_with_errors():
    result = validate_schema("PORT=bad\n", {"PORT": {"type": "int", "required": True}})
    assert "error" in result.summary()


def test_validation_issue_str():
    issue = ValidationIssue(key="FOO", message="bad value", severity="error")
    assert str(issue) == "[ERROR] FOO: bad value"


def test_validation_issue_warning_str():
    issue = ValidationIssue(key="BAR", message="empty", severity="warning")
    assert str(issue) == "[WARNING] BAR: empty"
