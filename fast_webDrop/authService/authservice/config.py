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
        self._user_metadata: Dict[str, Dict[str, Any]] = {}
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

            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # Load users (check both 'users' key and flat structure)
            if 'users' in data and isinstance(data['users'], dict):
                for username, user_data in data['users'].items():
                    if isinstance(user_data, str):
                        # Simple format: username: password
                        self._users[username] = user_data
                        self._user_metadata[username] = {
                            'is_active': True,
                            'roles': ['user'],
                            'email': None,
                            'metadata': {}
                        }
                    elif isinstance(user_data, dict):
                        # Extended format: username: {password, is_active, roles, email}
                        self._users[username] = user_data.get('password', '')
                        self._user_metadata[username] = {
                            'is_active': user_data.get('is_active', True),
                            'roles': user_data.get('roles', ['user']),
                            'email': user_data.get('email'),
                            'metadata': user_data.get('metadata', {})
                        }
            elif isinstance(data, dict):
                # Assume flat structure (username: password)
                for username, password in data.items():
                    if isinstance(password, str):
                        self._users[username] = password
                        self._user_metadata[username] = {
                            'is_active': True,
                            'roles': ['user'],
                            'email': None,
                            'metadata': {}
                        }

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
            # Set default metadata for env-loaded users
            if env_user not in self._user_metadata:
                self._user_metadata[env_user] = {
                    'is_active': True,
                    'roles': ['user'],
                    'email': None,
                    'metadata': {}
                }

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

    def get_user_metadata(self, username: str) -> Dict[str, Any]:
        """
        Get metadata for a specific user.

        Returns default metadata if user doesn't exist.
        """
        return self._user_metadata.get(username, {
            'is_active': True,
            'roles': ['user'],
            'email': None,
            'metadata': {}
        })

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def get_config(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self._config.copy()

    def set_users(self, users: Dict[str, str]) -> None:
        """Set users dictionary (useful for in-memory config)."""
        self._users = users.copy()
        # Ensure all users have metadata entries
        for username in self._users:
            if username not in self._user_metadata:
                self._user_metadata[username] = {
                    'is_active': True,
                    'roles': ['user'],
                    'email': None,
                    'metadata': {}
                }

    def reload(self) -> None:
        """Reload configuration from sources."""
        self._config = self.defaults.copy()
        self._users = {}
        self._user_metadata = {}
        self._load_config()

    def save_users(self, filepath: Optional[str] = None) -> None:
        """
        Save users back to YAML file.

        Args:
            filepath: Path to save to (defaults to self.yaml_file)

        Raises:
            ValueError: If no YAML file specified
        """
        if filepath is None:
            filepath = self.yaml_file

        if not filepath:
            raise ValueError("No YAML file specified for saving")

        # Reconstruct YAML structure with metadata
        data = {'users': {}}
        for username, password in self._users.items():
            meta = self._user_metadata.get(username, {})
            # Use extended format if user has custom metadata
            if (meta.get('email') or
                meta.get('roles', ['user']) != ['user'] or
                not meta.get('is_active', True) or
                meta.get('metadata')):
                # Use extended format
                user_data = {
                    'password': password,
                    'is_active': meta.get('is_active', True),
                    'roles': meta.get('roles', ['user'])
                }
                if meta.get('email'):
                    user_data['email'] = meta.get('email')
                if meta.get('metadata'):
                    user_data['metadata'] = meta.get('metadata')
                data['users'][username] = user_data
            else:
                # Use simple format
                data['users'][username] = password

        # Preserve other config keys
        for key, value in self._config.items():
            if key != 'users':
                data[key] = value

        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def validate(self, strict: bool = True) -> bool:
        """
        Validate that configuration is complete and correct.

        Args:
            strict: If True, check for security issues like plaintext passwords

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If no users are configured
        """
        if not self._users:
            raise ValueError("No users configured. Check YAML file or environment variables.")

        if strict:
            # Check all passwords are hashed
            from authservice.hashing import is_bcrypt_hash

            for username, password in self._users.items():
                if not is_bcrypt_hash(password):
                    import warnings
                    warnings.warn(
                        f"User '{username}' has plaintext password. "
                        f"Run: python scripts/migrate_passwords.py {self.yaml_file}",
                        UserWarning,
                        stacklevel=2
                    )

        return True

    def __repr__(self) -> str:
        return f"<AuthConfig with {len(self._users)} users>"
