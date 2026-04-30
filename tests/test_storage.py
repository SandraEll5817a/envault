"""Tests for storage backends using mocks."""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# S3Backend tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def s3_backend():
    with patch("boto3.client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        from envault.storage import S3Backend
        backend = S3Backend(bucket="test-bucket", prefix="envault/")
        backend._client = mock_client
        yield backend, mock_client


def test_s3_upload(s3_backend):
    backend, client = s3_backend
    backend.upload("prod.env", b"encrypted-data")
    client.put_object.assert_called_once_with(
        Bucket="test-bucket", Key="envault/prod.env", Body=b"encrypted-data"
    )


def test_s3_download(s3_backend):
    backend, client = s3_backend
    client.get_object.return_value = {"Body": MagicMock(read=lambda: b"secret-bytes")}
    result = backend.download("prod.env")
    assert result == b"secret-bytes"
    client.get_object.assert_called_once_with(Bucket="test-bucket", Key="envault/prod.env")


def test_s3_exists_true(s3_backend):
    backend, client = s3_backend
    client.head_object.return_value = {}
    assert backend.exists("prod.env") is True


def test_s3_exists_false(s3_backend):
    from botocore.exceptions import ClientError
    backend, client = s3_backend
    client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")
    assert backend.exists("missing.env") is False


def test_s3_prefix_applied(s3_backend):
    backend, client = s3_backend
    assert backend._full_key("staging.env") == "envault/staging.env"


def test_s3_prefix_empty(s3_backend):
    """Ensure _full_key works correctly when no prefix is set."""
    from envault.storage import S3Backend
    with patch("boto3.client"):
        backend = S3Backend(bucket="test-bucket", prefix="")
        assert backend._full_key("prod.env") == "prod.env"


# ---------------------------------------------------------------------------
# GCSBackend tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def gcs_backend():
    gcs_module = MagicMock()
    mock_bucket = MagicMock()
    gcs_module.Client.return_value.bucket.return_value = mock_bucket

    with patch.dict("sys.modules", {"google.cloud": MagicMock(), "google.cloud.storage": gcs_module}):
        from importlib import reload
        import envault.storage as storage_mod
        reload(storage_mod)
        backend = storage_mod.GCSBackend(bucket="test-bucket", prefix="envault/")
        backend._bucket = mock_bucket
        yield backend, mock_bucket


def test_gcs_upload(gcs_backend):
    backend, bucket = gcs_backend
    mock_blob = MagicMock()
    bucket.blob.return_value = mock_blob
    backend.upload("prod.env", b"gcs-data")
    mock_blob.upload_from_string.assert_called_once_with(b"gcs-data", content_type="application/octet-stream")


def test_gcs_download(gcs_backend):
    backend, bucket = gcs_backend
    mock_blob = MagicMock()
    mock_blob.download_as_bytes.return_value = b"gcs-secret"
    bucket.blob.return_value = mock_blob
