LOG_DEFAULT_HANDLERS = ["console"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "src.core.logging.json_formatter.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": LOG_DEFAULT_HANDLERS,
    },
}
