from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError

from src.core.config._env import ENV_FILE


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="REDIS_")

    host: str
    port: str
    db: int
    password: str
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    health_check_interval: int = 30

    def client_settings(self, backoff_retries_count: int) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "socket_keepalive": True,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "max_connections": self.max_connections,
            "health_check_interval": self.health_check_interval,
            "retry": Retry(ExponentialBackoff(), backoff_retries_count),
            "retry_on_error": [TimeoutError, ConnectionError],
        }
