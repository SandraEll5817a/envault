"""Tests for the share CLI commands."""

import pytest
from click.testing import CliRunner

from envault.cli_share import share_group
from envault.share import create_token

SECRET = "test-signing-secret"
BUCKET = "my-bucket"
KEY = "team/.env"


@pytest.fixture
def runner():
    return CliRunner()


def test_share_create_outputs_token(runner):
    result = runner.invoke(
        share_group,
        ["create", BUCKET, KEY, "--secret", SECRET],
    )
    assert result.exit_code == 0
    token = result.output.strip()
    assert "." in token
    assert len(token) > 20


def test_share_create_uses_envvar(runner):
    result = runner.invoke(
        share_group,
        ["create", BUCKET, KEY],
        env={"ENVAULT_SHARE_SECRET": SECRET},
    )
    assert result.exit_code == 0
    assert len(result.output.strip()) > 20


def test_share_create_custom_ttl(runner):
    result = runner.invoke(
        share_group,
        ["create", BUCKET, KEY, "--secret", SECRET, "--ttl", "120"],
    )
    assert result.exit_code == 0


def test_share_verify_valid_token(runner):
    token = create_token(BUCKET, KEY, SECRET, ttl=3600)
    result = runner.invoke(
        share_group,
        ["verify", token, "--secret", SECRET],
    )
    assert result.exit_code == 0
    assert BUCKET in result.output
    assert KEY in result.output
    assert "valid" in result.output


def test_share_verify_wrong_secret(runner):
    token = create_token(BUCKET, KEY, SECRET, ttl=3600)
    result = runner.invoke(
        share_group,
        ["verify", token, "--secret", "wrong"],
    )
    assert result.exit_code != 0
    assert "Invalid" in result.output or "Invalid" in (result.output + str(result.exception))


def test_share_verify_expired_token(runner):
    token = create_token(BUCKET, KEY, SECRET, ttl=-1)
    result = runner.invoke(
        share_group,
        ["verify", token, "--secret", SECRET],
    )
    assert result.exit_code != 0


def test_share_verify_garbage_token(runner):
    result = runner.invoke(
        share_group,
        ["verify", "garbage.token.data", "--secret", SECRET],
    )
    assert result.exit_code != 0
