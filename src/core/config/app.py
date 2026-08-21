from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import ENV_FILE


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="APP_")

    name: str = "auth"
    description: str = "auth-service"
    version: str = "0.1.0"
    api_v1_prefix: str = "/auth/api/v1"
    password_min_length: int = 8
    password_max_length: int = 128
    backoff_retries_count: int = 10
    grpc_port: int = 50051
