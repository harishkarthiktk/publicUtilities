"""
Logging setup for authentication system.
Provides standardized logging for auth events.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "AuthTemplate",
    log_file: Optional[str] = None,
    level: str = "INFO",
    max_bytes: int = 5242880,  # 5MB
    backup_count: int = 3,
    audit_log_file: Optional[str] = None
) -> "AuthLogger":
    """
    Set up a logger for the authentication system.

    Args:
        name: Logger name
        log_file: Path to log file (if None, logs to console only)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        audit_log_file: Optional separate file for audit logs

    Returns:
        Configured AuthLogger instance with audit support
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file provided)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")

    # Audit log handler (if audit_log_file provided)
    audit_handler = None
    if audit_log_file:
        try:
            audit_path = Path(audit_log_file)
            audit_path.parent.mkdir(parents=True, exist_ok=True)

            audit_formatter = logging.Formatter(
                '[AUDIT] %(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            audit_handler = logging.handlers.RotatingFileHandler(
                audit_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            audit_handler.setFormatter(audit_formatter)
            audit_handler.setLevel(logging.INFO)
        except Exception as e:
            logger.warning(f"Could not set up audit logging: {e}")

    return AuthLogger(logger, audit_handler)


class AuthLogger:
    """
    Specialized logger for authentication events.
    Provides convenient methods for common auth operations.
    """

    def __init__(self, logger: logging.Logger, audit_handler: Optional[logging.Handler] = None):
        """
        Initialize with a logger instance.

        Args:
            logger: The logging.Logger instance to use
            audit_handler: Optional handler for audit logs
        """
        self.logger = logger
        self.audit_handler = audit_handler

    def log_auth_attempt(self, username: str, ip_address: str, success: bool, error_code: Optional[str] = None) -> None:
        """
        Log an authentication attempt.

        Args:
            username: Username attempting to authenticate
            ip_address: IP address of the requester
            success: Whether authentication was successful
            error_code: Error code if authentication failed
        """
        status = "SUCCESS" if success else f"FAILED ({error_code})"
        self.logger.info(
            f"Auth attempt: user={username}, ip={ip_address}, status={status}"
        )

    def log_invalid_credentials(self, username: str, ip_address: str, password_length: int = 0) -> None:
        """
        Log invalid credentials attempt.

        Args:
            username: Username with invalid credentials
            ip_address: IP address of the requester
            password_length: Length of password (not the password itself)
        """
        self.logger.warning(
            f"Invalid credentials: user={username}, ip={ip_address}, pwd_len={password_length}"
        )

    def log_user_not_found(self, username: str, ip_address: str) -> None:
        """
        Log when user is not found.

        Args:
            username: Username that was not found
            ip_address: IP address of the requester
        """
        self.logger.warning(
            f"User not found: user={username}, ip={ip_address}"
        )

    def log_config_loaded(self, user_count: int, source: str) -> None:
        """
        Log configuration load event.

        Args:
            user_count: Number of users loaded
            source: Source of configuration (YAML, ENV, etc.)
        """
        self.logger.info(f"Auth config loaded: {user_count} users from {source}")

    def log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        Log authentication error.

        Args:
            message: Error message
            exception: Exception object (optional)
        """
        if exception:
            self.logger.error(f"{message}: {exception}", exc_info=True)
        else:
            self.logger.error(message)

    def _log_audit(self, message: str) -> None:
        """
        Internal method to log audit events to both audit handler and main logger.

        Args:
            message: Audit message to log
        """
        if self.audit_handler:
            # Create a temporary logger for audit events
            audit_logger = logging.getLogger(f"{self.logger.name}.audit")
            audit_logger.handlers = []
            audit_logger.addHandler(self.audit_handler)
            audit_logger.setLevel(logging.INFO)
            audit_logger.info(message)
        else:
            # Fallback to main logger if no audit handler
            self.logger.info(message)

    def log_user_added(
        self,
        username: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> None:
        """
        Log user addition event to audit log.

        Args:
            username: Username that was added
            by_whom: Who performed this action
            ip_address: IP address of the request
        """
        message = f"USER_ADDED: username={username}, by={by_whom}, ip={ip_address}"
        self._log_audit(message)

    def log_user_removed(
        self,
        username: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> None:
        """
        Log user removal event to audit log.

        Args:
            username: Username that was removed
            by_whom: Who performed this action
            ip_address: IP address of the request
        """
        message = f"USER_REMOVED: username={username}, by={by_whom}, ip={ip_address}"
        self._log_audit(message)

    def log_user_modified(
        self,
        username: str,
        field_changed: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> None:
        """
        Log user modification event to audit log.

        Args:
            username: Username that was modified
            field_changed: Field that was changed
            by_whom: Who performed this action
            ip_address: IP address of the request
        """
        message = f"USER_MODIFIED: username={username}, field={field_changed}, by={by_whom}, ip={ip_address}"
        self._log_audit(message)

    def log_password_changed(
        self,
        username: str,
        by_whom: str = "system",
        ip_address: str = "unknown"
    ) -> None:
        """
        Log password change event to audit log.

        Args:
            username: Username whose password was changed
            by_whom: Who performed this action
            ip_address: IP address of the request
        """
        message = f"PASSWORD_CHANGED: username={username}, by={by_whom}, ip={ip_address}"
        self._log_audit(message)
