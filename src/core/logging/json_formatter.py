import logging
from datetime import UTC, datetime
from typing import Any

import orjson

from src.core.config import settings

_LOG_RECORD_BUILTIN_ATTRS = frozenset(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for log collectors (Loki, ELK, etc.)."""

    def __init__(self) -> None:
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": settings.app.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_BUILTIN_ATTRS or key.startswith("_"):
                continue
            payload[key] = value

        return orjson.dumps(payload).decode()
