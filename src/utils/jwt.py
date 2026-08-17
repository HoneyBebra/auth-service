import time
from typing import Literal
from uuid import UUID

import jwt

from src.core.config import settings
from src.exceptions.jwt import TokenWrongTypeError


async def create_token(
        sub: UUID | str,
        token_type: Literal["access", "refresh"],
) -> str:
    iat = time.time()
    raw_data = {
        "sub": str(sub),
        "iat": iat,
    }

    if token_type == "access":
        raw_data["exp"] = iat + settings.jwt.access_token_expire
    elif token_type == "refresh":
        raw_data["exp"] = iat + settings.jwt.refresh_token_expire
    else:
        raise TokenWrongTypeError

    to_encode = raw_data.copy()
    to_encode.update({"type": token_type})
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt
