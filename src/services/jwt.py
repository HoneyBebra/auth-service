from typing import Any, Literal

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pydantic import ValidationError

from src.core.config import settings
from src.exceptions.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
    TokenRevokedError,
    TokenWrongTypeError,
)
from src.repositories.base.jwt_token import BaseJwtTokenRepository
from src.schemas.v1.jwt import UserJwtSchema


class TokenValidator:
    def __init__(self, jwt_token_repository: BaseJwtTokenRepository) -> None:
        self._jwt_token_repository = jwt_token_repository

    async def validate(
        self,
        raw_token: str | None,
        expected_type: Literal["access", "refresh"],
    ) -> tuple[UserJwtSchema, str]:
        token = self._ensure_present(raw_token)
        await self._ensure_not_revoked(token)
        payload = self._decode(token)
        schema = self._parse(payload)
        if schema.type != expected_type:
            raise TokenWrongTypeError
        return schema, token

    @staticmethod
    def _ensure_present(token: str | None) -> str:
        if token is None:
            raise TokenMissingError
        return token

    async def _ensure_not_revoked(self, token: str) -> None:
        if await self._jwt_token_repository.is_token_in_blacklist(token):
            raise TokenRevokedError

    @staticmethod
    def _decode(token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                jwt=token,
                key=settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm],
            )
        except ExpiredSignatureError as e:
            raise TokenExpiredError from e
        except InvalidTokenError as e:
            raise TokenInvalidError(str(e)) from e

    @staticmethod
    def _parse(payload: dict[str, Any]) -> UserJwtSchema:
        try:
            return UserJwtSchema(**payload)
        except ValidationError as e:
            raise TokenInvalidError from e
