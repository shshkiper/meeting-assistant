"""SQLAlchemy ORM-модели — описание таблиц базы данных."""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ── Перечисления ──────────────────────────────────────────────────────────────

class MeetingStatus(str, enum.Enum):
    UPLOADED    = "uploaded"
    TRANSCRIBING = "transcribing"
    DIARIZING   = "diarizing"
    ANALYZING   = "analyzing"
    COMPLETED   = "completed"
    FAILED      = "failed"


class TaskStatus(str, enum.Enum):
    OPEN        = "open"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    CANCELLED   = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email          = Column(String(255), unique=True, nullable=False, index=True)
    full_name      = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # None для LDAP-пользователей
    role           = Column(String(50), nullable=False, default="member")
    is_active      = Column(Boolean, nullable=False, default=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(),
                            onupdate=func.now(), nullable=False)

    meetings       = relationship("Meeting", back_populates="owner", lazy="select")


# ── Meeting ───────────────────────────────────────────────────────────────────

class Meeting(Base):
    __tablename__ = "meetings"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title            = Column(String(500), nullable=False)
    description      = Column(Text, nullable=True)
    meeting_date     = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    status           = Column(
        Enum(MeetingStatus, name="meetingstatus"),
        nullable=False,
        default=MeetingStatus.UPLOADED,
    )

    owner_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                              nullable=False, index=True)

    # Ключи файлов в MinIO
    audio_object_key = Column(String(512), nullable=True)
    video_object_key = Column(String(512), nullable=True)

    # ID задачи Celery для отслеживания прогресса
    celery_task_id   = Column(String(255), nullable=True)

    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(),
                              onupdate=func.now(), nullable=False)

    owner        = relationship("User", back_populates="meetings")
    transcript   = relationship("Transcript", back_populates="meeting",
                                uselist=False, cascade="all, delete-orphan")
    protocol     = relationship("Protocol", back_populates="meeting",
                                uselist=False, cascade="all, delete-orphan")
    tasks        = relationship("MeetingTask", back_populates="meeting",
                                cascade="all, delete-orphan")
    participants = relationship("MeetingParticipant", back_populates="meeting",
                                cascade="all, delete-orphan")


# ── Transcript ────────────────────────────────────────────────────────────────

class Transcript(Base):
    __tablename__ = "transcripts"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id        = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"),
                               nullable=False, unique=True, index=True)
    raw_text          = Column(Text, nullable=True)
    segments          = Column(JSON, nullable=True)      # List[{speaker, start, end, text}]
    language_detected = Column(String(10), nullable=True)
    summary           = Column(Text, nullable=True)
    keywords          = Column(JSON, nullable=True)      # List[{word, score}]
    contacts          = Column(JSON, nullable=True)      # List[{type, value}]
    sentiment         = Column(JSON, nullable=True)      # {overall, by_speaker, timeline}
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    meeting = relationship("Meeting", back_populates="transcript")


# ── Protocol ──────────────────────────────────────────────────────────────────

class Protocol(Base):
    __tablename__ = "protocols"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id       = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"),
                              nullable=False, unique=True, index=True)
    content_md       = Column(Text, nullable=True)      # Markdown
    content_html     = Column(Text, nullable=True)      # HTML (генерируется по запросу)
    agenda           = Column(JSON, nullable=True)      # List[str]
    decisions        = Column(JSON, nullable=True)      # List[str]
    next_meeting_date = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(),
                              onupdate=func.now(), nullable=False)

    meeting = relationship("Meeting", back_populates="protocol")


# ── MeetingTask ───────────────────────────────────────────────────────────────

class MeetingTask(Base):
    __tablename__ = "meeting_tasks"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id        = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    title             = Column(String(500), nullable=False)
    description       = Column(Text, nullable=True)
    assignee_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
                               nullable=True)
    assignee_name_raw = Column(String(255), nullable=True)  # имя как распознал LLM
    due_date          = Column(DateTime(timezone=True), nullable=True)
    priority          = Column(String(20), nullable=False, default="medium")
    status            = Column(String(20), nullable=False, default="open")
    jira_key          = Column(String(50), nullable=True)   # ключ задачи в Jira если интеграция включена
    source_segment    = Column(Text, nullable=True)         # цитата из транскрипта
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    meeting  = relationship("Meeting", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])


# ── MeetingParticipant ────────────────────────────────────────────────────────

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id      = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    speaker_label   = Column(String(50), nullable=False)    # SPEAKER_00, SPEAKER_01, ...
    display_name    = Column(String(255), nullable=True)    # имя заданное пользователем
    role_in_meeting = Column(String(100), nullable=True)    # председатель, секретарь, ...
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
                             nullable=True)

    meeting = relationship("Meeting", back_populates="participants")
    user    = relationship("User", foreign_keys=[user_id])
