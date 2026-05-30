# WebSocket-эндпоинт для отправки прогресса обработки совещания в реальном времени.
# Подписывается на канал Redis и пересылает обновления клиенту.

import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.config import settings

router = APIRouter()


@router.websocket("/meetings/{meeting_id}/progress")
async def meeting_progress_ws(websocket: WebSocket, meeting_id: str):
    await websocket.accept()
    logger.info(f"WebSocket подключён для совещания {meeting_id}")

    # Если Redis недоступен — сразу сообщаем клиенту и закрываем соединение
    try:
        redis = aioredis.from_url(settings.REDIS_URL)
        await redis.ping()
    except Exception as e:
        logger.warning(f"Redis недоступен, WebSocket не может работать: {e}")
        await websocket.send_text(json.dumps({"error": "Сервер прогресса временно недоступен"}))
        await websocket.close()
        return

    pubsub = redis.pubsub()
    channel = f"meeting:{meeting_id}:progress"

    try:
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                await websocket.send_text(data)
            else:
                # Пингуем чтобы соединение не закрылось по таймауту
                await websocket.send_text(json.dumps({"ping": True}))
                await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info(f"WebSocket отключён для совещания {meeting_id}")
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await redis.aclose()
