from src.core.config import settings
from src.exceptions.common import WrongParams
from src.repositories.base.rate_limit import BaseRateLimitRepository
from src.utils.encryption import hash_user_data


class RateLimitService:
    """Rate limiting by email/phone hash in Redis (fail counters and temporary locks)."""

    def __init__(
            self,
            rate_limit_repository: BaseRateLimitRepository,
    ) -> None:
        """
        :param rate_limit_repository: Redis storage for fail counters and lock keys.
        """
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
        """
        Check whether the operation is allowed for the given identifiers.

        Looks up the Redis lock key per identifier (OR semantics: email first, then phone).

        :param operation: Rate-limit scope, e.g. ``"login"``.
        :param email: Plain email; hashed before lookup. Optional if ``phone`` is set.
        :param phone: Plain phone; hashed before lookup. Optional if ``email`` is set.
        :returns: ``(True, -1)`` when no lock is active; ``(False, ttl)`` when locked
            and ``ttl`` is the lock TTL in seconds (for ``Retry-After``).
        :raises WrongParams: Neither ``email`` nor ``phone`` was provided.
        """
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

    async def increment_operation_failure(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> int:
        """
        Record a failed attempt and bump the fail counter in Redis.

        Increments ``fail`` keys for each provided identifier; TTL is set on first increment
        in the window (see ``ttl_by_operation``).

        :param operation: Rate-limit scope, e.g. ``"login"``.
        :param email: Plain email to count against. Optional if ``phone`` is set.
        :param phone: Plain phone to count against. Optional if ``email`` is set.
        :returns: Maximum fail count across the identifiers that were incremented.
        :raises WrongParams: Unknown ``operation`` or neither identifier was provided.
        """
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

    async def record_operation_success(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> None:
        """
        Clear fail counters after a successful operation (e.g. valid login).

        Does not remove lock keys — only ``fail`` counters for provided identifiers.

        :param operation: Rate-limit scope, e.g. ``"login"``.
        :param email: Plain email whose fail counter to reset. Optional if ``phone`` is set.
        :param phone: Plain phone whose fail counter to reset. Optional if ``email`` is set.
        :returns: ``None``.
        :raises WrongParams: Neither ``email`` nor ``phone`` was provided.
        """
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

    async def lock_operation(
            self,
            operation: str,
            email: str | None = None,
            phone: str | None = None,
    ) -> int:
        """
        Set a temporary lock for the given identifiers.

        Writes ``lock`` keys with TTL from ``ttl_by_operation``. When both identifiers
        are passed, returns TTL of the last one processed (phone if both are set).

        :param operation: Rate-limit scope, e.g. ``"login"``.
        :param email: Plain email to lock. Optional if ``phone`` is set.
        :param phone: Plain phone to lock. Optional if ``email`` is set.
        :returns: Lock TTL in seconds for ``Retry-After``; ``0`` if no identifier was locked.
        :raises WrongParams: Unknown ``operation``/``kind`` or no identifier provided.
        """
        if email is None and phone is None:
            raise WrongParams([email, phone])

        kind = "lock"
        expires_in = self._get_expires_in_by_params(
            operation=operation,
            kind=kind,
        )

        ttl = None
        if email is not None:
            await self.rate_limit_repository.lock(
                identifier_hash=hash_user_data(email),
                operation=operation,
                expires_in=expires_in,
            )
            ttl = await self.rate_limit_repository.get_ttl(
                identifier_hash=hash_user_data(email),
                kind=kind,
                operation=operation,
            )
        if phone is not None:
            await self.rate_limit_repository.lock(
                identifier_hash=hash_user_data(phone),
                operation=operation,
                expires_in=expires_in,
            )
            ttl = await self.rate_limit_repository.get_ttl(
                identifier_hash=hash_user_data(phone),
                kind=kind,
                operation=operation,
            )

        if ttl is None:
            return 0
        return ttl

    def _get_expires_in_by_params(self, operation: str, kind: str) -> int:
        """
        Resolve Redis TTL for an operation and key kind from ``ttl_by_operation``.

        :param operation: Rate-limit scope, e.g. ``"login"``.
        :param kind: Key segment — ``"fail"`` (counter window) or ``"lock"`` (block duration).
        :returns: TTL in seconds.
        :raises WrongParams: ``operation`` or ``kind`` is not configured.
        """
        operation_settings = self.ttl_by_operation.get(operation)
        if operation_settings is None:
            raise WrongParams([operation])
        expires_in = operation_settings.get(kind)
        if expires_in is None:
            raise WrongParams([operation, kind])

        return expires_in
