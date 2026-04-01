"""Logging setup for the application."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
        log_format: Optional custom log format
    """
    # Remove default handler
    logger.remove()
    
    # Default format
    if log_format is None:
        log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}"
    
    # Console handler (stderr for CLI compatibility)
    logger.add(
        sys.stderr,
        level=level,
        format=log_format,
        colorize=True,
    )
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=level,
            format=log_format,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )
    
    logger.info(f"Logging initialized at level: {level}")


def get_logger(name: Optional[str] = None):
    """Get a logger instance.
    
    Args:
        name: Optional logger name for context
        
    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
