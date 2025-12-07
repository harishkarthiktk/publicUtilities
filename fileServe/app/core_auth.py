from flask_httpauth import HTTPBasicAuth
from flask import current_app, request
import os
import yaml
from pathlib import Path
import logging

# Use print for early logging before app.logger is available

auth = HTTPBasicAuth()

# Module-level cache for user credentials
user_credentials_cache = None


def load_yaml_users():
    """
    Load user credentials from YAML file or environment variable path.
    Supports YAML structure with optional 'users' key or direct dict.
    Caches results for subsequent calls.
    Returns dict of username: password or None on failure.
    """
    global user_credentials_cache
    if user_credentials_cache is not None:
        return user_credentials_cache

    users_file = os.getenv('BASIC_AUTH_USERS_FILE', 'config/users.yaml')
    users_path = Path(users_file).resolve()
    current_app.logger.debug(f"Loading YAML from {users_path}, exists: {users_path.exists()}")

    if not users_path.exists():
        current_app.logger.info("No YAML users file found, falling back to env credentials")
        user_credentials_cache = None
        return None

    try:
        with open(users_path, 'r') as f:
            data = yaml.safe_load(f)
        current_app.logger.debug(f"YAML data loaded: {data}")

        if isinstance(data, dict):
            if 'users' in data:
                user_credentials_cache = data['users']
            else:
                user_credentials_cache = data
            if user_credentials_cache is not None:
                current_app.logger.info(f"Loaded {len(user_credentials_cache)} users from YAML")
            else:
                current_app.logger.warning("Loaded empty or invalid user credentials from YAML")
            return user_credentials_cache
        else:
            current_app.logger.warning("Invalid YAML format: expected dict")
            user_credentials_cache = None
            return None
    except Exception as e:
        current_app.logger.error(f"Error loading YAML users file {users_path}: {e}")
        user_credentials_cache = None
        return None


@auth.verify_password
def verify_password(username, password):
    """
    Verify username and password against YAML users or fallback to environment variables.
    Logs success/failure attempts.
    Returns username on success, None on failure.
    """
    client_ip = request.remote_addr
    current_app.logger.debug(f"Auth attempt for username: {username}, password length: {len(password)}, from IP: {client_ip}")
    # Try YAML first
    yaml_users = load_yaml_users()
    current_app.logger.debug(f"YAML users loaded for verification: {bool(yaml_users)}")
    if yaml_users and username in yaml_users and yaml_users[username] == password:
        current_app.logger.debug("Auth success via YAML")
        current_app.logger.info(f"Successful Basic Auth (YAML) for user: {username} from IP: {client_ip}")
        return username

    # Fallback to env
    expected_user = os.getenv('BASIC_AUTH_USER', 'admin')
    expected_pass = os.getenv('BASIC_AUTH_PASSWORD', 'password')
    current_app.logger.debug(f"Env fallback - expected_user: {expected_user}, expected_pass length: {len(expected_pass)}")
    if username == expected_user and password == expected_pass:
        current_app.logger.debug("Auth success via ENV")
        current_app.logger.info(f"Successful Basic Auth (ENV) for user: {username} from IP: {client_ip}")
        return username
    else:
        current_app.logger.debug(f"Auth failure - username '{username}' != '{expected_user}' or password mismatch")
        current_app.logger.warning(f"Failed Basic Auth attempt for user: {username} from IP: {client_ip}")
        return None