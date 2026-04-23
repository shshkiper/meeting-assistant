"""Transcription read + participant labelling."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Meeting, MeetingParticipant, Transcript, User
from app.schemas.schemas import ParticipantRead, ParticipantUpdate, TranscriptRead

router = APIRouter()


@router.get("/{meeting_id}", response_model=TranscriptRead)
async def get_transcript(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Transcript).where(Transcript.meeting_id == meeting_id))
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not ready yet")
    return transcript


@router.get("/{meeting_id}/participants", response_model=List[ParticipantRead])
async def list_participants(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting_id)
    )
    return result.scalars().all()


@router.patch("/{meeting_id}/participants/{participant_id}", response_model=ParticipantRead)
async def update_participant(
    meeting_id: uuid.UUID,
    participant_id: uuid.UUID,
    body: ParticipantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MeetingParticipant).where(
            MeetingParticipant.id == participant_id,
            MeetingParticipant.meeting_id == meeting_id,
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(participant, field, value)
    await db.commit()
    await db.refresh(participant)
    return participant
