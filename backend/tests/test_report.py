import re

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client_no_lifespan():
    async with AsyncClient(
        transport=ASGITransport(app=app, lifespan="off"),
        base_url="http://test",
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_openapi_available(client_no_lifespan):
    resp = await client_no_lifespan.get("/api/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("info", {}).get("title") == "MeetingAssistant API"


@pytest.mark.asyncio
async def test_docs_available(client_no_lifespan):
    resp = await client_no_lifespan.get("/api/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()


@pytest.mark.asyncio
async def test_health_shape(client_no_lifespan):
    resp = await client_no_lifespan.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) >= {"status", "service"}
    assert data["status"] == "ok"


def test_env_example_has_required_keys():
    # Проверяем, что основные настройки реально вынесены в .env
    import pathlib

    env_path = pathlib.Path(__file__).resolve().parents[2] / ".env.example"
    text = env_path.read_text(encoding="utf-8")
    for key in [
        "DATABASE_URL=",
        "REDIS_URL=",
        "MINIO_ENDPOINT=",
        "WHISPER_MODEL=",
        "LLM_PROVIDER=",
        "LOG_LEVEL=",
    ]:
        assert key in text


def test_allowed_audio_mime_list_looks_reasonable():
    from app.api.meetings import ALLOWED_AUDIO_MIME

    assert isinstance(ALLOWED_AUDIO_MIME, set)
    assert "audio/mpeg" in ALLOWED_AUDIO_MIME
    assert "audio/wav" in ALLOWED_AUDIO_MIME
    assert "video/mp4" in ALLOWED_AUDIO_MIME


def test_protocol_template_exists():
    import pathlib

    template_path = (
        pathlib.Path(__file__).resolve().parents[1]
        / ".."
        / "app"
        / "services"
        / "protocol_template.md.j2"
    ).resolve()
    assert template_path.exists()
    text = template_path.read_text(encoding="utf-8")
    assert len(text.strip()) > 50


def test_security_tokens_are_jwt_like():
    from app.core.security import create_access_token, create_refresh_token

    a = create_access_token("user-1")
    r = create_refresh_token("user-1")
    # JWT: header.payload.signature
    assert a.count(".") == 2
    assert r.count(".") == 2


def test_nlp_keyword_extraction_smoke():
    from app.services.nlp import keyword_extractor

    text = "Банк утвердил стратегию цифровой трансформации и план мероприятий."
    res = keyword_extractor.extract(text, top_n=5)
    assert isinstance(res, list)
    assert len(res) <= 5


def test_contact_extractor_finds_email_or_phone():
    from app.services.nlp import contact_extractor

    text = "Контакты: info@bank.ru, +7 (495) 123-45-67"
    res = contact_extractor.extract(text)
    assert isinstance(res, list)
    assert any((c.get("email") or c.get("phone")) for c in res)


def test_transcript_formatting_has_speakers_and_timestamps():
    from app.services.pipeline import _format_transcript

    segments = [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 5.0, "text": "Добрый день."},
        {"speaker": "SPEAKER_01", "start": 5.0, "end": 9.0, "text": "Здравствуйте."},
    ]
    formatted = _format_transcript(segments)
    assert "SPEAKER_00" in formatted
    assert "SPEAKER_01" in formatted
    # Должно быть что-то похожее на таймкоды (например, 00:00:05)
    assert re.search(r"\d{2}:\d{2}:\d{2}", formatted) is not None

