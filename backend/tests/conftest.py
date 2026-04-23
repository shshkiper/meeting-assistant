import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pytest

from app.core.database import get_db
from app.main import app


@dataclass
class _FakeResult:
    value: Any

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        if self.value is None:
            return []
        if isinstance(self.value, list):
            return self.value
        return [self.value]


class FakeAsyncSession:
    """
    Минимальная "памятная" замена для SQLAlchemy AsyncSession.

    Нужна, чтобы тесты можно было гонять без поднятого Postgres/Redis/MinIO и прочей
    инфраструктуры. Реализованы только те методы, которые реально используются в
    текущих API-тестах (в основном сценарии аутентификации).
    """

    def __init__(self):
        self._users_by_email: Dict[str, Any] = {}
        self._users_by_id: Dict[str, Any] = {}

    async def execute(self, statement):  # pragma: no cover
        # Тут не лезем глубоко в SQLAlchemy — для тестов хватает параметров,
        # которые попадают в compiled statement при простых SELECT ... WHERE.
        params = getattr(getattr(statement, "compile", lambda: None)(), "params", {}) or {}

        # Поиск пользователя по email (регистрация/логин)
        email = params.get("email_1") or params.get("email")
        if email is not None:
            return _FakeResult(self._users_by_email.get(email))

        # Поиск по user_id (refresh)
        user_id = params.get("id_1") or params.get("id")
        if user_id is not None:
            return _FakeResult(self._users_by_id.get(str(user_id)))

        return _FakeResult(None)

    def add(self, obj: Any) -> None:
        # Храним только минимум полей, который нужен тестам и генерации токенов
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "is_active", None) is None:
            obj.is_active = True
        if getattr(obj, "role", None) is None:
            obj.role = "user"
        self._users_by_email[getattr(obj, "email", "")] = obj
        self._users_by_id[str(getattr(obj, "id"))] = obj

    async def commit(self) -> None:
        return None

    async def refresh(self, obj: Any) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        return None


@pytest.fixture
def fake_db_session() -> FakeAsyncSession:
    return FakeAsyncSession()


@pytest.fixture(autouse=True)
def _override_get_db(fake_db_session: FakeAsyncSession):
    async def _fake_get_db():
        yield fake_db_session

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)

