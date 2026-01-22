"""Password hashing utilities using bcrypt."""

import bcrypt
import os
from typing import Dict, Optional, List
import yaml


def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash a password using bcrypt with configurable rounds.

    Args:
        password: The plaintext password to hash
        rounds: Number of bcrypt salt rounds (10-13 recommended)
               Higher values are more secure but slower
               Default: 12 (standard for most applications)

    Returns:
        The bcrypt hash of the password as a string

    Raises:
        TypeError: If password is not a string
        ValueError: If rounds is not in valid range (4-31)
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    if not isinstance(rounds, int) or rounds < 4 or rounds > 31:
        raise ValueError("Rounds must be an integer between 4 and 31")

    # Create salt with specified rounds
    salt = bcrypt.gensalt(rounds=rounds)
    # bcrypt.hashpw requires bytes
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(provided: str, hashed: str) -> bool:
    """
    Verify a provided password against a bcrypt hash.

    Args:
        provided: The plaintext password provided by the user
        hashed: The bcrypt hash to verify against

    Returns:
        True if the password matches the hash, False otherwise

    Raises:
        TypeError: If provided or hashed is not a string
    """
    if not isinstance(provided, str) or not isinstance(hashed, str):
        raise TypeError("Both provided and hashed must be strings")

    try:
        # bcrypt.checkpw requires bytes
        return bcrypt.checkpw(provided.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        # Invalid hash format
        return False


def is_bcrypt_hash(password: str) -> bool:
    """
    Check if a string is a valid bcrypt hash.

    Bcrypt hashes have format: $2a$, $2b$, $2x$, or $2y$ followed by cost and salt/hash data
    Standard format: $2b$12$... (60 characters total)

    Args:
        password: The string to check

    Returns:
        True if the string is a bcrypt hash, False otherwise
    """
    if not isinstance(password, str):
        return False

    # Bcrypt hashes are 60 characters and start with $2a$, $2b$, $2x$, or $2y$
    if len(password) != 60:
        return False

    if not password.startswith(('$2a$', '$2b$', '$2x$', '$2y$')):
        return False

    return True


def migrate_users_dict(users: Dict[str, str]) -> Dict[str, str]:
    """
    Convert plaintext passwords in a users dictionary to bcrypt hashes.

    Args:
        users: Dictionary mapping usernames to plaintext passwords

    Returns:
        Dictionary with passwords converted to bcrypt hashes

    Raises:
        TypeError: If users is not a dictionary
    """
    if not isinstance(users, dict):
        raise TypeError("users must be a dictionary")

    migrated = {}
    for username, password in users.items():
        if is_bcrypt_hash(password):
            # Already hashed, keep as-is
            migrated[username] = password
        else:
            # Hash the plaintext password
            migrated[username] = hash_password(password)

    return migrated


def migrate_yaml_file(
    yaml_path: str,
    backup: bool = True,
    reserved_keys: Optional[List[str]] = None,
    rounds: int = 12
) -> None:
    """
    Migrate a YAML users file from plaintext to bcrypt hashed passwords.

    Creates a backup with .bak extension before migration.

    Args:
        yaml_path: Path to the YAML file to migrate
        backup: If True, create a backup file (default True)
        reserved_keys: List of keys to skip (not treated as usernames)
                      Default: ['auth_type', 'log_level', 'log_file', 'require_https']
        rounds: Number of bcrypt salt rounds to use for new hashes (default 12)

    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        IOError: If backup or write operations fail
        yaml.YAMLError: If YAML parsing fails
    """
    if reserved_keys is None:
        reserved_keys = ['auth_type', 'log_level', 'log_file', 'require_https']
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    # Create backup if requested (but don't overwrite existing backup)
    if backup:
        backup_path = f"{yaml_path}.bak"
        if not os.path.exists(backup_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)

    # Load YAML file
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if config is None:
        config = {}

    # Handle both formats: users key or flat structure
    if 'users' in config:
        users = config['users']
        if isinstance(users, dict):
            config['users'] = migrate_users_dict(users)
    else:
        # Flat structure - migrate all non-reserved keys
        migrated = {}
        for key, value in config.items():
            if key not in reserved_keys:
                # Assume it's a username:password pair
                if isinstance(value, str):
                    migrated[key] = hash_password(value, rounds) if not is_bcrypt_hash(value) else value
                else:
                    migrated[key] = value
            else:
                migrated[key] = value
        config = migrated

    # Write back to YAML
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
