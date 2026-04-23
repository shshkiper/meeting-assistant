"""Analytics endpoints: sentiment trends, keyword frequency, meeting stats."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Meeting, MeetingStatus, MeetingTask, Transcript, User

router = APIRouter()


@router.get("/dashboard")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Summary stats for the current user."""
    meetings_count = await db.scalar(
        select(func.count()).where(Meeting.owner_id == current_user.id)
    )
    completed = await db.scalar(
        select(func.count()).where(
            Meeting.owner_id == current_user.id,
            Meeting.status == MeetingStatus.COMPLETED,
        )
    )
    total_tasks = await db.scalar(
        select(func.count(MeetingTask.id))
        .join(Meeting)
        .where(Meeting.owner_id == current_user.id)
    )

    return {
        "total_meetings": meetings_count or 0,
        "completed_meetings": completed or 0,
        "total_tasks": total_tasks or 0,
    }


@router.get("/{meeting_id}/sentiment")
async def meeting_sentiment(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    result = await db.execute(select(Transcript).where(Transcript.meeting_id == meeting_id))
    transcript = result.scalar_one_or_none()
    if not transcript or not transcript.sentiment:
        return {}
    return transcript.sentiment


@router.get("/{meeting_id}/keywords")
async def meeting_keywords(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    result = await db.execute(select(Transcript).where(Transcript.meeting_id == meeting_id))
    transcript = result.scalar_one_or_none()
    if not transcript or not transcript.keywords:
        return []
    return transcript.keywords


@router.get("/{meeting_id}/contacts")
async def meeting_contacts(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    result = await db.execute(select(Transcript).where(Transcript.meeting_id == meeting_id))
    transcript = result.scalar_one_or_none()
    if not transcript or not transcript.contacts:
        return []
    return transcript.contacts
