# AuthTemplate - Reusable Authentication Module

A **framework-agnostic**, **production-ready** authentication system that can be quickly integrated into any project. Built with security, simplicity, and reusability in mind.

**Table of Contents:**
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Framework Integration](#framework-integration)
- [API Reference](#api-reference)
- [Security Considerations](#security-considerations)
- [Audit Logging](#audit-logging)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

---

## Overview

AuthTemplate provides a clean, modular approach to implementing user authentication. It's designed to:

- **Work with any framework** (Flask, Express, Django, Spring Boot, etc.)
- **Be integrated in minutes** (copy, configure, use)
- **Support multiple auth methods** (HTTP Basic, custom adapters)
- **Handle configuration flexibly** (YAML files, environment variables, in-memory)
- **Provide detailed logging** for security auditing

### What's Included

```
authtemplate/
├── __init__.py              # Package initialization
├── core.py                  # Main authentication logic (180 lines)
├── config.py                # Configuration loader (180 lines)
├── models.py                # User and AuthResult models (80 lines)
├── logger.py                # Logging utilities (130 lines)
├── example_users.yaml       # Example user configuration
├── README.md                # This file
├── framework_examples/
│   ├── flask_example.py     # Flask integration (150 lines)
│   ├── express_example.js   # Express.js integration (150 lines)
│   ├── django_example.py    # Django integration (150 lines)
│   └── spring_boot_example.java  # Spring Boot integration (150 lines)
└── tests/
    └── (test files)
```

**Total code: ~500 lines of Python** - Easy to understand, modify, and integrate.

---

## Features

✅ **Framework-Agnostic** - Pure Python core, adapters for any framework
✅ **Multiple Configuration Sources** - YAML, environment variables, in-memory
✅ **HTTP Basic Auth Support** - Built-in Base64 header parsing
✅ **Comprehensive Logging** - Auth attempts, failures, sources
✅ **User Management** - Add/remove users at runtime
✅ **Extensible** - Custom hash functions, custom user models
✅ **Type Hints** - Full Python type annotations
✅ **Zero Dependencies** (Python) - Only standard library required
✅ **Well Documented** - Docstrings, examples, guides
✅ **Production Ready** - Used in fileServe (proven)

---

## Installation

### 1. Install Dependencies

AuthService requires `bcrypt` and `PyYAML`. Install them:

```bash
pip install -r requirements.txt
```

Or individually:

```bash
pip install bcrypt>=4.0.1 pyyaml>=6.0
```

### 2. Copy Module to Your Project

**Option A: Copy the module**

```bash
cp -r authtemplate/ /path/to/your/project/
```

**Option B: Install as package**

```bash
pip install -e .
```

**Option C: Install from pip (if published)**

```bash
pip install authService
```

---

## Quick Start

### Minimal Example (Python)

```python
from authtemplate import AuthManager, AuthConfig

# 1. Load configuration
config = AuthConfig(yaml_file='users.yaml')

# 2. Create auth manager
auth_manager = AuthManager(config)

# 3. Verify credentials
result = auth_manager.verify_credentials('admin', 'password', ip_address='127.0.0.1')

if result.success:
    print(f"Hello, {result.user.username}!")
else:
    print(f"Auth failed: {result.message}")
```

### Integration with Flask (10 minutes)

```python
from flask import Flask, jsonify, g, request
from authtemplate import AuthManager, AuthConfig
from functools import wraps

app = Flask(__name__)
auth_manager = AuthManager(AuthConfig(yaml_file='users.yaml'))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        result = auth_manager.verify_basic_auth_header(auth_header)
        if not result.success:
            return jsonify({'error': 'Unauthorized'}), 401
        g.user = result.user
        return f(*args, **kwargs)
    return decorated

@app.route('/protected')
@require_auth
def protected():
    return jsonify({'user': g.user.username})

if __name__ == '__main__':
    app.run()
```

That's it! Full HTTP Basic Auth in **10 lines of code**.

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Framework (Flask, Express, etc.)       │
└────────────────────────┬────────────────────────────────────────┘
                         │ requests with credentials
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AuthManager (core.py)                      │
│  - verify_credentials(username, password)                       │
│  - verify_basic_auth_header(auth_header)                        │
│  - add_user(), remove_user(), reload_users()                    │
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
1. Request arrives with Authorization header
   ↓
2. AuthManager.verify_basic_auth_header() decodes Base64
   ↓
3. AuthConfig loads users from YAML/ENV (with caching)
   ↓
4. AuthManager compares credentials
   ↓
5. AuthLogger logs attempt (success/failure)
   ↓
6. Return AuthResult with user object or error
```

### Class Hierarchy

```
AuthResult
├── success: bool
├── user: User (if successful)
├── message: str
└── error_code: str

User
├── username: str
├── email: Optional[str]
├── is_active: bool
├── roles: list
├── metadata: dict
└── last_login: datetime

AuthConfig
├── get_users() → Dict[username: password]
├── get_user_password(username) → str
├── validate() → bool
└── reload() → None

AuthManager
├── verify_credentials(username, password, ip) → AuthResult
├── verify_basic_auth_header(header, ip) → AuthResult
├── add_user(username, password) → bool
├── remove_user(username) → bool
├── list_users() → list
└── get_user_info(username) → dict
```

---

## Configuration

### YAML File Configuration

Create `users.yaml`:

```yaml
# Method 1: Using 'users' key (recommended)
users:
  admin: admin_password
  user1: user1_password
  developer: dev_secure_password

# Method 2: Flat structure (alternative)
# admin: admin_password
# user1: user1_password
```

Load with:

```python
from authtemplate import AuthConfig

config = AuthConfig(yaml_file='config/users.yaml')
```

### Environment Variables

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=admin_password
```

Load with:

```python
config = AuthConfig(use_env_vars=True)
```

### Priority Order

Configuration is loaded in this order (first match wins):

1. **YAML file** (if provided)
2. **Environment variables** (if enabled)
3. **Default values** (if provided)

Example with all sources:

```python
config = AuthConfig(
    yaml_file='users.yaml',          # 1. Load from YAML
    use_env_vars=True,                # 2. Merge with ENV
    defaults={'debug': False}          # 3. Add defaults
)
```

### In-Memory Configuration

For testing or runtime user management:

```python
from authtemplate import AuthConfig

config = AuthConfig()
config.set_users({
    'admin': 'password',
    'user1': 'password1'
})
```

---

## Framework Integration

### Flask

**File: `framework_examples/flask_example.py` (150 lines)**

Complete working example with:
- Decorator-based route protection
- HTTP Basic Auth support
- Protected and public endpoints
- User info endpoints

**Setup:**

```python
from authtemplate import AuthManager, AuthConfig
from flask import Flask, g, request
from functools import wraps

auth_manager = AuthManager(AuthConfig(yaml_file='users.yaml'))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        result = auth_manager.verify_basic_auth_header(auth_header)
        if not result.success:
            return {'error': 'Unauthorized'}, 401
        g.user = result.user
        return f(*args, **kwargs)
    return decorated

@app.route('/protected')
@require_auth
def protected():
    return {'user': g.user.username}
```

**Run example:**

```bash
cd framework_examples
python flask_example.py
```

### Express.js

**File: `framework_examples/express_example.js` (150 lines)**

Complete working example with:
- Middleware-based authentication
- YAML configuration loading
- Multiple endpoints

**Setup:**

```javascript
const basicAuth = require('basic-auth');

const requireAuth = (req, res, next) => {
    const credentials = basicAuth(req);
    const result = authManager.verifyCredentials(
        credentials.name,
        credentials.pass,
        req.ip
    );

    if (!result.success) {
        return res.status(401).json({error: 'Unauthorized'});
    }

    req.user = result.user;
    next();
};

app.get('/protected', requireAuth, (req, res) => {
    res.json({user: req.user.username});
});
```

**Run example:**

```bash
cd framework_examples
npm install
node express_example.js
```

### Django

**File: `framework_examples/django_example.py` (150 lines)**

Complete working example with:
- Decorator-based view protection
- Class-based and function-based views
- Django integration patterns

**Setup in your app:**

```python
# auth_adapter.py
from authtemplate import AuthManager, AuthConfig

auth_manager = AuthManager(AuthConfig(yaml_file='users.yaml'))

# views.py
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from functools import wraps
import base64

def require_basic_auth(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        result = auth_manager.verify_basic_auth_header(auth_header)
        if not result.success:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        request.user_obj = result.user
        return f(request, *args, **kwargs)
    return wrapper

@require_basic_auth
def protected_view(request):
    return JsonResponse({'user': request.user_obj.username})
```

### Spring Boot

**File: `framework_examples/spring_boot_example.java` (150 lines)**

Complete working example with:
- Spring Security configuration
- HTTP Basic Auth
- Controller examples

**Setup in your project:**

```java
// SecurityConfig.java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.httpBasic()
            .and()
            .authorizeRequests()
                .antMatchers("/health").permitAll()
                .anyRequest().authenticated();
        return http.build();
    }
}

// Controller.java
@RestController
public class AuthController {
    @GetMapping("/protected")
    public ResponseEntity<?> protected() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return ResponseEntity.ok(Map.of(
            "user", auth.getName()
        ));
    }
}
```

---

## API Reference

### AuthManager

Main class for authentication operations.

#### `__init__(config, logger=None, hash_function=None)`

Initialize the authentication manager.

**Parameters:**
- `config` (AuthConfig): Configuration instance
- `logger` (AuthLogger): Optional logger instance
- `hash_function` (callable): Optional function for verifying hashed passwords

**Example:**

```python
from authtemplate import AuthManager, AuthConfig

config = AuthConfig(yaml_file='users.yaml')
auth_manager = AuthManager(config)
```

#### `verify_credentials(username, password, ip_address='unknown')`

Verify user credentials.

**Parameters:**
- `username` (str): Username to authenticate
- `password` (str): Password to verify
- `ip_address` (str): Client IP address (for logging)

**Returns:** `AuthResult`

**Example:**

```python
result = auth_manager.verify_credentials('admin', 'password', '192.168.1.1')

if result.success:
    print(f"User: {result.user.username}")
else:
    print(f"Error: {result.message}")
```

#### `verify_basic_auth_header(auth_header, ip_address='unknown')`

Verify HTTP Basic Authentication header.

**Parameters:**
- `auth_header` (str): Authorization header value (e.g., "Basic base64...")
- `ip_address` (str): Client IP address

**Returns:** `AuthResult`

**Example:**

```python
auth_header = request.headers.get('Authorization')
result = auth_manager.verify_basic_auth_header(auth_header)
```

#### `add_user(username, password)`

Add a user to in-memory configuration.

**Parameters:**
- `username` (str): New username
- `password` (str): New password

**Returns:** `bool` - True if added, False if user already exists

**Example:**

```python
if auth_manager.add_user('newuser', 'newpass'):
    print("User added successfully")
```

#### `remove_user(username)`

Remove a user from in-memory configuration.

**Parameters:**
- `username` (str): Username to remove

**Returns:** `bool` - True if removed, False if user doesn't exist

#### `list_users()`

Get list of all configured usernames.

**Returns:** `list` of usernames

**Example:**

```python
users = auth_manager.list_users()
print(f"Configured users: {users}")
```

#### `get_user_info(username)`

Get information about a user.

**Parameters:**
- `username` (str): Username to look up

**Returns:** `dict` with user info or `None`

### AuthConfig

Configuration loader.

#### `__init__(yaml_file=None, env_file=None, use_env_vars=True, defaults=None)`

Initialize configuration.

**Parameters:**
- `yaml_file` (str): Path to YAML configuration file
- `env_file` (str): Path to .env file
- `use_env_vars` (bool): Whether to load from environment variables
- `defaults` (dict): Default configuration values

#### `get_users()`

Get all configured users.

**Returns:** `Dict[str, str]` - {username: password}

#### `get_user_password(username)`

Get password for a specific user.

**Returns:** `str` or `None`

#### `reload()`

Reload configuration from all sources.

#### `validate()`

Validate configuration completeness.

**Raises:** `ValueError` if no users are configured

### User

User model.

```python
@dataclass
class User:
    username: str
    email: Optional[str] = None
    is_active: bool = True
    roles: list = field(default_factory=lambda: ["user"])
    metadata: dict = field(default_factory=dict)
    last_login: Optional[datetime] = None
```

**Methods:**

- `has_role(role: str) -> bool` - Check if user has a role
- `to_dict() -> dict` - Convert to dictionary

### AuthResult

Authentication result.

```python
@dataclass
class AuthResult:
    success: bool
    user: Optional[User] = None
    message: str = ""
    error_code: Optional[str] = None
```

---

## Security Considerations

### ⚠️ Important Security Notes

#### 1. **Use HTTPS in Production**

HTTP Basic Auth transmits credentials as Base64-encoded text, which is **not encryption**. Always use HTTPS in production.

```python
# Good: Use with HTTPS
https://user:pass@example.com

# Bad: Unencrypted
http://user:pass@example.com
```

#### 2. **Built-in Password Hashing (Bcrypt)**

**As of v1.0.0+, bcrypt password hashing is enabled by default.** All passwords are automatically hashed and verified using bcrypt with 12 salt rounds.

When you add users:

```python
auth_manager.add_user('admin', 'my_password')
# Password is automatically hashed and stored as: $2b$12$...
```

When users authenticate:

```python
result = auth_manager.verify_credentials('admin', 'my_password')
# Password is automatically verified against the bcrypt hash
```

**For existing projects:** If you have plaintext passwords in YAML files, run the migration script:

```bash
python scripts/migrate_passwords.py your_users.yaml
```

See [MIGRATION.md](MIGRATION.md) for detailed migration instructions.

**Custom hash functions:** If you need a different hashing algorithm, you can still provide a custom function:

```python
from argon2 import PasswordHasher

hasher = PasswordHasher()

def verify_with_argon2(password, hash):
    try:
        hasher.verify(hash, password)
        return True
    except:
        return False

auth_manager = AuthManager(config, hash_function=verify_with_argon2, use_hashing=False)
```

Your `users.yaml` should contain bcrypt hashes:

```yaml
users:
  admin: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
```

#### 3. **Store Credentials Securely**

**Never commit credentials to version control:**

```bash
# Add to .gitignore
config/users.yaml
.env
```

**Use environment variables instead:**

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=secure_password
```

#### 4. **Implement Rate Limiting**

Protect against brute force attacks:

```python
# Flask example with flask-limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/auth/test', methods=['POST'])
@limiter.limit("5 per minute")
def auth_test():
    # Authentication endpoint
    pass
```

#### 5. **Log Authentication Events**

Monitor failed attempts:

```python
auth_manager = AuthManager(
    config,
    logger=auth_logger
)

# All attempts are logged with:
# - Username
# - IP address
# - Success/failure
# - Error code
```

#### 6. **Use CORS Carefully**

If your API is accessed from browsers, configure CORS properly:

```python
# Flask example
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://trusted-domain.com"])
```

---

## Audit Logging

### Track User Operations

AuthService provides comprehensive audit logging to track all user management operations. This is essential for security and compliance.

### Enable Audit Logging

```python
from authtemplate import AuthManager, AuthConfig, setup_logger

# Create logger with separate audit log file
logger = setup_logger(
    name="AuthManager",
    log_file="logs/auth.log",
    audit_log_file="logs/audit.log"  # Separate audit trail
)

config = AuthConfig(yaml_file='users.yaml')
auth_manager = AuthManager(config, logger=logger)

# Add user (automatically logged to audit.log)
auth_manager.add_user('newuser', 'password', by_whom='admin', ip_address='192.168.1.1')

# Remove user (automatically logged to audit.log)
auth_manager.remove_user('olduser', by_whom='admin', ip_address='192.168.1.1')
```

### Audit Log Format

Audit log entries include:

```
[AUDIT] 2025-01-10 19:30:45 - USER_ADDED: username=newuser, by=admin, ip=192.168.1.1
[AUDIT] 2025-01-10 19:31:20 - USER_REMOVED: username=olduser, by=admin, ip=192.168.1.1
[AUDIT] 2025-01-10 19:32:10 - PASSWORD_CHANGED: username=existinguser, by=user, ip=192.168.1.50
```

### Audit Log Events

The following events are automatically logged:

- **USER_ADDED** - When a new user is added
- **USER_REMOVED** - When a user is removed
- **USER_MODIFIED** - When user properties are changed
- **PASSWORD_CHANGED** - When a password is changed

Each entry includes:
- **Timestamp** - When the action occurred
- **Event type** - What operation was performed
- **username** - The user affected
- **by** - Who performed the action (for accountability)
- **ip** - Source IP address (for tracking)

### Filtering and Analyzing Audit Logs

```bash
# View all user additions
grep "USER_ADDED" logs/audit.log

# View changes by admin
grep "by=admin" logs/audit.log

# View all operations on a specific user
grep "username=admin" logs/audit.log

# Parse JSON-style output (with custom processing)
cat logs/audit.log | grep USER_ADDED | wc -l  # Count additions
```

---

## Advanced Usage

### Custom Password Hashing

Use bcrypt or Argon2:

```python
import bcrypt
from authtemplate import AuthManager, AuthConfig

def verify_bcrypt(provided: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(provided.encode(), hashed.encode())

config = AuthConfig(yaml_file='users.yaml')
auth_manager = AuthManager(
    config,
    hash_function=verify_bcrypt
)
```

### Role-Based Access Control (RBAC)

```python
# models.py
@dataclass
class User:
    username: str
    roles: list = field(default_factory=lambda: ["user"])

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        # Map roles to permissions
        role_permissions = {
            'admin': ['read', 'write', 'delete'],
            'user': ['read']
        }

        for role in self.roles:
            if permission in role_permissions.get(role, []):
                return True
        return False

# In your route
@require_auth
def delete_file(request):
    if not g.user.has_permission('delete'):
        return {'error': 'Permission denied'}, 403

    # Delete logic here
    pass
```

### Custom User Model

Extend the User class:

```python
from authtemplate.models import User
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CustomUser(User):
    department: str = ""
    manager: str = ""
    phone: str = ""

    def get_manager_email(self):
        # Custom logic
        pass
```

### Middleware-Based Authentication (Express)

```javascript
const authMiddleware = (req, res, next) => {
    const credentials = basicAuth(req);

    if (!credentials) {
        res.statusCode = 401;
        res.setHeader('WWW-Authenticate', 'Basic realm="app"');
        return res.json({error: 'Authentication required'});
    }

    const result = authManager.verifyCredentials(
        credentials.name,
        credentials.pass,
        req.ip
    );

    if (!result.success) {
        return res.status(401).json({error: 'Invalid credentials'});
    }

    req.user = result.user;
    next();
};

// Apply to all routes
app.use(authMiddleware);

// Or specific routes
app.get('/protected', authMiddleware, (req, res) => {
    res.json({user: req.user.username});
});
```

### Multi-Tenant Authentication

```python
class AuthConfig:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        yaml_file = f'config/users_{tenant_id}.yaml'
        super().__init__(yaml_file=yaml_file)

# Usage
tenant_1_config = AuthConfig('tenant1')
tenant_1_auth = AuthManager(tenant_1_config)

tenant_2_config = AuthConfig('tenant2')
tenant_2_auth = AuthManager(tenant_2_config)
```

---

## Troubleshooting

### "No users configured" Error

**Issue:** AuthConfig.validate() raises ValueError

**Solution:** Check that users.yaml exists and is properly formatted:

```yaml
users:
  admin: password
```

Or set environment variables:

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=password
```

### Invalid Authorization Header

**Issue:** "Invalid base64 encoding in authorization header"

**Solution:** Ensure header is formatted correctly:

```
Authorization: Basic base64(username:password)

# Example:
Authorization: Basic YWRtaW46cGFzc3dvcmQ=
```

### Users Not Loading from YAML

**Issue:** AuthManager lists 0 users despite YAML file existing

**Solution:** Check YAML syntax:

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('users.yaml'))"
```

Ensure correct structure:

```yaml
# Correct
users:
  admin: password

# Also correct (flat)
admin: password

# Incorrect (missing key)
admin: password
user1: password
```

### Logging Not Working

**Issue:** No log output from AuthManager

**Solution:** Ensure logger is set up:

```python
from authtemplate import setup_logger, AuthLogger, AuthManager

logger = setup_logger('MyAuth', log_file='logs/auth.log')
auth_logger = AuthLogger(logger)
auth_manager = AuthManager(config, logger=auth_logger)
```

### Performance Issues

**Issue:** Authentication requests are slow

**Solution:** The config loads from YAML once and caches. If slow:

1. Check disk I/O (reduce refresh rate)
2. Use environment variables instead of YAML
3. Consider database backend for large user bases

```python
# Reload users periodically
auth_manager.reload_users()  # Only call when needed
```

---

## Migration Guide

### From Flask-HTTPAuth

If you're using Flask-HTTPAuth directly:

**Before:**

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    user = load_user(username)
    return user and user.check_password(password)

@app.route('/api')
@auth.login_required
def api():
    return f"Hello, {auth.current_user()}"
```

**After:**

```python
from authtemplate import AuthManager, AuthConfig

auth_manager = AuthManager(AuthConfig(yaml_file='users.yaml'))

@require_auth
def api():
    return f"Hello, {g.user.username}"
```

Benefits:
- Framework-agnostic (not locked to Flask)
- YAML/ENV configuration instead of code
- Built-in logging
- Easier testing

### From Custom Auth System

If you have custom authentication code:

1. Create `config/users.yaml` with your users
2. Replace your verification logic with AuthManager
3. Use provided decorators/middleware
4. Remove custom logger code (use AuthTemplate logger)

---

## Best Practices

1. **Separate Configuration from Code**
   - Use YAML for users, environment for secrets

2. **Always Log Authentication Attempts**
   - Helps detect attacks and debug issues

3. **Hash Passwords in Production**
   - Use bcrypt, never plaintext

4. **Implement Rate Limiting**
   - Prevent brute force attacks

5. **Use HTTPS Always**
   - Basic Auth sends credentials in headers

6. **Document Your Integration**
   - Help future developers understand the auth flow

7. **Test Authentication Thoroughly**
   - Include both success and failure cases

8. **Monitor Failed Attempts**
   - Alert on suspicious patterns

---

## Support & Contributing

For issues, questions, or contributions:

1. **Report Issues**: Check existing documentation and framework examples
2. **Contribute**: Add new framework examples or improve existing code
3. **Security**: Report vulnerabilities privately, don't create public issues

---

## License

AuthTemplate is provided as-is for integration into your projects.

---

## Summary

| Aspect | Details |
|--------|---------|
| **Size** | ~500 lines of Python |
| **Dependencies** | None (standard library only) |
| **Setup Time** | 5-15 minutes |
| **Frameworks** | Flask, Express, Django, Spring Boot, FastAPI, etc. |
| **Auth Methods** | HTTP Basic Auth (extensible) |
| **Configuration** | YAML, environment variables, in-memory |
| **Security** | Plaintext storage (use bcrypt in production) |
| **Logging** | Built-in comprehensive logging |
| **Testing** | Framework examples included |

**Get started now:** Copy the `authtemplate` folder to your project and follow the framework-specific examples!
