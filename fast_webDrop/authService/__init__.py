"""
AuthTemplate - Reusable Authentication Module
A framework-agnostic authentication system that can be easily integrated into any project.
"""

__version__ = "1.0.0"
__author__ = "Your Organization"

try:
    from .core import AuthManager
    from .models import User
    from .config import AuthConfig
    from .logger import setup_logger
except ImportError:
    from core import AuthManager
    from models import User
    from config import AuthConfig
    from logger import setup_logger

__all__ = ['AuthManager', 'User', 'AuthConfig', 'setup_logger']
