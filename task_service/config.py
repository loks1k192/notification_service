"""Configuration settings for Task Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql+asyncpg://taskuser:taskpass@localhost:5432/taskdb"

    # JWT
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    queue_name: str = "task_notifications"
    exchange_name: str = "task_events"

    # Redis (for caching, if needed)
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
