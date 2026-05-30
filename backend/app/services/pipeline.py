# Celery-задача для обработки совещания.
# Шаги: скачать аудио → транскрибация → диаризация → NLP → протокол и задачи

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from celery import Celery
from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import Meeting, MeetingStatus, MeetingTask, Protocol, Transcript
from app.services.transcription import transcription_service, diarization_service
from app.services.nlp import keyword_extractor, contact_extractor, sentiment_analyzer
from app.services.llm import llm_service
from app.services.storage import storage_service

logger = get_task_logger(__name__)

celery_app = Celery("meeting_assistant")
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_max_tasks_per_child=10,  # перезапускаем воркер каждые 10 задач, чтобы не копилась память
)


def run_async(coro):
    # Celery синхронный, а наш код асинхронный — создаём новый event loop для каждой задачи
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _update_meeting_status(meeting_id: str, status: MeetingStatus, **kwargs):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Meeting).where(Meeting.id == UUID(meeting_id)))
        meeting = result.scalar_one_or_none()
        if meeting:
            meeting.status = status
            for k, v in kwargs.items():
                setattr(meeting, k, v)
            await db.commit()


async def _publish_progress(meeting_id: str, step: str, progress: int):
    # Отправляем прогресс в Redis чтобы фронтенд получил обновление по WebSocket.
    # Если Redis недоступен — просто пишем в лог и продолжаем, не роняем пайплайн.
    try:
        import json
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.publish(
            f"meeting:{meeting_id}:progress",
            json.dumps({"step": step, "progress": progress, "meeting_id": meeting_id}),
        )
        await r.aclose()
    except Exception as e:
        logger.warning(f"Не удалось отправить прогресс в Redis (шаг: {step}): {e}")


@celery_app.task(bind=True, name="process_meeting", max_retries=2)
def process_meeting(self, meeting_id: str):
    # Главная задача обработки совещания.
    # При ошибке пробуем ещё раз через 60 секунд (максимум 2 попытки).
    try:
        run_async(_process_meeting_async(meeting_id, self))
    except Exception as exc:
        logger.error(f"Ошибка обработки совещания {meeting_id}: {exc}")
        run_async(_update_meeting_status(meeting_id, MeetingStatus.FAILED))
        raise self.retry(exc=exc, countdown=60)


async def _process_meeting_async(meeting_id: str, task):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Meeting).where(Meeting.id == UUID(meeting_id)))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Шаг 1: скачиваем файл из MinIO на диск
        await _publish_progress(meeting_id, "Загрузка аудио", 5)
        await _update_meeting_status(meeting_id, MeetingStatus.TRANSCRIBING)

        audio_path = os.path.join(tmpdir, "audio.wav")
        object_key = meeting.audio_object_key or meeting.video_object_key

        await storage_service.download_file(
            bucket=settings.MINIO_BUCKET_AUDIO,
            object_key=object_key,
            dest_path=audio_path,
        )

        # Если это видео — вытаскиваем аудиодорожку через ffmpeg
        if object_key and object_key.lower().endswith((".mp4", ".mkv", ".webm", ".avi")):
            wav_path = os.path.join(tmpdir, "extracted.wav")
            await transcription_service.extract_audio(audio_path, wav_path)
            audio_path = wav_path

        # Шаг 2: транскрибация через Whisper
        await _publish_progress(meeting_id, "Транскрибация", 20)
        transcript_result = await transcription_service.transcribe(audio_path)

        # Шаг 3: определяем кто говорил (диаризация)
        await _publish_progress(meeting_id, "Разметка спикеров", 45)
        await _update_meeting_status(meeting_id, MeetingStatus.DIARIZING)

        diarization = await diarization_service.diarize(audio_path)
        segments = diarization_service.merge_transcript_with_diarization(
            transcript_result["segments"], diarization
        )

        # Шаг 4: NLP-анализ — ключевые слова, контакты, тональность
        await _publish_progress(meeting_id, "Анализ текста", 60)
        await _update_meeting_status(meeting_id, MeetingStatus.ANALYZING)

        full_text = transcript_result["text"]
        keywords = keyword_extractor.extract(full_text)
        contacts = contact_extractor.extract(full_text)
        sentiment = sentiment_analyzer.analyze(full_text, segments)

        # Шаг 5: LLM генерирует краткое саммари
        await _publish_progress(meeting_id, "Генерация саммари", 70)
        transcript_with_speakers = _format_transcript(segments)
        summary = await llm_service.generate_summary(transcript_with_speakers)

        # Шаг 6: сохраняем транскрипт в базу
        async with AsyncSessionLocal() as db:
            transcript = Transcript(
                meeting_id=UUID(meeting_id),
                raw_text=full_text,
                segments=segments,
                language_detected=transcript_result.get("language"),
                summary=summary,
                keywords=keywords,
                contacts=contacts,
                sentiment=sentiment,
            )
            db.add(transcript)
            await db.commit()

        # Шаг 7: LLM генерирует полный протокол в Markdown
        await _publish_progress(meeting_id, "Генерация протокола", 80)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Meeting).where(Meeting.id == UUID(meeting_id)))
            mtg = result.scalar_one()

            participants_str = ", ".join(
                {seg["speaker"] for seg in segments}
            )
            date_str = mtg.meeting_date.strftime("%d.%m.%Y") if mtg.meeting_date else "—"

        protocol_md = await llm_service.generate_protocol(
            transcript_with_speakers,
            date=date_str,
            participants=participants_str,
        )

        # Шаг 8: LLM извлекает задачи и поручения
        await _publish_progress(meeting_id, "Извлечение задач", 90)
        extracted_tasks = await llm_service.extract_tasks(transcript_with_speakers)

        # Шаг 9: сохраняем протокол и задачи в базу
        async with AsyncSessionLocal() as db:
            protocol = Protocol(
                meeting_id=UUID(meeting_id),
                content_md=protocol_md,
            )
            db.add(protocol)

            for t in extracted_tasks:
                task_obj = MeetingTask(
                    meeting_id=UUID(meeting_id),
                    title=t.get("title", "Задача")[:500],
                    description=t.get("description"),
                    assignee_name_raw=t.get("assignee_name"),
                    priority=t.get("priority", "medium"),
                    source_segment=t.get("source_segment"),
                )
                db.add(task_obj)

            await db.commit()

        # Шаг 10: помечаем совещание как обработанное
        await _update_meeting_status(meeting_id, MeetingStatus.COMPLETED)
        await _publish_progress(meeting_id, "Обработка завершена", 100)
        logger.info(f"Совещание {meeting_id} успешно обработано")


def _format_transcript(segments) -> str:
    # Собираем транскрипт в читаемый текст — каждая реплика с именем спикера
    lines = []
    current_speaker = None
    for seg in segments:
        spk = seg.get("speaker", "SPEAKER_00")
        text = seg.get("text", "").strip()
        if spk != current_speaker:
            lines.append(f"\n[{spk}]: {text}")
            current_speaker = spk
        else:
            lines.append(text)
    return " ".join(lines)
