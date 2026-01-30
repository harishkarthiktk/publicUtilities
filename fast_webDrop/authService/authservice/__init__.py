"""
AuthService - Framework-Agnostic Authentication Library
A production-ready authentication system that can be easily integrated into any Python project.
"""

__version__ = "1.0.0"
__author__ = "AuthService Contributors"

from .core import AuthManager
from .models import User, AuthResult
from .config import AuthConfig
from .logger import setup_logger, setup_logger_from_config, AuthLogger
from .hashing import hash_password, verify_password, is_bcrypt_hash, migrate_yaml_file
from .appconfig import AppConfig

__all__ = [
    'AuthManager',
    'User',
    'AuthResult',
    'AuthConfig',
    'AppConfig',
    'setup_logger',
    'setup_logger_from_config',
    'AuthLogger',
    'hash_password',
    'verify_password',
    'is_bcrypt_hash',
    'migrate_yaml_file'
]
