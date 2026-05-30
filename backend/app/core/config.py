# Все настройки приложения берутся из .env файла

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Основное
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"
    DEBUG: bool = False

    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://meetinguser:meetingpass@localhost:5432/meetingdb"

    # Redis и Celery (очередь задач)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MinIO (хранилище файлов)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_AUDIO: str = "meeting-audio"
    MINIO_BUCKET_DOCS: str = "meeting-docs"
    MINIO_SECURE: bool = False

    # Whisper (модель транскрибации)
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_LANGUAGE: str = "ru"

    # LLM (языковая модель для протоколов)
    LLM_PROVIDER: str = "ollama"
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    LLM_API_KEY: Optional[str] = None

    # CORS — откуда разрешены запросы на API
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        # Поддерживаем строку через запятую и список
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    # JWT-токены
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LDAP (корпоративная авторизация, опционально)
    LDAP_ENABLED: bool = False
    LDAP_SERVER: str = ""
    LDAP_BASE_DN: str = ""
    LDAP_BIND_DN: str = ""
    LDAP_BIND_PASSWORD: str = ""

    # Jira (интеграция для задач, опционально)
    JIRA_ENABLED: bool = False
    JIRA_URL: str = ""
    JIRA_TOKEN: str = ""
    JIRA_PROJECT_KEY: str = "MTG"

    # Логирование
    LOG_LEVEL: str = "INFO"


settings = Settings()
