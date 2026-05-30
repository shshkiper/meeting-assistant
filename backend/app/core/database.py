# Подключение к базе данных через SQLAlchemy (асинхронное)

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

from app.core.config import settings

# Создаём движок подключения к Postgres
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # проверяет соединение перед каждым запросом
    pool_size=10,
    max_overflow=20,
)

# Фабрика сессий — используется везде где нужна база
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    # Создаём таблицы при старте если их нет.
    # Если Postgres недоступен — просто логируем, не падаем.
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.warning(f"Не удалось подключиться к базе при старте: {e}. Таблицы будут созданы позже.")


async def get_db() -> AsyncSession:
    # Зависимость FastAPI — отдаёт сессию и закрывает её после запроса
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
