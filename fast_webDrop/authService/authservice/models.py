"""
User model definitions for authentication system.
Framework-agnostic user representation.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """
    Represents an authenticated user in the system.

    Attributes:
        username (str): Unique identifier for the user
        email (str): User's email address (optional)
        is_active (bool): Whether the user account is active
        roles (list): List of roles assigned to user
        metadata (dict): Additional user metadata
        last_login (datetime): Timestamp of last login (optional)
    """
    username: str
    email: Optional[str] = None
    is_active: bool = True
    roles: list = field(default_factory=lambda: ["user"])
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'roles': self.roles,
            'metadata': self.metadata,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        }

    def __repr__(self) -> str:
        return f"<User {self.username} (active={self.is_active})>"


@dataclass
class AuthResult:
    """
    Result of an authentication attempt.

    Attributes:
        success (bool): Whether authentication was successful
        user (User): Authenticated user (if successful)
        message (str): Status message
        error_code (str): Error code (if failed)
    """
    success: bool
    user: Optional[User] = None
    message: str = ""
    error_code: Optional[str] = None

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else f"FAILED ({self.error_code})"
        return f"<AuthResult {status}: {self.message}>"
