# Эндпоинты для регистрации, входа и обновления токена

from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.models import User
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter()

# Простая защита от перебора паролей — храним время попыток входа в памяти
_login_attempts: dict = defaultdict(list)
MAX_ATTEMPTS = 5       # максимум попыток
WINDOW_SECONDS = 60    # за какой период считаем


def _check_rate_limit(email: str) -> None:
    """Проверяет что пользователь не превысил лимит попыток входа."""
    now = time()
    # Оставляем только попытки за последнюю минуту
    _login_attempts[email] = [t for t in _login_attempts[email] if now - t < WINDOW_SECONDS]
    if len(_login_attempts[email]) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Слишком много попыток входа. Подождите минуту и попробуйте снова."
        )
    _login_attempts[email].append(now)


@router.post("/register", response_model=UserRead, status_code=201)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем что такой email ещё не зарегистрирован
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот email уже зарегистрирован")
    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Проверяем лимит попыток перед тем как лезть в базу
    _check_rate_limit(body.email)

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password or ""):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт отключён")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    # Выдаём новую пару токенов по refresh-токену
    from app.core.security import decode_token
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Передан не refresh-токен")
        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
