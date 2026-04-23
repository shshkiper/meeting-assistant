"""
Transcription service using OpenAI Whisper (local, on-premise).
Supports audio and video files via ffmpeg extraction.
"""

import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import ffmpeg
import whisper
from loguru import logger

from app.core.config import settings


class TranscriptionService:
    """Wraps Whisper for local, on-premise audio transcription."""

    _model: Optional[whisper.Whisper] = None

    @classmethod
    def get_model(cls) -> whisper.Whisper:
        if cls._model is None:
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
            cls._model = whisper.load_model(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
            )
            logger.info("Whisper model loaded successfully")
        return cls._model

    @staticmethod
    async def extract_audio(input_path: str, output_path: str) -> None:
        """Extract audio track from video file using ffmpeg."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                ffmpeg
                .input(input_path)
                .output(output_path, acodec="pcm_s16le", ar=16000, ac=1)
                .overwrite_output()
                .run(quiet=True)
            ),
        )

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio file.
        Returns dict with: text, segments, language
        """
        lang = language or settings.WHISPER_LANGUAGE
        model = self.get_model()

        if progress_callback:
            await progress_callback(10, "Загрузка аудио...")

        # Run in executor to not block the event loop
        loop = asyncio.get_event_loop()

        def _transcribe():
            return model.transcribe(
                audio_path,
                language=lang if lang != "auto" else None,
                word_timestamps=True,
                verbose=False,
                fp16=settings.WHISPER_DEVICE == "cuda",
            )

        result = await loop.run_in_executor(None, _transcribe)

        if progress_callback:
            await progress_callback(60, "Транскрибация завершена")

        # Normalize segments
        segments = [
            {
                "id": seg["id"],
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
                "speaker": "SPEAKER_00",  # will be enriched by diarization
            }
            for seg in result.get("segments", [])
        ]

        return {
            "text": result["text"].strip(),
            "segments": segments,
            "language": result.get("language", lang),
        }


class DiarizationService:
    """Speaker diarization using pyannote.audio."""

    def __init__(self):
        self._pipeline = None

    def get_pipeline(self):
        if self._pipeline is None:
            try:
                from pyannote.audio import Pipeline
                import torch
                logger.info("Loading pyannote diarization pipeline...")
                self._pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=os.getenv("HF_TOKEN"),
                )
                device = "cuda" if settings.WHISPER_DEVICE == "cuda" else "cpu"
                self._pipeline = self._pipeline.to(torch.device(device))
                logger.info("Diarization pipeline loaded")
            except Exception as e:
                logger.warning(f"Could not load pyannote pipeline: {e}. Using stub diarization.")
                return None
        return self._pipeline

    async def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Return list of {speaker, start, end} diarization segments.
        Falls back to single-speaker if pipeline unavailable.
        """
        pipeline = self.get_pipeline()
        if pipeline is None:
            return [{"speaker": "SPEAKER_00", "start": 0.0, "end": 99999.0}]

        loop = asyncio.get_event_loop()
        diarization = await loop.run_in_executor(None, lambda: pipeline(audio_path))

        return [
            {"speaker": str(turn.speaker), "start": round(turn.start, 2), "end": round(turn.end, 2)}
            for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]

    @staticmethod
    def merge_transcript_with_diarization(
        segments: List[Dict], diarization: List[Dict]
    ) -> List[Dict]:
        """Assign speaker labels to transcript segments based on overlap."""
        result = []
        for seg in segments:
            seg_mid = (seg["start"] + seg["end"]) / 2
            speaker = "SPEAKER_00"
            for d in diarization:
                if d["start"] <= seg_mid <= d["end"]:
                    speaker = d["speaker"]
                    break
            result.append({**seg, "speaker": speaker})
        return result


transcription_service = TranscriptionService()
diarization_service = DiarizationService()
