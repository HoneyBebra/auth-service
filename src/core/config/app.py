from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import ENV_FILE


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="APP_")

    name: str
    description: str
    version: str
    api_v1_prefix: str = "/auth/api/v1"
    password_min_length: int = 8
    backoff_retries_count: int = 10
    grpc_port: int = 50051
