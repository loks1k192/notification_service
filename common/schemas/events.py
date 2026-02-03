"""Shared event schemas for RabbitMQ messages."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for task notifications."""

    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    TASK_STATUS_CHANGED = "task.status_changed"


class TaskEvent(BaseModel):
    """Base schema for task-related events."""

    event_id: UUID = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    task_id: UUID = Field(..., description="Task identifier")
    user_id: UUID = Field(..., description="User who owns the task")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    data: dict = Field(default_factory=dict, description="Additional event data")

    model_config = {"json_schema_extra": {"examples": [{"event_id": "123e4567-e89b-12d3-a456-426614174000"}]}}


class NotificationStatus(str, Enum):
    """Notification processing status."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
