from typing import Literal

from fastapi import Cookie, Depends, HTTPException, status

from src.core.config import settings
from src.dependencies.services import get_token_validator
from src.exceptions.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
    TokenRevokedError,
    TokenWrongTypeError,
)
from src.schemas.v1.jwt import UserJwtSchema
from src.services.jwt import TokenValidator


async def get_access_token_data(
    access_token: str | None = Cookie(default=None, alias=settings.access_token_key_in_cookie),
    token_validator: TokenValidator = Depends(get_token_validator),
) -> tuple[UserJwtSchema, str]:
    return await _validate(access_token, "access", token_validator)


async def get_refresh_token_data(
    refresh_token: str | None = Cookie(default=None, alias=settings.refresh_token_key_in_cookie),
    token_validator: TokenValidator = Depends(get_token_validator),
) -> tuple[UserJwtSchema, str]:
    return await _validate(refresh_token, "refresh", token_validator)


async def _validate(
    raw_token: str | None,
    expected_type: Literal["access", "refresh"],
    token_validator: TokenValidator,
) -> tuple[UserJwtSchema, str]:
    try:
        return await token_validator.validate(raw_token, expected_type)
    except TokenMissingError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except TokenExpiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except TokenRevokedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except TokenWrongTypeError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
    except TokenInvalidError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e
