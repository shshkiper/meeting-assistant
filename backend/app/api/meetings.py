"""Meetings CRUD + file upload endpoint."""

import uuid
import mimetypes
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Meeting, MeetingStatus, User
from app.schemas.schemas import MeetingCreate, MeetingDetail, MeetingRead
from app.services.storage import storage_service
from app.services.pipeline import process_meeting

router = APIRouter()

ALLOWED_AUDIO_MIME = {
    "audio/mpeg", "audio/wav", "audio/x-wav", "audio/ogg",
    "audio/mp4", "audio/aac", "audio/flac", "audio/webm",
    "video/mp4", "video/webm", "video/x-matroska", "video/avi",
}


@router.get("/", response_model=List[MeetingRead])
async def list_meetings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    result = await db.execute(
        select(Meeting)
        .where(Meeting.owner_id == current_user.id)
        .order_by(Meeting.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/", response_model=MeetingRead, status_code=201)
async def create_meeting(
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload recording and create meeting — triggers async processing pipeline."""
    # Validate MIME type
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if content_type not in ALLOWED_AUDIO_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {content_type}. Allowed: audio/video files.",
        )

    meeting_id = uuid.uuid4()
    ext = (file.filename or "audio").rsplit(".", 1)[-1].lower()
    object_key = f"{meeting_id}/recording.{ext}"

    # Upload to MinIO
    data = await file.read()
    await storage_service.upload_file(
        bucket=settings.MINIO_BUCKET_AUDIO,
        object_key=object_key,
        data=data,
        content_type=content_type,
    )

    # Persist meeting record
    is_video = content_type.startswith("video/")
    meeting = Meeting(
        id=meeting_id,
        title=title,
        description=description,
        owner_id=current_user.id,
        status=MeetingStatus.UPLOADED,
        audio_object_key=None if is_video else object_key,
        video_object_key=object_key if is_video else None,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    # Kick off Celery pipeline
    task = process_meeting.delay(str(meeting_id))
    meeting.celery_task_id = task.id
    await db.commit()

    return meeting


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your meeting")
    await db.delete(meeting)
    await db.commit()
