"""Meeting tasks CRUD + optional Jira sync."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import MeetingTask, User
from app.schemas.schemas import TaskRead, TaskUpdate

router = APIRouter()


@router.get("/{meeting_id}", response_model=List[TaskRead])
async def list_tasks(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MeetingTask).where(MeetingTask.meeting_id == meeting_id)
    )
    return result.scalars().all()


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MeetingTask).where(MeetingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/sync-jira", response_model=TaskRead)
async def sync_to_jira(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Push task to Jira (if integration enabled)."""
    if not settings.JIRA_ENABLED:
        raise HTTPException(status_code=501, detail="Jira integration not enabled")

    result = await db.execute(select(MeetingTask).where(MeetingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    jira_key = await _create_jira_issue(task)
    task.jira_key = jira_key
    await db.commit()
    await db.refresh(task)
    return task


async def _create_jira_issue(task: MeetingTask) -> str:
    """Create Jira issue and return its key."""
    from jira import JIRA
    jira = JIRA(server=settings.JIRA_URL, token_auth=settings.JIRA_TOKEN)
    issue = jira.create_issue(
        project=settings.JIRA_PROJECT_KEY,
        summary=task.title,
        description=task.description or "",
        issuetype={"name": "Task"},
        priority={"name": task.priority.capitalize()},
    )
    return issue.key
