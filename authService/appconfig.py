"""
Centralized application configuration management.
Loads all settings from app_config.yaml.
"""

import yaml
import os
from typing import Any, Dict, Optional


class AppConfig:
    """
    Load and manage application configuration from YAML.

    Provides centralized access to all application settings including:
    - Logging configuration (paths, formats, rotation)
    - Authentication settings (hashing, error codes, defaults)
    - User management settings
    - Migration settings
    - Framework-specific settings

    Usage:
        config = AppConfig('config/app_config.yaml')
        log_level = config.get_log_level()
        bcrypt_rounds = config.get_bcrypt_rounds()
    """

    def __init__(self, config_file: str = "config/app_config.yaml"):
        """
        Initialize AppConfig by loading YAML file.

        Args:
            config_file: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If config file does not exist
        """
        self.config_file = config_file
        self.config = self._load_yaml(config_file)

    def _load_yaml(self, file_path: str) -> dict:
        """
        Load and parse YAML configuration file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML content as dictionary

        Raises:
            FileNotFoundError: If file does not exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    # ===== Application Settings =====
    def get_app_name(self) -> str:
        """Get application name from config."""
        return self.config.get('app', {}).get('name', 'AuthService')

    def get_environment(self) -> str:
        """Get current environment (production, development, staging)."""
        return self.config.get('app', {}).get('environment', 'production')

    def get_version(self) -> str:
        """Get application version."""
        return self.config.get('app', {}).get('version', '1.0.0')

    # ===== Logging Settings =====
    def get_logging_config(self) -> dict:
        """Get entire logging configuration section."""
        return self.config.get('logging', {})

    def get_log_file(self) -> Optional[str]:
        """Get path to general application log file."""
        return self.get_logging_config().get('general', {}).get('file')

    def get_log_level(self) -> str:
        """Get logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        return self.get_logging_config().get('general', {}).get('level', 'INFO')

    def get_log_format(self) -> str:
        """Get log message format string."""
        return self.get_logging_config().get('general', {}).get(
            'format',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def get_log_date_format(self) -> str:
        """Get date format for log timestamps."""
        return self.get_logging_config().get('general', {}).get(
            'date_format',
            '%Y-%m-%d %H:%M:%S'
        )

    def get_log_max_bytes(self) -> int:
        """Get maximum size of log file before rotation (in bytes)."""
        return self.get_logging_config().get('general', {}).get('max_bytes', 5242880)

    def get_log_backup_count(self) -> int:
        """Get number of backup log files to keep."""
        return self.get_logging_config().get('general', {}).get('backup_count', 3)

    def get_audit_log_file(self) -> Optional[str]:
        """Get path to audit log file (returns None if audit logging disabled)."""
        audit_cfg = self.get_logging_config().get('audit', {})
        if audit_cfg.get('enabled', False):
            return audit_cfg.get('file')
        return None

    def get_audit_log_format(self) -> str:
        """Get audit log message format string."""
        return self.get_logging_config().get('audit', {}).get(
            'format',
            '[AUDIT] %(asctime)s - %(message)s'
        )

    def get_audit_log_max_bytes(self) -> int:
        """Get maximum size of audit log file before rotation (in bytes)."""
        return self.get_logging_config().get('audit', {}).get('max_bytes', 5242880)

    def get_audit_log_backup_count(self) -> int:
        """Get number of backup audit log files to keep."""
        return self.get_logging_config().get('audit', {}).get('backup_count', 5)

    # ===== Authentication Settings =====
    def get_auth_config(self) -> dict:
        """Get entire authentication configuration section."""
        return self.config.get('auth', {})

    def use_hashing(self) -> bool:
        """Check if password hashing is enabled."""
        return self.get_auth_config().get('hashing', {}).get('enabled', True)

    def get_bcrypt_rounds(self) -> int:
        """Get number of bcrypt salt rounds (10-13 recommended)."""
        return self.get_auth_config().get('hashing', {}).get('bcrypt_rounds', 12)

    def get_hashing_algorithm(self) -> str:
        """Get hashing algorithm (bcrypt, argon2, etc.)."""
        return self.get_auth_config().get('hashing', {}).get('algorithm', 'bcrypt')

    def get_default_ip_address(self) -> str:
        """Get default IP address for logging when not provided."""
        return self.get_auth_config().get('defaults', {}).get('ip_address', 'unknown')

    def get_default_by_whom(self) -> str:
        """Get default 'by_whom' value for audit logging."""
        return self.get_auth_config().get('defaults', {}).get('by_whom', 'system')

    def get_default_user_role(self) -> str:
        """Get default role for new users."""
        return self.get_auth_config().get('defaults', {}).get('user_role', 'user')

    def get_default_user_is_active(self) -> bool:
        """Get default is_active status for new users."""
        return self.get_auth_config().get('defaults', {}).get('user_is_active', True)

    def get_session_timeout(self) -> int:
        """Get session timeout in seconds."""
        return self.get_auth_config().get('session', {}).get('timeout', 3600)

    def require_https(self) -> bool:
        """Check if HTTPS is required."""
        return self.get_auth_config().get('session', {}).get('require_https', True)

    # ===== Error Codes =====
    def get_error_code(self, error_type: str) -> str:
        """
        Get error code for a given error type.

        Args:
            error_type: Type of error (e.g., 'user_not_found')

        Returns:
            Error code string (e.g., 'USER_NOT_FOUND')
        """
        error_codes = self.config.get('error_codes', {})
        return error_codes.get(error_type, error_type.upper())

    # ===== Migration Settings =====
    def get_migration_config(self) -> dict:
        """Get entire migration configuration section."""
        return self.config.get('migration', {})

    def get_migration_backup_enabled(self) -> bool:
        """Check if backup files should be created during migration."""
        return self.get_migration_config().get('create_backup', True)

    def get_migration_backup_extension(self) -> str:
        """Get file extension for backup files (e.g., '.bak')."""
        return self.get_migration_config().get('backup_extension', '.bak')

    def get_migration_reserved_keys(self) -> list:
        """Get list of reserved configuration keys (not treated as usernames)."""
        return self.get_migration_config().get('reserved_keys', [])

    # ===== User Management =====
    def get_users_config_file(self) -> str:
        """Get path to users.yaml configuration file."""
        return self.config.get('users', {}).get('config_file', 'config/users.yaml')

    def get_users_auto_load(self) -> bool:
        """Check if users should be automatically loaded on init."""
        return self.config.get('users', {}).get('auto_load', True)

    # ===== Security Policy =====
    def get_security_config(self) -> dict:
        """Get entire security configuration section."""
        return self.config.get('security', {})

    def get_password_policy(self) -> dict:
        """Get password policy settings."""
        return self.get_security_config().get('password_policy', {})

    def get_rate_limiting_config(self) -> dict:
        """Get rate limiting settings."""
        return self.get_security_config().get('rate_limiting', {})

    def is_rate_limiting_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.get_rate_limiting_config().get('enabled', False)

    def get_rate_limit_max_attempts(self) -> int:
        """Get maximum authentication attempts allowed."""
        return self.get_rate_limiting_config().get('max_attempts', 5)

    def get_rate_limit_window(self) -> int:
        """Get rate limiting time window in seconds."""
        return self.get_rate_limiting_config().get('window_seconds', 300)

    # ===== Framework Settings =====
    def get_framework_config(self, framework: str) -> dict:
        """
        Get configuration for a specific framework.

        Args:
            framework: Framework name (flask, django, express, spring)

        Returns:
            Framework-specific configuration dictionary
        """
        frameworks = self.config.get('frameworks', {})
        return frameworks.get(framework, {})

    def __repr__(self) -> str:
        return f"<AppConfig from '{self.config_file}'>"
