"""Event service for publishing task events to RabbitMQ."""

from uuid import uuid4

from common.schemas.events import TaskEvent, EventType
from common.utils.rabbitmq import get_rabbitmq_connection, setup_exchange_and_queue, publish_task_event
from task_service.config import settings
from task_service.models import Task, TaskStatus


class EventService:
    """Service for publishing task events."""

    _connection = None
    _exchange = None

    @classmethod
    async def _ensure_connection(cls) -> None:
        """Ensure RabbitMQ connection and exchange are initialized."""
        if cls._connection is None or cls._connection.is_closed:
            cls._connection = await get_rabbitmq_connection(settings.rabbitmq_url)
            cls._exchange, _ = await setup_exchange_and_queue(
                cls._connection, settings.exchange_name, settings.queue_name
            )

    @classmethod
    async def publish_task_created(cls, task: Task) -> None:
        """Publish task created event."""
        await cls._ensure_connection()

        event = TaskEvent(
            event_id=uuid4(),
            event_type=EventType.TASK_CREATED,
            task_id=task.id,
            user_id=task.owner_id,
            data={
                "title": task.title,
                "status": task.status.value,
            },
        )

        await publish_task_event(cls._exchange, event)

    @classmethod
    async def publish_task_updated(cls, task: Task) -> None:
        """Publish task updated event."""
        await cls._ensure_connection()

        event = TaskEvent(
            event_id=uuid4(),
            event_type=EventType.TASK_UPDATED,
            task_id=task.id,
            user_id=task.owner_id,
            data={
                "title": task.title,
                "status": task.status.value,
            },
        )

        await publish_task_event(cls._exchange, event)

    @classmethod
    async def publish_task_status_changed(
        cls, task: Task, old_status: str
    ) -> None:
        """Publish task status changed event."""
        await cls._ensure_connection()

        event = TaskEvent(
            event_id=uuid4(),
            event_type=EventType.TASK_STATUS_CHANGED,
            task_id=task.id,
            user_id=task.owner_id,
            data={
                "title": task.title,
                "old_status": old_status.value if isinstance(old_status, TaskStatus) else str(old_status),
                "new_status": task.status.value,
            },
        )

        await publish_task_event(cls._exchange, event)

    @classmethod
    async def publish_task_deleted(cls, task: Task) -> None:
        """Publish task deleted event."""
        await cls._ensure_connection()

        event = TaskEvent(
            event_id=uuid4(),
            event_type=EventType.TASK_DELETED,
            task_id=task.id,
            user_id=task.owner_id,
            data={
                "title": task.title,
            },
        )

        await publish_task_event(cls._exchange, event)
