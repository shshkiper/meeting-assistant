"""MinIO object storage service."""

import os
from io import BytesIO
from typing import Optional

from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageService:
    def __init__(self):
        self._client: Optional[Minio] = None

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            self._ensure_buckets()
        return self._client

    def _ensure_buckets(self):
        for bucket in [settings.MINIO_BUCKET_AUDIO, settings.MINIO_BUCKET_DOCS]:
            try:
                if not self._client.bucket_exists(bucket):
                    self._client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
            except S3Error as e:
                logger.error(f"MinIO bucket error: {e}")

    async def upload_file(
        self,
        bucket: str,
        object_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to MinIO. Returns object key."""
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info(f"Uploaded {object_key} to {bucket} ({len(data)} bytes)")
        return object_key

    async def upload_file_path(
        self, bucket: str, object_key: str, file_path: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file from disk path."""
        self.client.fput_object(bucket, object_key, file_path, content_type=content_type)
        return object_key

    async def download_file(self, bucket: str, object_key: str, dest_path: str) -> None:
        """Download file from MinIO to disk."""
        self.client.fget_object(bucket, object_key, dest_path)
        logger.info(f"Downloaded {object_key} to {dest_path}")

    async def get_presigned_url(self, bucket: str, object_key: str, expires_hours: int = 1) -> str:
        """Generate temporary download URL."""
        from datetime import timedelta
        url = self.client.presigned_get_object(
            bucket, object_key, expires=timedelta(hours=expires_hours)
        )
        return url

    async def delete_file(self, bucket: str, object_key: str) -> None:
        self.client.remove_object(bucket, object_key)


storage_service = StorageService()
