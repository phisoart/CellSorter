"""
CellSorter Logging Configuration

This module sets up application-wide logging configuration.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from config.settings import (
    LOG_LEVEL, LOG_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT, BASE_DIR
)


def setup_logging(log_file: Optional[str] = None, console_level: str = "INFO") -> logging.Logger:
    """
    Set up application logging with file and console handlers.
    
    Args:
        log_file: Optional custom log file path
        console_level: Console logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Default log file path
    if log_file is None:
        log_file = log_dir / "cellsorter.log"
    
    # Create root logger
    logger = logging.getLogger("cellsorter")
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"cellsorter.{name}")


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message with optional context."""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional context."""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs) -> None:
        """Log error message with optional context."""
        self.logger.error(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional context."""
        self.logger.debug(message, extra=kwargs)