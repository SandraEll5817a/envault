"""Integration tests for the rotate CLI commands."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.cli_rotate import rotate_group
from envault.rotate import RotationResult


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_backend():
    backend = MagicMock()
    return backend


def test_rotate_one_success(runner):
    result_obj = RotationResult(key="prod/.env", success=True)

    with patch("envault.cli_rotate.get_backend") as mock_get_backend, \
         patch("envault.cli_rotate.rotate_key", return_value=result_obj):
        mock_get_backend.return_value = _mock_backend()
        result = runner.invoke(
            rotate_group,
            ["one", "prod/.env",
             "--old-pass", "old",
             "--new-pass", "new",
             "--bucket", "my-bucket"],
        )

    assert result.exit_code == 0
    assert "Rotated" in result.output


def test_rotate_one_failure(runner):
    result_obj = RotationResult(key="prod/.env", success=False, error="bad decrypt")

    with patch("envault.cli_rotate.get_backend") as mock_get_backend, \
         patch("envault.cli_rotate.rotate_key", return_value=result_obj):
        mock_get_backend.return_value = _mock_backend()
        result = runner.invoke(
            rotate_group,
            ["one", "prod/.env",
             "--old-pass", "old",
             "--new-pass", "new",
             "--bucket", "my-bucket"],
        )

    assert result.exit_code != 0


def test_rotate_all_all_success(runner):
    results = [
        RotationResult(key="a/.env", success=True),
        RotationResult(key="b/.env", success=True),
    ]

    with patch("envault.cli_rotate.get_backend") as mock_get_backend, \
         patch("envault.cli_rotate.rotate_all", return_value=results):
        mock_get_backend.return_value = _mock_backend()
        result = runner.invoke(
            rotate_group,
            ["all", "a/.env", "b/.env",
             "--old-pass", "old",
             "--new-pass", "new",
             "--bucket", "my-bucket"],
        )

    assert result.exit_code == 0
    assert "a/.env: OK" in result.output
    assert "b/.env: OK" in result.output


def test_rotate_all_partial_failure(runner):
    results = [
        RotationResult(key="a/.env", success=True),
        RotationResult(key="b/.env", success=False, error="decrypt error"),
    ]

    with patch("envault.cli_rotate.get_backend") as mock_get_backend, \
         patch("envault.cli_rotate.rotate_all", return_value=results):
        mock_get_backend.return_value = _mock_backend()
        result = runner.invoke(
            rotate_group,
            ["all", "a/.env", "b/.env",
             "--old-pass", "old",
             "--new-pass", "new",
             "--bucket", "my-bucket"],
        )

    assert result.exit_code != 0
    assert "FAIL" in result.output
