"""
Configuration loader for authentication system.
Supports YAML files, environment variables, and in-memory configuration.
"""

import os
import yaml
from typing import Dict, Optional, Any
from pathlib import Path


class AuthConfig:
    """
    Manages authentication configuration from multiple sources.

    Priority order:
    1. YAML file (if provided)
    2. Environment variables
    3. Default values
    """

    def __init__(
        self,
        yaml_file: Optional[str] = None,
        env_file: Optional[str] = None,
        use_env_vars: bool = True,
        defaults: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication configuration.

        Args:
            yaml_file: Path to YAML configuration file
            env_file: Path to .env file (for manual loading)
            use_env_vars: Whether to use environment variables
            defaults: Default configuration values
        """
        self.yaml_file = yaml_file
        self.env_file = env_file
        self.use_env_vars = use_env_vars
        self.defaults = defaults or {}
        self._config: Dict[str, Any] = {}
        self._users: Dict[str, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from all sources."""
        # Load defaults first
        self._config = self.defaults.copy()

        # Load from YAML if provided
        if self.yaml_file:
            self._load_from_yaml()

        # Load from environment variables
        if self.use_env_vars:
            self._load_from_env()

    def _load_from_yaml(self) -> None:
        """Load configuration and users from YAML file."""
        try:
            yaml_path = Path(self.yaml_file)
            if not yaml_path.exists():
                raise FileNotFoundError(f"YAML config file not found: {self.yaml_file}")

            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            # Load users (check both 'users' key and flat structure)
            if 'users' in data and isinstance(data['users'], dict):
                self._users = data['users'].copy()
            elif isinstance(data, dict):
                # Assume flat structure (username: password)
                self._users = data.copy()

            # Load other config
            for key, value in data.items():
                if key != 'users':
                    self._config[key] = value

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {self.yaml_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading YAML config: {e}")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Load single user credentials from env
        env_user = os.getenv('AUTH_USER', os.getenv('BASIC_AUTH_USER'))
        env_password = os.getenv('AUTH_PASSWORD', os.getenv('BASIC_AUTH_PASSWORD'))

        if env_user and env_password:
            self._users[env_user] = env_password

        # Load other configuration from env
        for key in ['AUTH_TYPE', 'LOG_LEVEL', 'LOG_FILE', 'REQUIRE_HTTPS']:
            env_key = f"AUTH_{key.upper()}" if key not in ['AUTH_TYPE'] else key
            if env_key in os.environ:
                self._config[key.lower()] = os.getenv(env_key)

    def get_users(self) -> Dict[str, str]:
        """Get all configured users and passwords."""
        return self._users.copy()

    def get_user_password(self, username: str) -> Optional[str]:
        """Get password for a specific user."""
        return self._users.get(username)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def get_config(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self._config.copy()

    def set_users(self, users: Dict[str, str]) -> None:
        """Set users dictionary (useful for in-memory config)."""
        self._users = users.copy()

    def reload(self) -> None:
        """Reload configuration from sources."""
        self._config = self.defaults.copy()
        self._users = {}
        self._load_config()

    def validate(self) -> bool:
        """Validate that configuration is complete."""
        if not self._users:
            raise ValueError("No users configured. Check YAML file or environment variables.")
        return True

    def __repr__(self) -> str:
        return f"<AuthConfig with {len(self._users)} users>"
