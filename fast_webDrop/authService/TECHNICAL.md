# AuthService - Technical Documentation

Complete technical reference for AuthService authentication library.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Package Structure](#package-structure)
3. [Installation](#installation)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Security Implementation](#security-implementation)
7. [User Management](#user-management)
8. [Audit Logging](#audit-logging)
9. [Advanced Usage](#advanced-usage)
10. [Framework Integration](#framework-integration)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Framework (Flask, Django, etc.)        │
└────────────────────────┬────────────────────────────────────────┘
                         │ requests with credentials
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AuthManager (core.py)                      │
│  - verify_credentials(username, password)                       │
│  - verify_basic_auth_header(auth_header)                        │
│  - add_user(), remove_user(), change_password()                 │
│  - persist_changes()                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    ┌────────────┐  ┌──────────┐  ┌──────────┐
    │ AuthConfig │  │ AuthLogger│  │ User     │
    │ (YAML/ENV) │  │ (Logging) │  │ (Models) │
    └────────────┘  └──────────┘  └──────────┘
         ↓
    ┌────────────────────┐
    │  users.yaml / ENV  │
    └────────────────────┘
```

### Data Flow

```
1. HTTP Request with Authorization header
   ↓
2. AuthManager.verify_basic_auth_header() decodes Base64
   ↓
3. AuthConfig loads user from YAML/ENV (cached)
   ↓
4. Constant-time password comparison
   ↓
5. Check is_active field
   ↓
6. AuthLogger logs attempt (success/failure)
   ↓
7. Return AuthResult with User object or error
```

### Class Hierarchy

```python
AuthResult
├── success: bool
├── user: User (if successful)
├── message: str
└── error_code: str

User
├── username: str
├── email: Optional[str]
├── is_active: bool = True
├── roles: list = ["user"]
├── metadata: dict = {}
└── last_login: Optional[datetime]

AuthConfig
├── _users: Dict[str, str]
├── _user_metadata: Dict[str, Dict]
└── Methods:
    ├── get_users() → Dict
    ├── get_user_metadata(username) → Dict
    ├── save_users(filepath)
    └── validate(strict=True)

AuthManager
├── config: AuthConfig
├── logger: AuthLogger
├── users: Dict[str, str]
└── Methods:
    ├── verify_credentials() → AuthResult
    ├── verify_basic_auth_header() → AuthResult
    ├── add_user() → bool
    ├── remove_user() → bool
    ├── change_password() → bool
    ├── persist_changes() → None
    ├── list_users() → list
    └── get_user_info() → dict
```

---

## Package Structure

```
authService/
├── authservice/              # Main package
│   ├── __init__.py          # Public API exports
│   ├── core.py              # AuthManager (authentication logic)
│   ├── config.py            # AuthConfig (configuration loading)
│   ├── models.py            # User, AuthResult (data models)
│   ├── logger.py            # AuthLogger (logging utilities)
│   ├── hashing.py           # Password hashing (bcrypt)
│   └── appconfig.py         # AppConfig (centralized config)
│
├── tests/                    # Test suite
│   ├── test_auth.py         # Authentication tests
│   ├── test_hashing.py      # Hashing tests
│   ├── test_audit_log.py    # Audit logging tests
│   └── test_appconfig.py    # Configuration tests
│
├── examples/                 # Framework examples
│   ├── flask_example.py
│   ├── django_example.py
│   └── ...
│
├── scripts/                  # Utility scripts
│   └── migrate_passwords.py # Password migration
│
├── config/                   # Configuration files
│   ├── app_config.yaml      # Application config
│   └── users.yaml           # User credentials
│
├── setup.py                  # Package setup
├── pyproject.toml           # Build configuration
├── requirements.txt         # Dependencies
│
├── README.md                # Main documentation
├── QUICKSTART.md            # Getting started guide
└── TECHNICAL.md             # This file
```

### Import Structure

```python
# Public API (from authservice/__init__.py)
from authservice import (
    AuthManager,              # Main authentication class
    User,                     # User model
    AuthResult,               # Authentication result
    AuthConfig,               # Configuration loader
    AppConfig,                # Centralized config
    setup_logger,             # Logger factory
    setup_logger_from_config, # Logger from config
    AuthLogger,               # Logger class
    hash_password,            # Password hashing
    verify_password,          # Password verification
    is_bcrypt_hash,           # Hash validation
    migrate_yaml_file         # Password migration
)
```

---

## Installation

### From PyPI (Recommended)

```bash
pip install authservice
```

### From Source

```bash
git clone https://github.com/yourusername/authService.git
cd authService
pip install -e .
```

### Dependencies

```txt
pyyaml>=6.0     # YAML configuration files
bcrypt>=4.0.1   # Password hashing
```

### Verify Installation

```python
from authservice import AuthManager, __version__
print(f"AuthService {__version__} installed successfully")
```

---

## API Reference

### AuthManager

Main class for authentication operations.

#### `__init__(config, logger=None, hash_function=None, use_hashing=True, app_config=None)`

Initialize the authentication manager.

**Parameters:**
- `config` (AuthConfig): Configuration instance
- `logger` (AuthLogger, optional): Logger instance
- `hash_function` (callable, optional): Custom password verification function
- `use_hashing` (bool): Enable password hashing (deprecated, always True)
- `app_config` (AppConfig, optional): Centralized application config

**Returns:** AuthManager instance

**Example:**
```python
from authservice import AuthManager, AuthConfig

config = AuthConfig(yaml_file='users.yaml')
auth = AuthManager(config)
```

#### `verify_credentials(username, password, ip_address='unknown')`

Verify user credentials with constant-time comparison.

**Parameters:**
- `username` (str): Username to authenticate
- `password` (str): Password to verify
- `ip_address` (str): Client IP address (for logging)

**Returns:** `AuthResult`

**Security:** Uses constant-time comparison to prevent timing attacks.

**Example:**
```python
result = auth.verify_credentials('admin', 'password', '192.168.1.1')

if result.success:
    print(f"User: {result.user.username}")
    print(f"Roles: {result.user.roles}")
else:
    print(f"Error: {result.error_code} - {result.message}")
```

**Error Codes:**
- `INVALID_CREDENTIALS` - Username doesn't exist or password is wrong
- `USER_DISABLED` - Account is inactive (is_active=False)
- `AUTH_ERROR` - Internal authentication error

#### `verify_basic_auth_header(auth_header, ip_address='unknown')`

Verify HTTP Basic Authentication header.

**Parameters:**
- `auth_header` (str): Authorization header value (e.g., "Basic base64...")
- `ip_address` (str): Client IP address

**Returns:** `AuthResult`

**Example:**
```python
auth_header = request.headers.get('Authorization')
result = auth.verify_basic_auth_header(auth_header, request.remote_addr)
```

**Error Codes:**
- `INVALID_HEADER` - Header doesn't start with "Basic "
- `INVALID_ENCODING` - Base64 decoding failed
- `HEADER_PARSE_ERROR` - Header parsing error
- (Plus error codes from `verify_credentials`)

#### `add_user(username, password, by_whom='system', ip_address='unknown')`

Add a user to in-memory configuration with automatic password hashing.

**Parameters:**
- `username` (str): New username
- `password` (str): New password (will be hashed automatically)
- `by_whom` (str): Who is performing this action (for audit logs)
- `ip_address` (str): IP address of requester

**Returns:** `bool` - True if added, False if user already exists

**Example:**
```python
if auth.add_user('newuser', 'password123', by_whom='admin'):
    print("User added successfully")
```

**Note:** Changes are in-memory only. Call `persist_changes()` to save to YAML.

#### `remove_user(username, by_whom='system', ip_address='unknown')`

Remove a user from in-memory configuration.

**Parameters:**
- `username` (str): Username to remove
- `by_whom` (str): Who is performing this action
- `ip_address` (str): IP address of requester

**Returns:** `bool` - True if removed, False if user doesn't exist

**Example:**
```python
if auth.remove_user('olduser', by_whom='admin'):
    print("User removed")
```

#### `change_password(username, new_password, by_whom='system', ip_address='unknown')`

Change user password with audit logging.

**Parameters:**
- `username` (str): Username whose password to change
- `new_password` (str): New password (will be hashed automatically)
- `by_whom` (str): Who is performing this action
- `ip_address` (str): IP address of requester

**Returns:** `bool` - True if changed, False if user doesn't exist

**Example:**
```python
if auth.change_password('admin', 'new_secure_password', by_whom='admin'):
    print("Password changed")
```

#### `persist_changes()`

Persist in-memory user changes to YAML file.

**Raises:** `ValueError` if no YAML file is configured

**Example:**
```python
auth.add_user('user1', 'password1')
auth.change_password('admin', 'newpass')
auth.persist_changes()  # Save to users.yaml
```

#### `list_users()`

Get list of all configured usernames.

**Returns:** `list` of usernames

**Example:**
```python
users = auth.list_users()
print(f"Users: {', '.join(users)}")
```

#### `get_user_info(username)`

Get information about a user.

**Parameters:**
- `username` (str): Username to look up

**Returns:** `dict` with user info or `None` if user doesn't exist

**Example:**
```python
info = auth.get_user_info('admin')
# Returns: {'username': 'admin', 'exists': True, 'is_active': True}
```

#### `reload_users()`

Reload users from configuration source.

**Example:**
```python
# users.yaml was modified externally
auth.reload_users()
```

---

### AuthConfig

Configuration loader for YAML files and environment variables.

#### `__init__(yaml_file=None, env_file=None, use_env_vars=True, defaults=None)`

Initialize configuration.

**Parameters:**
- `yaml_file` (str, optional): Path to YAML configuration file
- `env_file` (str, optional): Path to .env file
- `use_env_vars` (bool): Whether to load from environment variables
- `defaults` (dict, optional): Default configuration values

**Example:**
```python
# From YAML
config = AuthConfig(yaml_file='config/users.yaml')

# From environment
config = AuthConfig(use_env_vars=True)

# Combined
config = AuthConfig(
    yaml_file='users.yaml',
    use_env_vars=True,
    defaults={'debug': False}
)
```

#### `get_users()`

Get all configured users.

**Returns:** `Dict[str, str]` - {username: password_hash}

**Example:**
```python
users = config.get_users()
print(f"Configured users: {list(users.keys())}")
```

#### `get_user_password(username)`

Get password hash for a specific user.

**Parameters:**
- `username` (str): Username to look up

**Returns:** `str` (password hash) or `None`

**Example:**
```python
password_hash = config.get_user_password('admin')
```

#### `get_user_metadata(username)`

Get metadata for a specific user (extended YAML format).

**Parameters:**
- `username` (str): Username to look up

**Returns:** `dict` with metadata:
```python
{
    'is_active': bool,
    'roles': list,
    'email': str or None,
    'metadata': dict
}
```

**Example:**
```python
meta = config.get_user_metadata('admin')
print(f"Roles: {meta['roles']}")
print(f"Email: {meta['email']}")
print(f"Active: {meta['is_active']}")
```

#### `save_users(filepath=None)`

Save users back to YAML file.

**Parameters:**
- `filepath` (str, optional): Path to save to (defaults to self.yaml_file)

**Raises:** `ValueError` if no YAML file specified

**Example:**
```python
config.save_users()  # Save to original file
config.save_users('backup/users.yaml')  # Save to different file
```

#### `validate(strict=True)`

Validate configuration completeness and security.

**Parameters:**
- `strict` (bool): Check for security issues like plaintext passwords

**Returns:** `bool` - True if valid

**Raises:** `ValueError` if no users configured

**Example:**
```python
try:
    config.validate(strict=True)
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

#### `reload()`

Reload configuration from all sources.

**Example:**
```python
config.reload()
```

---

### User Model

User data model (dataclass).

```python
@dataclass
class User:
    username: str
    email: Optional[str] = None
    is_active: bool = True
    roles: list = field(default_factory=lambda: ["user"])
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
```

#### `has_role(role)`

Check if user has a specific role.

**Parameters:**
- `role` (str): Role to check

**Returns:** `bool`

**Example:**
```python
if user.has_role('admin'):
    print("User is an administrator")
```

#### `to_dict()`

Convert user to dictionary representation.

**Returns:** `dict`

**Example:**
```python
user_dict = user.to_dict()
# Returns: {'username': '...', 'email': '...', ...}
```

---

### AuthResult Model

Authentication result (dataclass).

```python
@dataclass
class AuthResult:
    success: bool
    user: Optional[User] = None
    message: str = ""
    error_code: Optional[str] = None
```

**Example:**
```python
result = auth.verify_credentials('admin', 'password')

if result.success:
    print(f"Success: {result.message}")
    print(f"User: {result.user.username}")
else:
    print(f"Failed: {result.error_code} - {result.message}")
```

---

## Configuration

### YAML Configuration Formats

#### Simple Format

Basic username:password mapping:

```yaml
users:
  admin: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
  user1: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
  developer: $2b$12$uVPJhDDZPjpCxKI/3KX1QOHs.XdkFKC8KbIvlvxdR0KHAhAZ2Pkyq
```

**Use case:** Simple authentication without extra metadata

#### Extended Format

Complete user information with metadata:

```yaml
users:
  admin:
    password: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
    is_active: true
    roles: [admin, manager, user]
    email: admin@example.com
    metadata:
      department: IT
      employee_id: E001
      phone: "+1-555-0100"

  user1:
    password: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
    is_active: true
    roles: [user]
    email: user1@example.com
    metadata:
      department: Sales

  suspended:
    password: $2b$12$...
    is_active: false  # Account disabled
    roles: [user]
    email: suspended@example.com
```

**Use case:** Role-based access control, user metadata, account disabling

#### Backward Compatibility

Both formats work simultaneously:

```yaml
users:
  # Simple format
  admin: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK

  # Extended format
  user1:
    password: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
    roles: [admin]
    email: user1@example.com
```

### Environment Variables

```bash
# Single user credentials
export AUTH_USER=admin
export AUTH_PASSWORD=admin_password

# Alternative names
export BASIC_AUTH_USER=admin
export BASIC_AUTH_PASSWORD=admin_password
```

**Priority:** YAML file overrides environment variables.

### Configuration Priority

1. YAML file (if provided)
2. Environment variables (if enabled)
3. Default values (if provided)

---

## Security Implementation

### Timing Attack Protection

AuthService uses constant-time password comparison to prevent timing attacks.

**Implementation:**

```python
# In core.py
DUMMY_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK"

def verify_credentials(self, username, password, ip_address='unknown'):
    # Always perform password verification (constant time)
    stored_password = self.users.get(username, DUMMY_HASH)
    password_valid = self._compare_passwords(password, stored_password)

    # Check both conditions
    user_exists = username in self.users

    if not user_exists or not password_valid:
        # Same error code for both cases
        return AuthResult(
            success=False,
            message="Invalid credentials",
            error_code="INVALID_CREDENTIALS"
        )
```

**Why this matters:**
- Prevents attackers from distinguishing between "user doesn't exist" and "wrong password"
- Uses dummy hash for non-existent users to maintain constant timing
- Both code paths take approximately the same time

### Username Enumeration Prevention

Returns the same error code for both scenarios:

```python
# Non-existent user
result = auth.verify_credentials('fake_user', 'password')
# Returns: INVALID_CREDENTIALS

# Wrong password
result = auth.verify_credentials('real_user', 'wrong_password')
# Returns: INVALID_CREDENTIALS (same error code)
```

**Before (vulnerable):**
- Non-existent user: `USER_NOT_FOUND`
- Wrong password: `INVALID_CREDENTIALS`
- Attacker can enumerate valid usernames

**After (secure):**
- Both cases: `INVALID_CREDENTIALS`
- Impossible to distinguish between the two cases

### Password Hashing

Bcrypt with 12 salt rounds (default):

```python
from authservice import hash_password, verify_password

# Hash password
hashed = hash_password('my_password')
# Output: $2b$12$... (60 characters)

# Verify password
is_valid = verify_password('my_password', hashed)
# Output: True
```

**Bcrypt Rounds Guide:**

| Rounds | Speed      | Security    | Use Case            |
|--------|------------|-------------|---------------------|
| 4-8    | Very fast  | Low         | Testing only        |
| 10     | Fast       | Good        | Development         |
| 11-12  | Standard   | Recommended | Production (default)|
| 13+    | Slow       | Very high   | High-security apps  |

**Change rounds:**

```python
from authservice import hash_password

# Faster (less secure, for development)
hash_password('password', rounds=10)

# Slower (more secure, for sensitive apps)
hash_password('password', rounds=13)
```

### Inactive Account Blocking

Extended YAML format supports account disabling:

```yaml
users:
  suspended:
    password: $2b$12$...
    is_active: false  # Account disabled
```

```python
result = auth.verify_credentials('suspended', 'correct_password')
# Returns: error_code='USER_DISABLED'
```

---

## User Management

### Add Users

```python
# Add user (password automatically hashed)
auth.add_user('newuser', 'secure_password', by_whom='admin')

# Verify immediately
result = auth.verify_credentials('newuser', 'secure_password')
print(result.success)  # True
```

### Change Passwords

```python
# Change password
auth.change_password('admin', 'new_password', by_whom='admin')

# Old password no longer works
result = auth.verify_credentials('admin', 'old_password')
print(result.success)  # False

# New password works
result = auth.verify_credentials('admin', 'new_password')
print(result.success)  # True
```

### Persist Changes

```python
# Make changes in-memory
auth.add_user('user1', 'password1')
auth.add_user('user2', 'password2')
auth.change_password('admin', 'new_password')

# Save to YAML
auth.persist_changes()

# Reload and verify
auth2 = AuthManager(AuthConfig(yaml_file='users.yaml'))
print(auth2.list_users())  # ['admin', 'user1', 'user2']
```

### Remove Users

```python
# Remove user
auth.remove_user('olduser', by_whom='admin')

# Verify removed
users = auth.list_users()
print('olduser' in users)  # False
```

---

## Audit Logging

### Enable Audit Logging

```python
from authservice import AuthManager, AuthConfig, setup_logger

# Create logger with separate audit log
logger = setup_logger(
    name='AuthManager',
    log_file='logs/auth.log',
    audit_log_file='logs/audit.log'
)

config = AuthConfig(yaml_file='users.yaml')
auth = AuthManager(config, logger=logger)
```

### Audit Events

The following events are automatically logged:

- **USER_ADDED** - New user account created
- **USER_REMOVED** - User account deleted
- **USER_MODIFIED** - User information changed (future)
- **PASSWORD_CHANGED** - Password modified

### Audit Log Format

```
[AUDIT] 2026-01-22 10:15:30 - USER_ADDED: username=newuser, by=admin, ip=192.168.1.1
[AUDIT] 2026-01-22 10:16:45 - PASSWORD_CHANGED: username=admin, by=admin, ip=192.168.1.1
[AUDIT] 2026-01-22 10:17:20 - USER_REMOVED: username=olduser, by=admin, ip=192.168.1.1
```

Each entry includes:
- Timestamp (ISO format)
- Event type
- username (affected user)
- by (actor performing action)
- ip (source IP address)

### Filtering Audit Logs

```bash
# View all user additions
grep "USER_ADDED" logs/audit.log

# View changes by specific admin
grep "by=admin" logs/audit.log

# View all operations on a user
grep "username=admin" logs/audit.log

# Count password changes
grep "PASSWORD_CHANGED" logs/audit.log | wc -l
```

---

## Advanced Usage

### Custom Password Hashing

Use a different hashing algorithm (e.g., Argon2):

```python
from argon2 import PasswordHasher
from authservice import AuthManager, AuthConfig

hasher = PasswordHasher()

def verify_with_argon2(password, hash):
    try:
        hasher.verify(hash, password)
        return True
    except:
        return False

auth = AuthManager(
    AuthConfig(yaml_file='users.yaml'),
    hash_function=verify_with_argon2
)
```

### Role-Based Access Control

```python
# Check user role
result = auth.verify_credentials('admin', 'password')

if result.success:
    user = result.user

    if user.has_role('admin'):
        # Allow admin operation
        pass

    if user.has_role('manager'):
        # Allow manager operation
        pass
```

**In Flask:**

```python
from functools import wraps
from flask import g, jsonify

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not g.user.has_role(role):
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/admin/dashboard')
@require_auth
@require_role('admin')
def admin_dashboard():
    return {'message': 'Admin dashboard'}
```

### Multi-Tenant Authentication

```python
class TenantAuthConfig(AuthConfig):
    def __init__(self, tenant_id):
        yaml_file = f'config/tenants/{tenant_id}/users.yaml'
        super().__init__(yaml_file=yaml_file)

# Usage
tenant1_config = TenantAuthConfig('tenant1')
tenant1_auth = AuthManager(tenant1_config)

tenant2_config = TenantAuthConfig('tenant2')
tenant2_auth = AuthManager(tenant2_config)
```

### Custom User Model

```python
from authservice.models import User
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CustomUser(User):
    department: str = ""
    manager: str = ""
    phone: str = ""
    hire_date: datetime = None

    def is_manager(self):
        return 'manager' in self.roles

    def get_full_info(self):
        return {
            **self.to_dict(),
            'department': self.department,
            'manager': self.manager,
            'phone': self.phone
        }
```

---

## Framework Integration

### Flask Complete Example

```python
from flask import Flask, request, g, jsonify
from authservice import AuthManager, AuthConfig, setup_logger
from functools import wraps

app = Flask(__name__)

# Setup authentication
logger = setup_logger('FlaskAuth', audit_log_file='logs/audit.log')
config = AuthConfig(yaml_file='config/users.yaml')
auth_manager = AuthManager(config, logger=logger)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        result = auth_manager.verify_basic_auth_header(
            auth_header,
            ip_address=request.remote_addr
        )

        if not result.success:
            return jsonify({'error': 'Unauthorized'}), 401

        g.user = result.user
        return f(*args, **kwargs)
    return decorated

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not g.user.has_role(role):
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/api/public')
def public():
    return jsonify({'message': 'Public endpoint'})

@app.route('/api/protected')
@require_auth
def protected():
    return jsonify({
        'user': g.user.username,
        'roles': g.user.roles,
        'email': g.user.email
    })

@app.route('/api/admin')
@require_auth
@require_role('admin')
def admin():
    return jsonify({'message': 'Admin only'})

@app.route('/api/users', methods=['GET'])
@require_auth
@require_role('admin')
def list_users():
    users = auth_manager.list_users()
    return jsonify({'users': users})

@app.route('/api/users', methods=['POST'])
@require_auth
@require_role('admin')
def add_user():
    data = request.json
    success = auth_manager.add_user(
        data['username'],
        data['password'],
        by_whom=g.user.username,
        ip_address=request.remote_addr
    )

    if success:
        auth_manager.persist_changes()
        return jsonify({'message': 'User added'}), 201
    else:
        return jsonify({'error': 'User exists'}), 409

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Testing

### Run Test Suite

```bash
# Activate environment
source ~/.venv_gen/bin/activate

# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_auth -v

# Run specific test class
python -m unittest tests.test_auth.TestAuthManager -v

# Run specific test method
python -m unittest tests.test_auth.TestAuthManager.test_verify_credentials -v
```

### Test Coverage

AuthService includes 122 tests covering:

- Authentication (basic, HTTP Basic Auth)
- Security (timing attacks, username enumeration)
- User management (add, remove, change password)
- Persistence (save/load from YAML)
- Extended YAML format
- Audit logging
- Configuration loading
- Password hashing

### Writing Tests

```python
import unittest
from authservice import AuthManager, AuthConfig

class TestMyIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AuthConfig()
        self.config.set_users({
            'testuser': hash_password('testpass')
        })
        self.auth = AuthManager(self.config)

    def test_authentication(self):
        result = self.auth.verify_credentials('testuser', 'testpass')
        self.assertTrue(result.success)

    def test_wrong_password(self):
        result = self.auth.verify_credentials('testuser', 'wrong')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'INVALID_CREDENTIALS')
```

---

## Troubleshooting

### Common Issues

#### 1. "No users configured" Error

**Cause:** AuthConfig can't find users in YAML or environment.

**Solution:**
```python
# Check YAML file exists
import os
print(os.path.exists('config/users.yaml'))

# Check YAML content
import yaml
with open('config/users.yaml') as f:
    print(yaml.safe_load(f))

# Or use environment variables
export AUTH_USER=admin
export AUTH_PASSWORD=password
```

#### 2. "Invalid credentials" Always Fails

**Cause:** Passwords in YAML are plaintext, not bcrypt hashes.

**Solution:**
```python
from authservice import hash_password

# Generate hash
hashed = hash_password('my_password')
print(hashed)  # Use this in YAML
```

Or migrate existing file:
```bash
python scripts/migrate_passwords.py config/users.yaml
```

#### 3. ImportError: No module named 'authservice'

**Cause:** Package not installed.

**Solution:**
```bash
pip install -e .
```

#### 4. Authentication is Slow

**Cause:** Bcrypt rounds too high (default 12).

**Solution:** For development, reduce rounds:
```python
from authservice import hash_password

# Faster for development (less secure)
hash_password('password', rounds=10)
```

#### 5. Audit Log Not Created

**Cause:** Log directory doesn't exist or no permissions.

**Solution:**
```bash
mkdir -p logs
chmod 755 logs
```

#### 6. YAML Parse Error

**Cause:** Invalid YAML syntax.

**Solution:** Validate YAML:
```bash
python -c "import yaml; yaml.safe_load(open('users.yaml'))"
```

---

## Error Codes Reference

| Code | Meaning | Cause |
|------|---------|-------|
| `INVALID_CREDENTIALS` | Authentication failed | Username doesn't exist or password is wrong |
| `USER_DISABLED` | Account disabled | User has `is_active: false` |
| `AUTH_ERROR` | Internal error | Exception during authentication |
| `INVALID_HEADER` | Bad Authorization header | Header doesn't start with "Basic " |
| `INVALID_ENCODING` | Base64 decode failed | Malformed Base64 in header |
| `HEADER_PARSE_ERROR` | Header parsing error | Cannot parse username:password |

---

## Performance Considerations

### Bcrypt Performance

Bcrypt rounds affect performance:

| Rounds | Time (approx) | Use Case |
|--------|---------------|----------|
| 10     | ~100ms       | Development |
| 12     | ~250ms       | Production (default) |
| 13     | ~500ms       | High security |

**Recommendation:** Use 12 rounds (default) for production.

### Caching

AuthConfig caches YAML content in memory. Reload only when needed:

```python
# Good: Reload periodically
if time.time() - last_reload > 300:  # Every 5 minutes
    auth.reload_users()

# Bad: Reload on every request
auth.reload_users()  # Don't do this
```

### Large User Bases

For >1000 users, consider:
- Database backend instead of YAML
- External authentication service (OAuth, LDAP)
- Caching layer (Redis)

---

## Migration Guide

### From Plaintext to Bcrypt

```bash
# Migrate existing YAML file
python scripts/migrate_passwords.py config/users.yaml
```

### From Flask-HTTPAuth

**Before:**
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    user = load_user(username)
    return user and user.check_password(password)
```

**After:**
```python
from authservice import AuthManager, AuthConfig

auth_manager = AuthManager(AuthConfig(yaml_file='users.yaml'))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        result = auth_manager.verify_basic_auth_header(
            request.headers.get('Authorization', '')
        )
        if not result.success:
            return jsonify({'error': 'Unauthorized'}), 401
        g.user = result.user
        return f(*args, **kwargs)
    return decorated
```

---

## Best Practices

1. **Use HTTPS in production** - Never use HTTP Basic Auth over HTTP
2. **Store credentials securely** - Add `config/users.yaml` to `.gitignore`
3. **Implement rate limiting** - Protect against brute force attacks
4. **Monitor audit logs** - Set up alerts for suspicious activity
5. **Rotate passwords regularly** - Especially for admin accounts
6. **Use extended YAML format** - For better user management
7. **Enable audit logging** - For compliance and security
8. **Test thoroughly** - Include both success and failure cases
9. **Keep dependencies updated** - Regular security updates

---

## Additional Resources

- **Repository:** https://github.com/yourusername/authService
- **Issues:** https://github.com/yourusername/authService/issues
- **Examples:** See `examples/` directory
- **Tests:** See `tests/` directory

---

**For getting started, see [QUICKSTART.md](QUICKSTART.md)**

**For feature overview, see [README.md](README.md)**
