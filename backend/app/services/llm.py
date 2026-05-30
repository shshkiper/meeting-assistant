# Сервис для работы с языковой моделью — генерирует саммари, протоколы, извлекает задачи.
# Работает с Ollama (локально) и OpenAI-совместимыми API.

import json
import re
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings


SUMMARY_PROMPT = """Ты — корпоративный ассистент по протоколированию совещаний.

Ниже приведена транскрипция совещания с разметкой по спикерам.
Составь краткое саммари на русском языке (3-7 предложений), которое включает:
1. Цель встречи
2. Ключевые обсуждённые вопросы
3. Принятые решения

Транскрипция:
{transcript}

Саммари:"""


PROTOCOL_PROMPT = """Ты — корпоративный секретарь. Составь протокол совещания в формате Markdown на основе транскрипции.

Структура протокола:
# Протокол совещания

**Дата:** {date}
**Участники:** {participants}
**Председатель:** {chair}
**Секретарь:** {secretary}

## 1. Повестка дня
(перечисли пункты)

## 2. Ход совещания
(краткое изложение по каждому пункту)

## 3. Принятые решения
(нумерованный список решений)

## 4. Поручения
(таблица: № | Поручение | Ответственный | Срок | Статус)

## 5. Следующее совещание
(если упоминалось)

Транскрипция:
{transcript}

Протокол:"""


TASKS_PROMPT = """Ты — ассистент по управлению задачами.

Из следующей транскрипции совещания извлеки все поручения, задачи и обязательства.
Верни ТОЛЬКО валидный JSON-массив без пояснений.

Формат каждого объекта:
{{
  "title": "краткое название задачи (до 100 символов)",
  "description": "подробное описание",
  "assignee_name": "имя ответственного или null",
  "due_date": "YYYY-MM-DD или null",
  "priority": "high | medium | low",
  "source_segment": "точная цитата из транскрипции"
}}

Транскрипция:
{transcript}

JSON:"""


class LLMService:
    # Один класс для всех LLM — работает и с Ollama и с OpenAI

    async def _call(self, prompt: str, max_tokens: int = 2000) -> str:
        # Выбираем нужный провайдер из настроек
        provider = settings.LLM_PROVIDER.lower()

        if provider == "ollama":
            return await self._call_ollama(prompt, max_tokens)
        elif provider in ("openai", "anthropic"):
            return await self._call_openai_compat(prompt, max_tokens)
        else:
            raise ValueError(f"Неизвестный провайдер LLM: {provider}")

    async def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        # Отправляем запрос в Ollama (локальный сервер)
        import httpx
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{settings.LLM_BASE_URL}/api/generate",
                json={
                    "model": settings.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.3},
                },
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def _call_openai_compat(self, prompt: str, max_tokens: int) -> str:
        # Отправляем запрос в OpenAI-совместимый API
        import httpx
        headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
        base = settings.LLM_BASE_URL or "https://api.openai.com"
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{base}/v1/chat/completions",
                headers=headers,
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def generate_summary(self, transcript_text: str) -> str:
        # Генерируем краткое саммари совещания
        logger.info("Генерация саммари...")
        prompt = SUMMARY_PROMPT.format(transcript=transcript_text[:8000])
        summary = await self._call(prompt, max_tokens=1000)
        return summary.strip()

    async def generate_protocol(
        self,
        transcript_text: str,
        date: str = "",
        participants: str = "",
        chair: str = "—",
        secretary: str = "—",
    ) -> str:
        # Генерируем полный протокол в формате Markdown
        logger.info("Генерация протокола...")
        prompt = PROTOCOL_PROMPT.format(
            transcript=transcript_text[:10000],
            date=date,
            participants=participants,
            chair=chair,
            secretary=secretary,
        )
        protocol = await self._call(prompt, max_tokens=3000)
        return protocol.strip()

    async def extract_tasks(self, transcript_text: str) -> List[Dict[str, Any]]:
        # Извлекаем задачи и поручения из транскрипта
        logger.info("Извлечение задач...")
        prompt = TASKS_PROMPT.format(transcript=transcript_text[:8000])
        response = await self._call(prompt, max_tokens=2000)

        # Убираем markdown-обёртку если LLM добавил ```json ... ```
        json_text = re.sub(r"```(?:json)?|```", "", response).strip()

        # Ищем массив [...] в ответе
        match = re.search(r"\[.*\]", json_text, re.DOTALL)
        if match:
            json_text = match.group(0)

        try:
            tasks = json.loads(json_text)
            if not isinstance(tasks, list):
                return []
            return tasks
        except json.JSONDecodeError as e:
            logger.warning(f"Не удалось распарсить JSON с задачами: {e}")
            return []


llm_service = LLMService()
