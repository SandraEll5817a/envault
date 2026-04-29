"""Storage backends for envault: S3 and GCS support."""

import os
from abc import ABC, abstractmethod
from typing import Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(self, key: str, data: bytes) -> None:
        """Upload encrypted data to the backend."""
        ...

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download encrypted data from the backend."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the backend."""
        ...


class S3Backend(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(self, bucket: str, prefix: str = "envault/"):
        try:
            import boto3
        except ImportError as e:
            raise ImportError("boto3 is required for S3 backend: pip install boto3") from e

        self.bucket = bucket
        self.prefix = prefix
        self._client = boto3.client("s3")

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def upload(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self.bucket, Key=self._full_key(key), Body=data)

    def download(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=self._full_key(key))
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self._client.head_object(Bucket=self.bucket, Key=self._full_key(key))
            return True
        except ClientError:
            return False


class GCSBackend(StorageBackend):
    """Google Cloud Storage backend."""

    def __init__(self, bucket: str, prefix: str = "envault/"):
        try:
            from google.cloud import storage as gcs
        except ImportError as e:
            raise ImportError(
                "google-cloud-storage is required for GCS backend: "
                "pip install google-cloud-storage"
            ) from e

        self.bucket_name = bucket
        self.prefix = prefix
        self._client = gcs.Client()
        self._bucket = self._client.bucket(bucket)

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def upload(self, key: str, data: bytes) -> None:
        blob = self._bucket.blob(self._full_key(key))
        blob.upload_from_string(data, content_type="application/octet-stream")

    def download(self, key: str) -> bytes:
        blob = self._bucket.blob(self._full_key(key))
        return blob.download_as_bytes()

    def exists(self, key: str) -> bool:
        blob = self._bucket.blob(self._full_key(key))
        return blob.exists()
