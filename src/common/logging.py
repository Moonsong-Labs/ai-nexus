"""Logging utilities."""

import logging
import os


def logger(name: str):
    """Initialize the logger."""
    log = logging.getLogger(name)

    if not log.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)

    log.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    return log
