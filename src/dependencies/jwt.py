from typing import Literal

from fastapi import Cookie, Depends, HTTPException, status

from src.core.config import settings
from src.dependencies.services import get_jwt_service
from src.exceptions.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
    TokenRevokedError,
    TokenWrongTypeError,
)
from src.schemas.v1.jwt import UserJwtSchema
from src.services.jwt import JwtService


async def get_raw_access_token(
    access_token: str | None = Cookie(
        default=None,
        alias=settings.jwt.access_token_key_in_cookie,
    ),
) -> str | None:
    return access_token


async def get_raw_refresh_token(
    refresh_token: str | None = Cookie(
        default=None,
        alias=settings.jwt.refresh_token_key_in_cookie,
    ),
) -> str | None:
    return refresh_token


async def get_valid_access_token_data(
    access_token: str | None = Depends(get_raw_access_token),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> tuple[UserJwtSchema, str]:
    return await _validate(access_token, "access", jwt_service)


async def get_valid_refresh_token_data(
    refresh_token: str | None = Depends(get_raw_refresh_token),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> tuple[UserJwtSchema, str]:
    return await _validate(refresh_token, "refresh", jwt_service)


async def _validate(
    raw_token: str | None,
    expected_type: Literal["access", "refresh"],
    jwt_service: JwtService,
) -> tuple[UserJwtSchema, str]:
    try:
        return await jwt_service.validate(raw_token, expected_type)
    except (
        TokenMissingError,
        TokenExpiredError,
        TokenRevokedError,
        TokenWrongTypeError,
        TokenInvalidError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message) from e
