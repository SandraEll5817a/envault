"""Tests for the envault CLI commands."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from envault.cli import cli


ENV_CONTENT = b"API_KEY=secret\nDB_URL=postgres://localhost/db\n"
PASSPHRASE = "test-passphrase-123"
BUCKET = "my-test-bucket"
REMOTE_PATH = "envault/.env.enc"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_bytes(ENV_CONTENT)
    return str(p)


@patch("envault.cli.S3Backend")
def test_push_success(mock_s3_cls, runner, env_file):
    mock_backend = MagicMock()
    mock_s3_cls.return_value = mock_backend

    result = runner.invoke(cli, [
        "push", env_file,
        "--key", PASSPHRASE,
        "--bucket", BUCKET,
        "--remote-path", REMOTE_PATH,
    ])

    assert result.exit_code == 0
    assert "Pushed" in result.output
    mock_backend.upload.assert_called_once()
    upload_args = mock_backend.upload.call_args[0]
    assert upload_args[0] == REMOTE_PATH
    assert isinstance(upload_args[1], bytes)


@patch("envault.cli.S3Backend")
def test_pull_success(mock_s3_cls, runner, tmp_path):
    from envault.crypto import encrypt
    ciphertext = encrypt(ENV_CONTENT, PASSPHRASE)

    mock_backend = MagicMock()
    mock_backend.exists.return_value = True
    mock_backend.download.return_value = ciphertext
    mock_s3_cls.return_value = mock_backend

    out_file = str(tmp_path / ".env.pulled")
    result = runner.invoke(cli, [
        "pull", out_file,
        "--key", PASSPHRASE,
        "--bucket", BUCKET,
        "--remote-path", REMOTE_PATH,
    ])

    assert result.exit_code == 0
    assert "Pulled" in result.output
    from pathlib import Path
    assert Path(out_file).read_bytes() == ENV_CONTENT


@patch("envault.cli.S3Backend")
def test_pull_file_not_found(mock_s3_cls, runner, tmp_path):
    mock_backend = MagicMock()
    mock_backend.exists.return_value = False
    mock_s3_cls.return_value = mock_backend

    out_file = str(tmp_path / ".env")
    result = runner.invoke(cli, [
        "pull", out_file,
        "--key", PASSPHRASE,
        "--bucket", BUCKET,
    ])

    assert result.exit_code == 1
    assert "not found" in result.output


@patch("envault.cli.S3Backend")
def test_check_exists(mock_s3_cls, runner):
    mock_backend = MagicMock()
    mock_backend.exists.return_value = True
    mock_s3_cls.return_value = mock_backend

    result = runner.invoke(cli, ["check", "--bucket", BUCKET])
    assert result.exit_code == 0
    assert "Found" in result.output


@patch("envault.cli.S3Backend")
def test_check_not_exists(mock_s3_cls, runner):
    mock_backend = MagicMock()
    mock_backend.exists.return_value = False
    mock_s3_cls.return_value = mock_backend

    result = runner.invoke(cli, ["check", "--bucket", BUCKET])
    assert result.exit_code == 1
    assert "Not found" in result.output


def test_push_missing_key(runner, env_file):
    result = runner.invoke(cli, ["push", env_file, "--bucket", BUCKET])
    assert result.exit_code != 0
