from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config._env import ENV_FILE

_FERNET_KEY_ERROR = (
    "ENCRYPTION_USER_DATA_SECRET_KEY must be a valid Fernet key "
    "(32 url-safe base64-encoded bytes). Generate with: "
    'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
)


class EncryptionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="ENCRYPTION_")

    user_data_secret_key: str

    @field_validator("user_data_secret_key")
    @classmethod
    def validate_user_data_secret_key(cls, value: str) -> str:
        try:
            Fernet(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(_FERNET_KEY_ERROR) from exc
        return value
