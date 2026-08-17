import logging

from src.core.config import settings
from src.core.logging.events import Event, Events, log_event
from src.exceptions.common import WrongParams
from src.repositories.base.rate_limit import BaseRateLimitRepository
from src.utils.encryption import hash_user_data

logger = logging.getLogger(__name__)


class RateLimitService:
    """Rate limiting by email/phone hash (fail counters and temporary locks)."""

    def __init__(
        self,
        rate_limit_repository: BaseRateLimitRepository,
    ) -> None:
        """
        :param rate_limit_repository: storage for fail counters and lock keys.
        """
        self.rate_limit_repository = rate_limit_repository

        self.ttl_by_operation: dict[str, dict[str, int]] = {
            "login": {
                "fail": settings.rate_limit.login_failed_window_seconds,
                "lock": settings.rate_limit.login_lock_duration_seconds,
            },
        }

        self.event_by_operation: dict[str, dict[str, Event]] = {
            "login": {
                "fail": Events.rate_limit_login_failed,
                "lock": Events.rate_limit_login_locked,
                "success": Events.rate_limit_login_success_reset,
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

        Looks up the lock key per identifier (OR semantics: email first, then phone).

        :param operation: Rate-limit scope, e.g. ``"login"``.
        :param email: Plain email; hashed before lookup. Optional if ``phone`` is set.
        :param phone: Plain phone; hashed before lookup. Optional if ``email`` is set.
        :returns: ``(True, -1)`` when no lock is active; ``(False, ttl)`` when locked
            and ``ttl`` is the lock TTL in seconds (for ``Retry-After``).
        :raises WrongParams: Neither ``email`` nor ``phone`` was provided.
        """
        if email is None and phone is None:
            raise WrongParams([email, phone])

        params = {"operation": operation, "kind": "lock"}

        identifier_data = self._get_identifier_not_none_data(email, phone)
        for identifier in identifier_data:
            identifier_hash = hash_user_data(identifier)
            is_lock = await self.rate_limit_repository.is_exists(
                identifier_hash=identifier_hash,
                **params,
            )
            if is_lock:
                ttl = await self.rate_limit_repository.get_ttl(
                    identifier_hash=identifier_hash,
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
        Record a failed attempt and bump the fail counter.

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
        event_name, event_log_level = self._get_event_name_and_log_level_by_params(
            operation=operation,
            event_key=kind,
        )

        expires_in = self._get_expires_in_by_params(
            operation=operation,
            kind=kind,
        )

        identifier_data = self._get_identifier_not_none_data(email, phone)

        fails_counts = []

        for identifier in identifier_data:
            identifier_hash = hash_user_data(identifier)
            fails_count = await self.rate_limit_repository.increment_counter(
                identifier_hash=identifier_hash,
                kind=kind,
                operation=operation,
                expires_in_only_after_first_increment=expires_in,
            )
            fails_counts.append(fails_count)
            log_event(
                logger=logger,
                level=event_log_level,
                event=event_name,
                identifier_hash=identifier_hash,
                attempt_count=fails_count,
                operation=operation,
            )

        return max(fails_counts)

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
        event_name, event_log_level = self._get_event_name_and_log_level_by_params(
            operation=operation,
            event_key="success",
        )

        identifier_data = self._get_identifier_not_none_data(email, phone)

        for identifier in identifier_data:
            identifier_hash = hash_user_data(identifier)
            await self.rate_limit_repository.delete(
                identifier_hash=identifier_hash,
                kind=kind,
                operation=operation,
            )
            log_event(
                logger=logger,
                level=event_log_level,
                event=event_name,
                identifier_hash=identifier_hash,
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
        event_name, event_log_level = self._get_event_name_and_log_level_by_params(
            operation=operation,
            event_key=kind,
        )

        expires_in = self._get_expires_in_by_params(
            operation=operation,
            kind=kind,
        )

        identifier_data = self._get_identifier_not_none_data(email, phone)

        ttl = None

        for identifier in identifier_data:
            identifier_hash = hash_user_data(identifier)
            await self.rate_limit_repository.lock(
                identifier_hash=identifier_hash,
                operation=operation,
                expires_in=expires_in,
            )
            ttl = await self.rate_limit_repository.get_ttl(
                identifier_hash=identifier_hash,
                kind=kind,
                operation=operation,
            )
            log_event(
                logger=logger,
                level=event_log_level,
                event=event_name,
                identifier_hash=identifier_hash,
                lock_duration=expires_in,
                operation=operation,
            )

        if ttl is None:
            return 0
        return ttl

    def _get_event_name_and_log_level_by_params(
        self,
        operation: str,
        event_key: str,
    ) -> tuple[str, int]:
        operation_events = self.event_by_operation.get(operation)
        if operation_events is None:
            raise WrongParams([operation])
        event = operation_events.get(event_key)
        if event is None:
            raise WrongParams([operation, event_key])

        return event.name, event.level

    def _get_expires_in_by_params(self, operation: str, kind: str) -> int:
        """
        Resolve TTL for an operation and key kind from ``ttl_by_operation``.

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

    @staticmethod
    def _get_identifier_not_none_data(*params: str | None) -> list[str]:
        identifier_data = []

        for param in params:
            if param is not None:
                identifier_data.append(param)

        return identifier_data
