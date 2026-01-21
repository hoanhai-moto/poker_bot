import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "poker_bot",
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True
) -> logging.Logger:
    """
    Setup and configure a logger.

    Args:
        name: Logger name
        level: Logging level
        log_dir: Directory for log files
        console: Enable console output
        file: Enable file output

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file:
        log_dir = log_dir or Path("./logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "poker_bot") -> logging.Logger:
    """
    Get an existing logger or create a new one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If no handlers, set up with defaults
    if not logger.handlers:
        return setup_logger(name)

    return logger


class LoggerAdapter:
    """Adapter to add context to log messages."""

    def __init__(self, logger: logging.Logger, prefix: str = ""):
        self._logger = logger
        self._prefix = prefix

    def _format_message(self, message: str) -> str:
        if self._prefix:
            return f"[{self._prefix}] {message}"
        return message

    def debug(self, message: str):
        self._logger.debug(self._format_message(message))

    def info(self, message: str):
        self._logger.info(self._format_message(message))

    def warning(self, message: str):
        self._logger.warning(self._format_message(message))

    def error(self, message: str):
        self._logger.error(self._format_message(message))

    def critical(self, message: str):
        self._logger.critical(self._format_message(message))
