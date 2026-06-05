from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.exc import DisconnectionError, OperationalError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.config._env import ENV_FILE


def sqlalchemy_backoff_decorator_settings(retries_count: int) -> dict[str, Any]:
    return {
        "stop": stop_after_attempt(retries_count),
        "wait": wait_exponential(multiplier=1, min=2, max=60),
        "retry": retry_if_exception_type((OperationalError, DisconnectionError)),
        "reraise": True,
    }


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="POSTGRES_")

    user: str
    password: str
    db: str
    host: str
    port: str
    echo: bool

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.user}:"
            f"{self.password}@"
            f"{self.host}:"
            f"{self.port}/"
            f"{self.db}"
        )
