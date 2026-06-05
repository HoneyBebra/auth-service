from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import ENV_FILE


class EncryptionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="ENCRYPTION_")

    user_data_secret_key: str
