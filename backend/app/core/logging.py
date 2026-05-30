# Настройка логирования через loguru — вывод в консоль и в файл

import sys
from loguru import logger
from app.core.config import settings


def setup_logging() -> None:
    logger.remove()
    # Красивый вывод в консоль
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    # Запись в файл — ротация по 100 МБ, хранить 30 дней
    logger.add(
        "logs/meeting_assistant.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO",
        serialize=True,
    )
