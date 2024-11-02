import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(config):
    """Set up loggers based on the configuration provided."""
    log_file = os.path.expanduser(config.get("log_file"))
    error_file = os.path.expanduser(config.get("error_file"))
    log_level = config.get("log_level", "INFO").upper()
    max_bytes = config.get("log_max_bytes", 5 * 1024 * 1024)  # Default 5MB
    backup_count = config.get("log_backup_count", 3)  # Default 3 backup files

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    os.makedirs(os.path.dirname(error_file), exist_ok=True)

    # General log configuration
    log_formatter = logging.Formatter(
        config.get("log_format", "%(asctime)s - %(levelname)s - %(message)s")
    )

    # Avoid duplicate handlers
    logger = logging.getLogger("log")
    if not logger.hasHandlers():
        logger.setLevel(log_level)
        log_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        log_handler.setFormatter(log_formatter)
        logger.addHandler(log_handler)

    # Error log configuration
    error_logger = logging.getLogger("error")
    if not error_logger.hasHandlers():
        error_logger.setLevel(logging.ERROR)
        error_handler = RotatingFileHandler(
            error_file, maxBytes=max_bytes, backupCount=backup_count
        )
        error_handler.setFormatter(log_formatter)
        error_logger.addHandler(error_handler)

    return logger, error_logger


def initialize_logging(config):
    setup_logger(config)

