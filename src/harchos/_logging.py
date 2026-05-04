"""Logging configuration for the HarchOS SDK."""

from __future__ import annotations

import logging
import sys
from typing import Optional

LOGGER_NAME = "harchos"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger for the HarchOS SDK.

    Args:
        name: Optional child logger name (e.g. "http", "retry").

    Returns:
        A :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if name:
        logger = logger.getChild(name)
    return logger


def configure_logging(
    level: int = logging.WARNING,
    format_string: Optional[str] = None,
    handler: Optional[logging.Handler] = None,
) -> None:
    """Configure the HarchOS SDK logger.

    Args:
        level: Logging level (default: WARNING).
        format_string: Custom format string.
        handler: Custom handler (default: StreamHandler to stderr).
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    if not handler:
        handler = logging.StreamHandler(sys.stderr)

    if format_string:
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    logger.addHandler(handler)
