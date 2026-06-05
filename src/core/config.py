from functools import lru_cache
from logging import config as logging_config
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from sqlalchemy.exc import DisconnectionError, OperationalError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.logger import LOGGING

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    postgres_echo: bool

    api_v1_prefix: str = "/auth/api/v1"

    app_name: str
    app_description: str
    app_version: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_blacklist_redis_prefix: str = "auth:jwt:bl"

    access_token_key_in_cookie: str = "access_token"
    refresh_token_key_in_cookie: str = "refresh_token"

    access_token_expire: int = access_token_expire_minutes * 60
    refresh_token_expire: int = refresh_token_expire_days * 24 * 60 * 60

    password_min_length: int = 8

    redis_host: str
    redis_port: str
    redis_db: int
    redis_password: str
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    redis_max_connections: int = 50
    redis_health_check_interval: int = 30

    encryption_user_data_secret_key: str

    backoff_retries_count: int = 10

    grpc_port: int = 50051

    __cookie_base_settings: dict[str, Any] = {
        "httponly": True,
        "secure": True,
        "samesite": "lax",
    }
    __access_cookie_base_settings: dict[str, Any] = {
        "key": access_token_key_in_cookie,
        **__cookie_base_settings,
    }
    __refresh_cookie_base_settings: dict[str, Any] = {
        "key": refresh_token_key_in_cookie,
        **__cookie_base_settings,
    }

    access_cookie_set_settings: dict[str, Any] = {
        **__access_cookie_base_settings,
        "max_age": access_token_expire,
    }
    access_cookie_delete_settings: dict[str, Any] = __access_cookie_base_settings

    refresh_cookie_set_settings: dict[str, Any] = {
        **__refresh_cookie_base_settings,
        "max_age": refresh_token_expire
    }
    refresh_cookie_delete_settings: dict[str, Any] = __refresh_cookie_base_settings

    @property
    def backoff_decorator_sqlalchemy_settings(self) -> dict[str, Any]:
        return {
            "stop": stop_after_attempt(self.backoff_retries_count),
            "wait":  wait_exponential(multiplier=1, min=2, max=60),
            "retry": retry_if_exception_type((OperationalError, DisconnectionError)),
            "reraise": True,
        }

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    @property
    def redis_settings(self) -> dict[str, Any]:
        return {
            "host": self.redis_host,
            "port": self.redis_port,
            "db": self.redis_db,
            "password": self.redis_password,
            "socket_keepalive": True,
            "socket_timeout": self.redis_socket_timeout,
            "socket_connect_timeout": self.redis_socket_connect_timeout,
            "max_connections": self.redis_max_connections,
            "health_check_interval": self.redis_health_check_interval,
            "retry": Retry(ExponentialBackoff(), self.backoff_retries_count),
            "retry_on_error": [TimeoutError, ConnectionError],
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

logging_config.dictConfig(LOGGING)
