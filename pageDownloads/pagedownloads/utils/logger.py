import logging
import sys
from .config_loader import config


def setup_logger(name: str = None, config_section: str = "common") -> logging.Logger:
    """
    Setup standardized logger across all tools.

    Args:
        name: Logger name (defaults to calling module)
        config_section: Config section to read logging settings from

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or __name__)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    # Load logging config
    log_level_str = config.get(config_section, 'logging.level', 'INFO')
    log_format = config.get(config_section, 'logging.format',
                            '%(asctime)s - %(levelname)s - %(message)s')
    log_file = config.get(config_section, 'logging.file', 'logs.txt')
    log_mode = config.get(config_section, 'logging.mode', 'a')

    # Set log level
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatters
    formatter = logging.Formatter(log_format)

    # File handler
    file_handler = logging.FileHandler(log_file, mode=log_mode, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
