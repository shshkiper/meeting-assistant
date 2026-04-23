"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "member"


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Meeting ───────────────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    meeting_date: Optional[datetime] = None


class MeetingRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    meeting_date: Optional[datetime]
    duration_seconds: Optional[int]
    status: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingDetail(MeetingRead):
    transcript: Optional["TranscriptRead"] = None
    protocol: Optional["ProtocolRead"] = None
    tasks: List["TaskRead"] = []
    participants: List["ParticipantRead"] = []


# ── Transcript ────────────────────────────────────────────────────────────────

class Segment(BaseModel):
    speaker: str
    start: float
    end: float
    text: str


class TranscriptRead(BaseModel):
    id: UUID
    meeting_id: UUID
    raw_text: Optional[str]
    segments: Optional[List[Segment]]
    language_detected: Optional[str]
    summary: Optional[str]
    keywords: Optional[List[Dict[str, Any]]]
    contacts: Optional[List[Dict[str, Any]]]
    sentiment: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Protocol ──────────────────────────────────────────────────────────────────

class ProtocolRead(BaseModel):
    id: UUID
    meeting_id: UUID
    content_md: Optional[str]
    content_html: Optional[str]
    agenda: Optional[List[str]]
    decisions: Optional[List[str]]
    next_meeting_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProtocolUpdate(BaseModel):
    content_md: Optional[str] = None
    agenda: Optional[List[str]] = None
    decisions: Optional[List[str]] = None
    next_meeting_date: Optional[datetime] = None


# ── Task ──────────────────────────────────────────────────────────────────────

class TaskRead(BaseModel):
    id: UUID
    meeting_id: UUID
    title: str
    description: Optional[str]
    assignee_id: Optional[UUID]
    assignee_name_raw: Optional[str]
    due_date: Optional[datetime]
    priority: str
    status: str
    jira_key: Optional[str]
    source_segment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None


# ── Participant ───────────────────────────────────────────────────────────────

class ParticipantRead(BaseModel):
    id: UUID
    speaker_label: str
    display_name: Optional[str]
    role_in_meeting: Optional[str]

    model_config = {"from_attributes": True}


class ParticipantUpdate(BaseModel):
    display_name: Optional[str] = None
    role_in_meeting: Optional[str] = None
    user_id: Optional[UUID] = None


# ── Processing status ─────────────────────────────────────────────────────────

class ProcessingStatus(BaseModel):
    meeting_id: UUID
    status: str
    progress: int = 0         # 0-100
    current_step: str = ""
    error: Optional[str] = None


# Forward refs
MeetingDetail.model_rebuild()
