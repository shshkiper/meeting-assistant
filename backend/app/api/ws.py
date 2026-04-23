"""
WebSocket endpoint for real-time meeting processing progress.
Subscribes to Redis pub/sub channel and forwards messages to client.
"""

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
    logger.info(f"WS connected for meeting {meeting_id}")

    redis = aioredis.from_url(settings.REDIS_URL)
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
                # Ping to keep connection alive
                await websocket.send_text(json.dumps({"ping": True}))
                await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info(f"WS disconnected for meeting {meeting_id}")
    except Exception as e:
        logger.error(f"WS error: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await redis.aclose()
