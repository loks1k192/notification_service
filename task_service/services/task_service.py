"""Task service for task management operations."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from task_service.models import Task, User, TaskStatus
from task_service.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskFilter, TaskListResponse


class TaskService:
    """Service for task-related operations."""

    @staticmethod
    async def create_task(db: AsyncSession, task_create: TaskCreate, owner_id: UUID) -> Task:
        """Create a new task."""
        db_task = Task(**task_create.model_dump(), owner_id=owner_id)
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return db_task

    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: UUID, owner_id: UUID) -> Task:
        """Get a task by ID, ensuring it belongs to the user."""
        result = await db.execute(
            select(Task).where(and_(Task.id == task_id, Task.owner_id == owner_id))
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return task

    @staticmethod
    async def get_tasks(
        db: AsyncSession, owner_id: UUID, task_filter: TaskFilter
    ) -> TaskListResponse:
        """Get tasks with filtering and pagination."""
        # Build query
        query = select(Task).where(Task.owner_id == owner_id)

        # Apply filters
        if task_filter.status:
            query = query.where(Task.status == task_filter.status)

        if task_filter.search:
            search_pattern = f"%{task_filter.search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.offset(task_filter.skip).limit(task_filter.limit).order_by(Task.created_at.desc())

        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()

        return TaskListResponse(
            tasks=[TaskResponse.model_validate(task) for task in tasks],
            total=total,
            skip=task_filter.skip,
            limit=task_filter.limit,
        )

    @staticmethod
    async def update_task(
        db: AsyncSession, task_id: UUID, task_update: TaskUpdate, owner_id: UUID
    ) -> Task:
        """Update a task."""
        task = await TaskService.get_task_by_id(db, task_id, owner_id)

        # Track status change
        old_status = task.status

        # Update fields
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        await db.commit()
        await db.refresh(task)

        # Check if status changed
        status_changed = old_status != task.status

        # Store metadata for event publishing
        task._status_changed = status_changed
        task._old_status = old_status

        return task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: UUID, owner_id: UUID) -> None:
        """Delete a task."""
        task = await TaskService.get_task_by_id(db, task_id, owner_id)
        await db.delete(task)
        await db.commit()
