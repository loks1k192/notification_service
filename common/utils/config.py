"""Shared configuration utilities."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    database_url: str
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


class RedisSettings(BaseSettings):
    """Redis configuration."""

    redis_url: str = "redis://localhost:6379/0"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration."""

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    queue_name: str = "task_notifications"
    exchange_name: str = "task_events"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
