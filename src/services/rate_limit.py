from src.core.config import settings
from src.exceptions.common import WrongParams
from src.repositories.base.rate_limit import BaseRateLimitRepository
from src.utils.encryption import hash_user_data


class RateLimitService:
    def __init__(
            self,
            rate_limit_repository: BaseRateLimitRepository,
    ) -> None:
        self.rate_limit_repository = rate_limit_repository

        self.ttl_by_operation: dict[str, dict[str, int]] = {
            "login": {
                "fail": settings.rate_limit.login_failed_window_seconds,
                "lock": settings.rate_limit.login_lock_duration_seconds,
            },
        }

    async def is_operation_allowed(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> tuple[bool, int]:
        """returns False and TTL if operation is not allowed, else - True and -1"""

        if email is None and phone is None:
            raise WrongParams([email, phone])

        params = {
            "operation": operation,
            "kind": "lock"
        }

        if email is not None:
            is_lock = await self.rate_limit_repository.is_exists(
                identifier_hash=hash_user_data(email),
                **params,
            )
            if is_lock:
                ttl = await self.rate_limit_repository.get_ttl(
                    identifier_hash=hash_user_data(email),
                    **params,
                )
                return False, ttl

        if phone is not None:
            is_lock = await self.rate_limit_repository.is_exists(
                identifier_hash=hash_user_data(phone),
                **params,
            )
            if is_lock:
                ttl = await self.rate_limit_repository.get_ttl(
                    identifier_hash=hash_user_data(phone),
                    **params,
                )
                return False, ttl

        return True, -1

    async def increment_login_failure(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> int:
        """returns the final count"""

        if email is None and phone is None:
            raise WrongParams([email, phone])

        kind = "fail"
        expires_in = self._get_expires_in_by_params(
            operation=operation,
            kind=kind,
        )

        email_fails_count = 0
        phone_fails_count = 0
        if email is not None:
            email_fails_count = await self.rate_limit_repository.increment_counter(
                identifier_hash=hash_user_data(email),
                kind=kind,
                operation=operation,
                expires_in_only_after_first_increment=expires_in,
            )
        if phone is not None:
            phone_fails_count = await self.rate_limit_repository.increment_counter(
                identifier_hash=hash_user_data(phone),
                kind=kind,
                operation=operation,
                expires_in_only_after_first_increment=expires_in,
            )

        return max(email_fails_count, phone_fails_count)

    async def record_login_success(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> None:
        if email is None and phone is None:
            raise WrongParams([email, phone])

        kind = "fail"

        if email is not None:
            await self.rate_limit_repository.delete(
                identifier_hash=hash_user_data(email),
                kind=kind,
                operation=operation,
            )
        if phone is not None:
            await self.rate_limit_repository.delete(
                identifier_hash=hash_user_data(phone),
                kind=kind,
                operation=operation,
            )

        return None

    async def lock(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> None:
        if email is None and phone is None:
            raise WrongParams([email, phone])

        kind = "lock"
        expires_in = self._get_expires_in_by_params(
            operation=operation,
            kind=kind,
        )

        if email is not None:
            await self.rate_limit_repository.lock(
                identifier_hash=hash_user_data(email),
                operation=operation,
                expires_in=expires_in,
            )
        if phone is not None:
            await self.rate_limit_repository.lock(
                identifier_hash=hash_user_data(phone),
                operation=operation,
                expires_in=expires_in,
            )

    def _get_expires_in_by_params(self, operation: str, kind: str) -> int:
        operation_settings = self.ttl_by_operation.get(operation)
        if operation_settings is None:
            raise WrongParams([operation])
        expires_in = operation_settings.get(kind)
        if expires_in is None:
            raise WrongParams([operation, kind])

        return expires_in
