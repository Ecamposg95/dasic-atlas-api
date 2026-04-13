"""
Structured logging configuration for DASIC ERP.
Call configure_logging() once at application startup.
"""

import logging
import logging.config
import os


def configure_logging() -> None:
    """Configure structured console logging from LOG_LEVEL env var."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "structured",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": log_level,
            },
        }
    )
