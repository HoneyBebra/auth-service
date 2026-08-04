from functools import lru_cache
from logging import config as logging_config

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import ENV_FILE
from src.core.config.app import AppSettings
from src.core.config.encryption import EncryptionSettings
from src.core.config.jwt import JwtSettings
from src.core.config.postgres import PostgresSettings
from src.core.config.rate_limit import RateLimitSettings
from src.core.config.redis import RedisSettings
from src.core.logging.logger import LOGGING

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)  # type: ignore[arg-type]
    redis: RedisSettings = Field(default_factory=RedisSettings)  # type: ignore[arg-type]
    jwt: JwtSettings = Field(default_factory=JwtSettings)  # type: ignore[arg-type]
    app: AppSettings = Field(default_factory=AppSettings)  # type: ignore[arg-type]
    encryption: EncryptionSettings = Field(default_factory=EncryptionSettings)  # type: ignore[arg-type]
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)  # type: ignore[arg-type]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

logging_config.dictConfig(LOGGING)
