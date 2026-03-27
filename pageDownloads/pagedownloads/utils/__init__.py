from .config_loader import config
from .logger import setup_logger
from .browser_setup import ensure_browser_available
from .duplicate_detector import detect_and_remove_duplicates

__all__ = ['config', 'setup_logger', 'ensure_browser_available', 'detect_and_remove_duplicates']
