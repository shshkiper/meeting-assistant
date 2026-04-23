"""
Tests for core API endpoints.
Run: pytest backend/tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@bank.com", "full_name": "Test User", "password": "secret123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@bank.com"

    # Login
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@bank.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 403  # No bearer token


@pytest.mark.asyncio
async def test_meetings_requires_auth(client):
    resp = await client.get("/api/v1/meetings/")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client):
    resp = await client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 403


class TestNLPServices:
    """Unit tests for NLP services (no DB/LLM needed)."""

    def test_keyword_extraction(self):
        from app.services.nlp import keyword_extractor
        text = "Банк принял решение об увеличении резервного фонда на следующий квартал."
        result = keyword_extractor.extract(text, top_n=5)
        assert isinstance(result, list)

    def test_contact_extraction_email(self):
        from app.services.nlp import contact_extractor
        text = "Свяжитесь с нами: info@bank.ru или +7 (495) 123-45-67"
        result = contact_extractor.extract(text)
        assert any(c.get("email") for c in result)

    def test_sentiment_analysis(self):
        from app.services.nlp import sentiment_analyzer
        result = sentiment_analyzer.analyze("Совещание прошло очень продуктивно.")
        assert "overall" in result


class TestTranscriptFormatting:
    def test_format_segments(self):
        from app.services.pipeline import _format_transcript
        segments = [
            {"speaker": "SPEAKER_00", "start": 0, "end": 5, "text": "Добрый день."},
            {"speaker": "SPEAKER_01", "start": 5, "end": 10, "text": "Здравствуйте."},
            {"speaker": "SPEAKER_00", "start": 10, "end": 15, "text": "Начнём совещание."},
        ]
        result = _format_transcript(segments)
        assert "SPEAKER_00" in result
        assert "SPEAKER_01" in result
        assert "Добрый день" in result


class TestProtocolExport:
    def test_build_docx(self):
        from app.api.protocols import _build_docx
        md = "# Протокол\n## 1. Повестка\n- Пункт 1\n- Пункт 2\n## 2. Решения\n1. Утвердить бюджет\n"
        result = _build_docx(md, "Тестовое совещание")
        assert isinstance(result, bytes)
        assert len(result) > 1000  # Valid DOCX has content
