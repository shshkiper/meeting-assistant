"""
MeetingAssistant Backend — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.api import (
    auth,
    meetings,
    transcriptions,
    protocols,
    tasks,
    analytics,
    users,
    ws,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    setup_logging()
    await init_db()
    yield


app = FastAPI(
    title="MeetingAssistant API",
    description="Цифровой ассистент для обработки записей совещаний",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router,           prefix=PREFIX + "/auth",          tags=["Auth"])
app.include_router(users.router,          prefix=PREFIX + "/users",         tags=["Users"])
app.include_router(meetings.router,       prefix=PREFIX + "/meetings",      tags=["Meetings"])
app.include_router(transcriptions.router, prefix=PREFIX + "/transcriptions",tags=["Transcriptions"])
app.include_router(protocols.router,      prefix=PREFIX + "/protocols",     tags=["Protocols"])
app.include_router(tasks.router,          prefix=PREFIX + "/tasks",         tags=["Tasks"])
app.include_router(analytics.router,      prefix=PREFIX + "/analytics",     tags=["Analytics"])
app.include_router(ws.router,             prefix="/ws",                     tags=["WebSocket"])


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "meeting-assistant-api"}
