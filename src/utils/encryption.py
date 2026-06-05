import hashlib
import hmac
from functools import lru_cache

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from src.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"])


@lru_cache
def get_fernet() -> Fernet:
    return Fernet(settings.encryption.user_data_secret_key)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_user_data(data: str) -> str:
    return hmac.new(
        settings.encryption.user_data_secret_key.encode(),
        data.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_user_data(data: str, hashed_data: str) -> bool:
    return hash_user_data(data) == hashed_data


def encrypt_data(data: str) -> str:
    fernet = get_fernet()
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(data: str) -> str:
    fernet = get_fernet()
    return fernet.decrypt(data.encode()).decode()
