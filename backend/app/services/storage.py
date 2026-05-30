# Сервис для работы с MinIO — загрузка, скачивание и удаление файлов

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
        # Создаём клиент при первом обращении (ленивая инициализация)
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
        # Создаём бакеты если их ещё нет
        for bucket in [settings.MINIO_BUCKET_AUDIO, settings.MINIO_BUCKET_DOCS]:
            try:
                if not self._client.bucket_exists(bucket):
                    self._client.make_bucket(bucket)
                    logger.info(f"Создан бакет MinIO: {bucket}")
            except S3Error as e:
                logger.error(f"Ошибка бакета MinIO: {e}")

    async def upload_file(
        self,
        bucket: str,
        object_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        # Загружаем байты в MinIO
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info(f"Загружен файл {object_key} в {bucket} ({len(data)} байт)")
        return object_key

    async def upload_file_path(
        self, bucket: str, object_key: str, file_path: str, content_type: str = "application/octet-stream"
    ) -> str:
        # Загружаем файл с диска в MinIO
        self.client.fput_object(bucket, object_key, file_path, content_type=content_type)
        return object_key

    async def download_file(self, bucket: str, object_key: str, dest_path: str) -> None:
        # Скачиваем файл из MinIO на диск
        self.client.fget_object(bucket, object_key, dest_path)
        logger.info(f"Скачан файл {object_key} в {dest_path}")

    async def get_presigned_url(self, bucket: str, object_key: str, expires_hours: int = 1) -> str:
        # Генерируем временную ссылку для скачивания файла
        from datetime import timedelta
        url = self.client.presigned_get_object(
            bucket, object_key, expires=timedelta(hours=expires_hours)
        )
        return url

    async def delete_file(self, bucket: str, object_key: str) -> None:
        self.client.remove_object(bucket, object_key)


storage_service = StorageService()
