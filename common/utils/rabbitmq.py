"""RabbitMQ connection utilities."""

import json
from typing import Optional
from uuid import uuid4

import aio_pika
from aio_pika import Connection, Exchange, Message, Queue

from common.schemas.events import TaskEvent


async def get_rabbitmq_connection(rabbitmq_url: str) -> Connection:
    """Create and return a RabbitMQ connection."""
    return await aio_pika.connect_robust(rabbitmq_url)


async def setup_exchange_and_queue(
    connection: Connection, exchange_name: str, queue_name: str
) -> tuple[Exchange, Queue]:
    """Set up exchange and queue for task events."""
    channel = await connection.channel()

    # Declare exchange
    exchange = await channel.declare_exchange(
        exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
    )

    # Declare queue
    queue = await channel.declare_queue(queue_name, durable=True)

    # Bind queue to exchange
    await queue.bind(exchange, routing_key="task.*")

    return exchange, queue


async def publish_task_event(
    exchange: Exchange, event: TaskEvent, routing_key: Optional[str] = None
) -> None:
    """Publish a task event to RabbitMQ."""
    if routing_key is None:
        routing_key = event.event_type.value

    message_body = event.model_dump_json()
    message = Message(
        message_body.encode(),
        message_id=str(event.event_id),
        timestamp=event.timestamp,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await exchange.publish(message, routing_key=routing_key)
