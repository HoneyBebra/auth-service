import logging
from typing import Any


# TODO: Convert to pydantic-settings (?)
class Events:
    rate_limit_login_failed: dict[str, str | int] = {
        "name": "rate_limit.login_failed",
        "level": logging.INFO,
    }
    rate_limit_login_locked: dict[str, str | int] = {
        "name": "rate_limit.login_locked",
        "level": logging.WARNING,
    }
    rate_limit_login_success_reset: dict[str, str | int] = {
        "name": "rate_limit.login_success_reset",
        "level": logging.INFO,
    }


def log_event(
        logger: logging.Logger,
        level: int,
        event: str,
        message: str | None = None,
        **fields: Any,
) -> None:
    """
    Write one structured log line

    :param logger: Target logger, usually ``logging.getLogger(__name__)`` for the
        calling module
    :param level: Standard ``logging`` level constant
    :param event: Stable machine-readable event name used for filtering and alerts
        Convention: dotted lowercase identifier, e.g. ``rate_limit.login_failed``,
        ``rate_limit.login_locked``. Emitted as top-level JSON key ``event``
    :param message: Human-readable log text stored in the ``message`` field
    :param fields: Arbitrary context merged into the JSON payload as top-level keys

        Common examples for rate limiting:

        - ``identifier_hash`` — hashed email or phone (required for limit events).
        - ``attempt_count`` — current fail counter after increment.
        - ``lock_duration`` — lock TTL in seconds from settings.
        - ``operation`` — rate-limit scope, e.g. ``"login"``.

    :returns: ``None``.
    """
    logger.log(
        level=level,
        msg=message,
        extra={"event": event, **fields},
    )
