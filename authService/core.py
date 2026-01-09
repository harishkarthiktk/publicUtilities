"""
Core authentication logic.
Framework-agnostic authentication manager that handles credential verification.
"""

import base64
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

# Handle both relative and absolute imports
try:
    from .models import User, AuthResult
    from .config import AuthConfig
    from .logger import setup_logger, AuthLogger
except ImportError:
    from models import User, AuthResult
    from config import AuthConfig
    from logger import setup_logger, AuthLogger


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
        hash_function: Optional[callable] = None
    ):
        """
        Initialize authentication manager.

        Args:
            config: AuthConfig instance with user configuration
            logger: AuthLogger instance (creates default if not provided)
            hash_function: Function to verify hashed passwords
                          (for bcrypt, Argon2, etc.)
        """
        self.config = config
        self.hash_function = hash_function
        self.config.validate()

        # Set up logging
        if logger:
            self.logger = logger
        else:
            default_logger = setup_logger("AuthManager")
            self.logger = AuthLogger(default_logger)

        # Load users from config
        self.users = self.config.get_users()
        self.logger.log_config_loaded(len(self.users), "AuthConfig")

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
            # Check if user exists
            if username not in self.users:
                self.logger.log_user_not_found(username, ip_address)
                return AuthResult(
                    success=False,
                    message="User not found",
                    error_code="USER_NOT_FOUND"
                )

            stored_password = self.users[username]

            # If hash function provided, use it; otherwise do plaintext comparison
            if self.hash_function:
                password_valid = self.hash_function(password, stored_password)
            else:
                password_valid = self._compare_passwords(password, stored_password)

            if not password_valid:
                self.logger.log_invalid_credentials(username, ip_address, len(password))
                return AuthResult(
                    success=False,
                    message="Invalid credentials",
                    error_code="INVALID_CREDENTIALS"
                )

            # Create user object
            user = User(
                username=username,
                is_active=True,
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
        Compare passwords (plaintext comparison).

        Note: This is insecure for production. Use bcrypt or Argon2
        for real implementations.

        Args:
            provided: Password provided by user
            stored: Password stored in system

        Returns:
            True if passwords match, False otherwise
        """
        return provided == stored

    def reload_users(self) -> None:
        """Reload users from configuration source."""
        self.config.reload()
        self.users = self.config.get_users()
        self.logger.log_config_loaded(len(self.users), "AuthConfig (reloaded)")

    def add_user(self, username: str, password: str) -> bool:
        """
        Add a user to the in-memory configuration.

        Note: This does not persist to YAML or database.

        Args:
            username: Username to add
            password: Password for the user

        Returns:
            True if user added successfully, False if user already exists
        """
        if username in self.users:
            return False

        self.users[username] = password
        return True

    def remove_user(self, username: str) -> bool:
        """
        Remove a user from the in-memory configuration.

        Note: This does not persist to YAML or database.

        Args:
            username: Username to remove

        Returns:
            True if user removed, False if user doesn't exist
        """
        if username not in self.users:
            return False

        del self.users[username]
        return True

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
