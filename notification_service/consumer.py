"""RabbitMQ consumer for processing task notifications."""

import asyncio
import json
import logging
from typing import Optional

import aio_pika
import redis.asyncio as redis
from aio_pika.abc import AbstractIncomingMessage

from common.schemas.events import TaskEvent, NotificationStatus
from notification_service.config import settings
from notification_service.processor import NotificationProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class NotificationConsumer:
    """Consumer for processing task notification events from RabbitMQ."""

    def __init__(self) -> None:
        """Initialize the consumer."""
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.redis_client: Optional[redis.Redis] = None
        self.processor = NotificationProcessor()

    async def connect_redis(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def connect_rabbitmq(self) -> None:
        """Connect to RabbitMQ and set up exchange/queue."""
        try:
            self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                settings.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(settings.queue_name, durable=True)

            # Bind queue to exchange
            await self.queue.bind(exchange, routing_key="task.*")

            logger.info("Connected to RabbitMQ and set up queue")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def _get_notification_status(self, event_id: str) -> Optional[str]:
        """Get notification status from Redis."""
        if not self.redis_client:
            return None

        try:
            status = await self.redis_client.get(f"notification:{event_id}")
            return status
        except Exception as e:
            logger.error(f"Failed to get notification status from Redis: {e}")
            return None

    async def _set_notification_status(
        self, event_id: str, status: NotificationStatus
    ) -> None:
        """Set notification status in Redis."""
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                f"notification:{event_id}", 86400 * 7, status.value
            )  # 7 days TTL
        except Exception as e:
            logger.error(f"Failed to set notification status in Redis: {e}")

    async def _process_message(self, message: AbstractIncomingMessage) -> None:
        """Process a single message from RabbitMQ."""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                event = TaskEvent(**body)

                # Check if already processed (deduplication)
                existing_status = await self._get_notification_status(str(event.event_id))
                if existing_status == NotificationStatus.PROCESSED.value:
                    logger.info(f"Event {event.event_id} already processed, skipping")
                    return

                logger.info(
                    f"Processing event: {event.event_type} for task {event.task_id}"
                )

                # Set status to pending
                await self._set_notification_status(event.event_id, NotificationStatus.PENDING)

                # Process notification
                await self.processor.process_notification(event)

                # Mark as processed
                await self._set_notification_status(
                    event.event_id, NotificationStatus.PROCESSED
                )

                logger.info(f"Successfully processed event {event.event_id}")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                if self.redis_client and event:
                    try:
                        await self._set_notification_status(
                            event.event_id, NotificationStatus.FAILED
                        )
                    except Exception as redis_error:
                        logger.error(f"Failed to set failed status: {redis_error}")

                # Re-raise to let RabbitMQ handle retries if needed
                raise

    async def start(self) -> None:
        """Start consuming messages."""
        await self.connect_redis()
        await self.connect_rabbitmq()

        logger.info("Starting notification consumer...")

        if not self.queue:
            raise RuntimeError("Queue not initialized")

        # Start consuming
        await self.queue.consume(self._process_message)
        logger.info("Notification consumer started and listening for messages")

    async def stop(self) -> None:
        """Stop the consumer and close connections."""
        logger.info("Stopping notification consumer...")

        if self.queue:
            await self.queue.cancel()

        if self.channel:
            await self.channel.close()

        if self.connection:
            await self.connection.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Notification consumer stopped")


async def main() -> None:
    """Main entry point for the notification consumer."""
    consumer = NotificationConsumer()

    try:
        await consumer.start()

        # Keep running
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
