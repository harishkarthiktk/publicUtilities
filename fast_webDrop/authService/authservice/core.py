"""
Core authentication logic.
Framework-agnostic authentication manager that handles credential verification.
"""

import base64
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from authservice.models import User, AuthResult
from authservice.config import AuthConfig
from authservice.logger import setup_logger, setup_logger_from_config, AuthLogger
from authservice.hashing import hash_password, verify_password, is_bcrypt_hash
from authservice.appconfig import AppConfig

# Dummy hash for constant-time comparison (prevents timing attacks)
# This is a bcrypt hash of an empty string
DUMMY_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oDzS.W9H8wCi"


class AuthManager:
    """
    Framework-agnostic authentication manager.

    Handles:
    - Credential verification
    - User loading and validation
    - Authentication attempt logging
    - Session/token validation (if needed)

    Usage:
        config = AuthConfig(yaml_file='users.yaml')
        auth_manager = AuthManager(config)
        result = auth_manager.verify_credentials('username', 'password')
    """

    def __init__(
        self,
        config: AuthConfig,
        logger: Optional[AuthLogger] = None,
        hash_function: Optional[callable] = None,
        use_hashing: bool = True,
        app_config: Optional[AppConfig] = None
    ):
        """
        Initialize authentication manager.

        Args:
            config: AuthConfig instance with user configuration
            logger: AuthLogger instance (creates default if not provided)
            hash_function: Function to verify hashed passwords
                          (for bcrypt, Argon2, etc.)
            use_hashing: If True, use built-in bcrypt hashing (deprecated parameter)
            app_config: AppConfig instance with centralized settings (optional)
        """
        self.config = config
        self.hash_function = hash_function
        self.app_config = app_config

        # Deprecate use_hashing parameter
        if use_hashing is False:
            import warnings
            warnings.warn(
                "use_hashing parameter is deprecated and will be ignored. "
                "Passwords are always hashed for security.",
                DeprecationWarning,
                stacklevel=2
            )
        self.use_hashing = use_hashing

        self.config.validate()

        # Set up logging
        if logger:
            self.logger = logger
        else:
            # setup_logger now returns an AuthLogger directly
            if app_config:
                self.logger = setup_logger_from_config(app_config)
            else:
                self.logger = setup_logger("AuthManager")

        # Load users from config
        self.users = self.config.get_users()
        self.logger.log_config_loaded(len(self.users), "AuthConfig")

    @staticmethod
    def from_config(app_config: AppConfig) -> "AuthManager":
        """
        Create AuthManager from centralized application config.

        Initializes AuthManager with all settings loaded from AppConfig,
        including user configuration, logger settings, and hashing options.

        Args:
            app_config: AppConfig instance with loaded configuration

        Returns:
            Configured AuthManager instance

        Raises:
            FileNotFoundError: If config files do not exist
        """
        # Load user configuration
        user_config = AuthConfig(yaml_file=app_config.get_users_config_file())

        # Setup logger from config
        logger = setup_logger_from_config(app_config)

        # Create auth manager with all config settings
        return AuthManager(
            config=user_config,
            logger=logger,
            use_hashing=app_config.use_hashing(),
            app_config=app_config
        )

    def verify_credentials(
        self,
        username: str,
        password: str,
        ip_address: str = "unknown"
    ) -> AuthResult:
        """
        Verify user credentials.

        Args:
            username: Username to authenticate
            password: Password to verify
            ip_address: IP address of the request (for logging)

        Returns:
            AuthResult with user object if successful, error info if failed
        """
        try:
            # Always perform password verification to prevent timing attacks
            # Use dummy hash if user doesn't exist to maintain constant time
            stored_password = self.users.get(username, DUMMY_HASH)

            # If hash function provided, use it; otherwise use built-in comparison
            if self.hash_function:
                password_valid = self.hash_function(password, stored_password)
            else:
                password_valid = self._compare_passwords(password, stored_password)

            # Check if user exists AND password is valid
            user_exists = username in self.users

            if not user_exists or not password_valid:
                self.logger.log_invalid_credentials(username, ip_address, len(password))
                return AuthResult(
                    success=False,
                    message="Invalid credentials",
                    error_code="INVALID_CREDENTIALS"
                )

            # Get user metadata and check if account is active
            user_meta = self.config.get_user_metadata(username)
            if not user_meta.get('is_active', True):
                self.logger.log_auth_attempt(username, ip_address, False, "USER_DISABLED")
                return AuthResult(
                    success=False,
                    message="Account is disabled",
                    error_code="USER_DISABLED"
                )

            # Create fully populated user object
            user = User(
                username=username,
                email=user_meta.get('email'),
                is_active=user_meta.get('is_active', True),
                roles=user_meta.get('roles', ['user']),
                metadata=user_meta.get('metadata', {}),
                last_login=datetime.now()
            )

            self.logger.log_auth_attempt(username, ip_address, True)
            return AuthResult(
                success=True,
                user=user,
                message="Authentication successful"
            )

        except Exception as e:
            self.logger.log_error(f"Error during authentication", e)
            return AuthResult(
                success=False,
                message="Authentication error",
                error_code="AUTH_ERROR"
            )

    def verify_basic_auth_header(
        self,
        auth_header: str,
        ip_address: str = "unknown"
    ) -> AuthResult:
        """
        Verify HTTP Basic Authentication header.

        Expects header in format: "Basic base64(username:password)"

        Args:
            auth_header: Authorization header value
            ip_address: IP address of the request

        Returns:
            AuthResult with user object if successful, error info if failed
        """
        try:
            if not auth_header.startswith("Basic "):
                return AuthResult(
                    success=False,
                    message="Invalid authorization header format",
                    error_code="INVALID_HEADER"
                )

            # Decode basic auth
            encoded = auth_header[6:]  # Remove "Basic " prefix
            try:
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)
            except (ValueError, UnicodeDecodeError):
                return AuthResult(
                    success=False,
                    message="Invalid base64 encoding in authorization header",
                    error_code="INVALID_ENCODING"
                )

            # Verify credentials
            return self.verify_credentials(username, password, ip_address)

        except Exception as e:
            self.logger.log_error(f"Error parsing basic auth header", e)
            return AuthResult(
                success=False,
                message="Error parsing authorization header",
                error_code="HEADER_PARSE_ERROR"
            )

    def _compare_passwords(self, provided: str, stored: str) -> bool:
        """
        Compare passwords using bcrypt verification.

        Requires passwords to be stored as bcrypt hashes. Plaintext passwords
        are rejected with a clear error message.

        Args:
            provided: Password provided by user
            stored: Bcrypt hash stored in system

        Returns:
            True if the password matches the hash, False otherwise
        """
        # Require bcrypt hash format
        if not is_bcrypt_hash(stored):
            self.logger.log_error(
                f"Plaintext password detected for verification. Run migration script: python scripts/migrate_passwords.py"
            )
            return False

        return verify_password(provided, stored)

    def reload_users(self) -> None:
        """Reload users from configuration source."""
        self.config.reload()
        self.users = self.config.get_users()
        self.logger.log_config_loaded(len(self.users), "AuthConfig (reloaded)")

    def add_user(
        self,
        username: str,
        password: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> bool:
        """
        Add a user to the in-memory configuration.

        Passwords are automatically hashed using bcrypt for security.
        Note: This does not persist to YAML or database.

        Args:
            username: Username to add
            password: Password for the user
            by_whom: Who is performing this action (for audit logging)
            ip_address: IP address of the request (for audit logging)

        Returns:
            True if user added successfully, False if user already exists
        """
        if username in self.users:
            return False

        # Always hash password for security (unless already hashed)
        if not is_bcrypt_hash(password):
            password = hash_password(password)

        self.users[username] = password

        # Log the audit event
        self.logger.log_user_added(username, by_whom, ip_address)

        return True

    def change_password(
        self,
        username: str,
        new_password: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> bool:
        """
        Change user password with audit logging.

        Note: This does not persist to YAML or database.

        Args:
            username: Username whose password to change
            new_password: New password for the user
            by_whom: Who is performing this action (for audit logging)
            ip_address: IP address of the request (for audit logging)

        Returns:
            True if password changed successfully, False if user doesn't exist
        """
        if username not in self.users:
            return False

        # Hash new password (unless already hashed)
        if not is_bcrypt_hash(new_password):
            hashed = hash_password(new_password)
        else:
            hashed = new_password

        self.users[username] = hashed

        # Audit log - using log_user_added as placeholder
        # Note: logger might not have log_password_changed method yet
        try:
            self.logger.log_password_changed(username, by_whom, ip_address)
        except AttributeError:
            # Fallback to generic audit log if method doesn't exist
            self.logger.log_audit_event(
                f"PASSWORD_CHANGED",
                username,
                {"changed_by": by_whom, "ip_address": ip_address}
            )

        return True

    def remove_user(
        self,
        username: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> bool:
        """
        Remove a user from the in-memory configuration.

        Note: This does not persist to YAML or database.

        Args:
            username: Username to remove
            by_whom: Who is performing this action (for audit logging)
            ip_address: IP address of the request (for audit logging)

        Returns:
            True if user removed, False if user doesn't exist
        """
        if username not in self.users:
            return False

        del self.users[username]

        # Log the audit event
        self.logger.log_user_removed(username, by_whom, ip_address)

        return True

    def persist_changes(self) -> None:
        """
        Persist in-memory user changes to YAML file.

        Writes current users and metadata back to the YAML configuration file.

        Raises:
            ValueError: If no YAML file is configured
        """
        # Sync in-memory users back to config before saving
        self.config.set_users(self.users)
        self.config.save_users()

    def list_users(self) -> list:
        """Get list of all configured usernames."""
        return list(self.users.keys())

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a user.

        Args:
            username: Username to look up

        Returns:
            User info dict or None if user doesn't exist
        """
        if username not in self.users:
            return None

        return {
            'username': username,
            'exists': True,
            'is_active': True
        }

    def __repr__(self) -> str:
        return f"<AuthManager with {len(self.users)} users>"
