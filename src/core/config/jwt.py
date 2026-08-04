from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import ENV_FILE


class JwtSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="JWT_")

    secret_key: str
    algorithm: str
    blacklist_redis_prefix: str = "auth:jwt:bl"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    access_token_key_in_cookie: str = "access_token"
    refresh_token_key_in_cookie: str = "refresh_token"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return value

    @property
    def access_token_expire(self) -> int:
        return self.access_token_expire_minutes * 60

    @property
    def refresh_token_expire(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60

    @property
    def _cookie_base_settings(self) -> dict[str, Any]:
        return {
            "httponly": True,
            "secure": True,
            "samesite": "lax",
        }

    @property
    def access_cookie_set_settings(self) -> dict[str, Any]:
        return {
            "key": self.access_token_key_in_cookie,
            **self._cookie_base_settings,
            "max_age": self.access_token_expire,
        }

    @property
    def access_cookie_delete_settings(self) -> dict[str, Any]:
        return {
            "key": self.access_token_key_in_cookie,
            **self._cookie_base_settings,
        }

    @property
    def refresh_cookie_set_settings(self) -> dict[str, Any]:
        return {
            "key": self.refresh_token_key_in_cookie,
            **self._cookie_base_settings,
            "max_age": self.refresh_token_expire,
        }

    @property
    def refresh_cookie_delete_settings(self) -> dict[str, Any]:
        return {
            "key": self.refresh_token_key_in_cookie,
            **self._cookie_base_settings,
        }
