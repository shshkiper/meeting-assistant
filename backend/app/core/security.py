# Всё что связано с безопасностью: хеширование паролей и JWT-токены

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Контекст для хеширования паролей через bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Хешируем пароль перед сохранением в базу
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    # Проверяем введённый пароль против хеша из базы
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    # Создаём короткоживущий токен для доступа к API
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(
        {"sub": str(subject), "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(subject: Any) -> str:
    # Создаём долгоживущий токен для обновления access-токена
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    # Проверяем подпись токена и возвращаем его содержимое
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Неверный токен: {e}") from e
