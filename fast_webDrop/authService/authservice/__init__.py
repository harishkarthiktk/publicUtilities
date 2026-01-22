"""
AuthService - Framework-Agnostic Authentication Library
A production-ready authentication system that can be easily integrated into any Python project.
"""

__version__ = "1.0.0"
__author__ = "AuthService Contributors"

from authservice.core import AuthManager
from authservice.models import User, AuthResult
from authservice.config import AuthConfig
from authservice.logger import setup_logger, setup_logger_from_config, AuthLogger
from authservice.hashing import hash_password, verify_password, is_bcrypt_hash, migrate_yaml_file
from authservice.appconfig import AppConfig

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
