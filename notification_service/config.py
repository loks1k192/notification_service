"""Configuration settings for Notification Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    queue_name: str = "task_notifications"
    exchange_name: str = "task_events"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
