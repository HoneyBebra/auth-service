from functools import lru_cache
from logging import config as logging_config

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import BASE_DIR, ENV_FILE
from src.core.config.app import AppSettings
from src.core.config.encryption import EncryptionSettings
from src.core.config.jwt import JwtSettings
from src.core.config.postgres import PostgresSettings
from src.core.config.rate_limit import RateLimitSettings
from src.core.config.redis import RedisSettings
from src.core.logger import LOGGING

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JwtSettings = Field(default_factory=JwtSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    encryption: EncryptionSettings = Field(default_factory=EncryptionSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

logging_config.dictConfig(LOGGING)

__all__ = [
    "BASE_DIR",
    "ENV_FILE",
    "AppSettings",
    "EncryptionSettings",
    "JwtSettings",
    "PostgresSettings",
    "RedisSettings",
    "Settings",
    "get_settings",
    "settings",
]
