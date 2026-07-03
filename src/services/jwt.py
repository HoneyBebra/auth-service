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


class JwtService:
    """Validate JWT access and refresh tokens (signature, expiry, blacklist, payload)."""

    def __init__(self, jwt_token_repository: BaseJwtTokenRepository) -> None:
        """
        :param jwt_token_repository: storage for revoked tokens.
        """
        self._jwt_token_repository = jwt_token_repository

    async def validate(
        self,
        raw_token: str | None,
        expected_type: Literal["access", "refresh"],
    ) -> tuple[UserJwtSchema, str]:
        """
        Run the full token validation pipeline for protected endpoints.

        Checks presence, blacklist, signature, expiry, payload shape, and token type.

        :param raw_token: JWT string from cookie or request; ``None`` if missing.
        :param expected_type: Required token kind — ``"access"`` or ``"refresh"``.
        :returns: Parsed claims and the same raw token string (for blacklist on logout/refresh).
        :raises TokenMissingError: Token was not provided.
        :raises TokenRevokedError: Token is in the revocation blacklist.
        :raises TokenExpiredError: ``exp`` is in the past.
        :raises TokenInvalidError: Bad signature, malformed payload, or schema mismatch.
        :raises TokenWrongTypeError: ``type`` claim does not match ``expected_type``.
        """
        token = self._ensure_present(raw_token)
        await self._ensure_not_revoked(token)
        payload = self._decode(token)
        schema = self._parse(payload)
        if schema.type != expected_type:
            raise TokenWrongTypeError
        return schema, token

    @staticmethod
    def _ensure_present(token: str | None) -> str:
        """
        Reject missing credentials before any crypto or storage work.

        :param token: Raw JWT or ``None``.
        :returns: The same non-empty token string.
        :raises TokenMissingError: ``token`` is ``None``.
        """
        if token is None:
            raise TokenMissingError
        return token

    async def _ensure_not_revoked(self, token: str) -> None:
        """
        Reject tokens that were invalidated on logout or refresh rotation.

        :param token: Raw JWT to look up in the blacklist.
        :returns: ``None`` when the token is not revoked.
        :raises TokenRevokedError: Token exists in the blacklist.
        """
        if await self._jwt_token_repository.is_token_in_blacklist(token):
            raise TokenRevokedError

    @staticmethod
    def _decode(token: str) -> dict[str, Any]:
        """
        Verify signature and decode the JWT payload.

        Uses ``settings.jwt.secret_key`` and ``settings.jwt.algorithm``.

        :param token: Raw JWT string.
        :returns: Decoded claims as a plain dict.
        :raises TokenExpiredError: Signature valid but token expired.
        :raises TokenInvalidError: Invalid signature or malformed token.
        """
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
        """
        Map decoded claims to the internal JWT schema.

        :param payload: Claims returned by ``_decode``.
        :returns: Validated ``UserJwtSchema`` instance.
        :raises TokenInvalidError: Required fields missing or wrong types.
        """
        try:
            return UserJwtSchema(**payload)
        except ValidationError as e:
            raise TokenInvalidError from e
