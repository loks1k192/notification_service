"""Task management router."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.database import get_db
from task_service.models import User, Task, TaskStatus
from task_service.auth import get_current_user
from task_service.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskFilter,
    TaskListResponse,
)
from task_service.services.task_service import TaskService
from task_service.services.event_service import EventService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Create a new task.
    
    - **title**: Task title (required)
    - **description**: Task description (optional)
    - **status**: Task status (default: pending)
    """
    task = await TaskService.create_task(db, task_create, current_user.id)
    
    # Publish task created event
    await EventService.publish_task_created(task)
    
    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    status: TaskStatus | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """
    Get tasks with filtering and pagination.
    
    - **status**: Filter by task status
    - **search**: Search in title and description
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (1-100)
    """
    task_filter = TaskFilter(status=status, search=search, skip=skip, limit=limit)
    return await TaskService.get_tasks(db, current_user.id, task_filter)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Get a task by ID."""
    task = await TaskService.get_task_by_id(db, task_id, current_user.id)
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Update a task.
    
    - **title**: New task title (optional)
    - **description**: New task description (optional)
    - **status**: New task status (optional)
    """
    task = await TaskService.update_task(db, task_id, task_update, current_user.id)
    
    # Publish appropriate event
    if hasattr(task, "_status_changed") and task._status_changed:
        await EventService.publish_task_status_changed(task, task._old_status)
    else:
        await EventService.publish_task_updated(task)
    
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a task."""
    task = await TaskService.get_task_by_id(db, task_id, current_user.id)
    await TaskService.delete_task(db, task_id, current_user.id)
    
    # Publish task deleted event
    await EventService.publish_task_deleted(task)
