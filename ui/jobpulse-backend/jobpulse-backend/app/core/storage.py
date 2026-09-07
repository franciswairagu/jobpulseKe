"""
Storage abstraction for uploaded CVs.

Only the extracted text/analysis is meant to live long-term (see
app/services/cv_service.py) - raw CV bytes are written here just long
enough for parsing, per the "don't persist raw CV content" principle
noted in the notebook. Swap STORAGE_PROVIDER=s3 to write to S3 instead
of local disk without changing any calling code.
"""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_bytes: bytes, filename: str) -> str:
        """Persist bytes, return a storage key/path."""

    @abstractmethod
    def read_path(self, storage_key: str) -> str:
        """Return a local filesystem path usable for parsing."""

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, filename: str) -> str:
        suffix = Path(filename).suffix
        return f"{uuid.uuid4().hex}{suffix}"

    def save(self, file_bytes: bytes, filename: str) -> str:
        key = self._safe_name(filename)
        target = self.base_dir / key
        target.write_bytes(file_bytes)
        return str(target)

    def read_path(self, storage_key: str) -> str:
        return storage_key

    def delete(self, storage_key: str) -> None:
        path = Path(storage_key)
        if path.exists():
            path.unlink()


class S3StorageBackend(StorageBackend):
    """S3-compatible backend. Requires boto3 and STORAGE_BUCKET to be set."""

    def __init__(self, bucket: str):
        import boto3  # imported lazily so local dev doesn't need boto3

        self.bucket = bucket
        self.client = boto3.client("s3")
        self._tmp_dir = Path("/tmp/jobpulse_cv_cache")
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_bytes: bytes, filename: str) -> str:
        key = f"cvs/{uuid.uuid4().hex}{Path(filename).suffix}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=file_bytes)
        return key

    def read_path(self, storage_key: str) -> str:
        local_path = self._tmp_dir / Path(storage_key).name
        self.client.download_file(self.bucket, storage_key, str(local_path))
        return str(local_path)

    def delete(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_PROVIDER == "s3":
        if not settings.STORAGE_BUCKET:
            raise RuntimeError("STORAGE_BUCKET must be set when STORAGE_PROVIDER=s3")
        return S3StorageBackend(settings.STORAGE_BUCKET)
    return LocalStorageBackend(settings.LOCAL_STORAGE_DIR)
