"""Logging configuration for NYC Taxi Data Engineering pipeline."""

import logging
import sys
from pathlib import Path
from src.utils.config import settings


def get_logger(name: str = "nyc_taxi_pipeline") -> logging.Logger:
    """Create and configure a standardized logger instance.

    Args:
        name: The name of the module or component requesting the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File Handler
    try:
        log_file: Path = settings.LOG_FILE
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as e:
        console_handler.emit(
            logging.LogRecord(
                name=name,
                level=logging.WARNING,
                pathname=__file__,
                lineno=42,
                msg=f"Could not initialize log file handler: {e}",
                args=(),
                exc_info=None,
            )
        )

    return logger
