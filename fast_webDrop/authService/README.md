# AuthService

**Production-ready, framework-agnostic authentication library for Python projects.**

AuthService provides secure, simple authentication that works with any web framework. Built with security best practices, it protects against timing attacks and username enumeration while providing a clean, modular API.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Why AuthService?

- **Framework-Agnostic** - Works with Flask, Django, FastAPI, or any Python framework
- **Security-First** - Timing attack protection, username enumeration prevention, bcrypt hashing
- **Simple Integration** - Get authentication running in 5 minutes
- **Production-Ready** - Comprehensive audit logging, password management, persistence
- **Modular Design** - Clean separation of concerns, easy to extend

---

## Features

✅ **Security Built-In**
- Constant-time password comparison (timing attack protection)
- Username enumeration prevention
- Bcrypt password hashing (12 rounds default)
- Inactive account blocking

✅ **Flexible Configuration**
- YAML files (simple & extended format)
- Environment variables
- In-memory configuration
- User metadata (roles, email, custom fields)

✅ **User Management**
- Add/remove users at runtime
- Password change functionality
- Persistence layer (save to YAML)
- User metadata and roles

✅ **Audit Logging**
- Track all user operations
- Separate audit log file
- Compliance-ready

✅ **Framework Support**
- Flask examples included
- Django examples included
- FastAPI compatible
- Express.js reference

---

## Quick Start

### Installation

```bash
pip install authservice
```

Or install in development mode:

```bash
git clone <repository>
cd authService
pip install -e .
```

### 30-Second Example

```python
from authservice import AuthManager, AuthConfig

# 1. Configure (users.yaml with bcrypt hashes)
config = AuthConfig(yaml_file='users.yaml')

# 2. Create auth manager
auth = AuthManager(config)

# 3. Authenticate
result = auth.verify_credentials('admin', 'password')

if result.success:
    print(f"Welcome, {result.user.username}!")
    print(f"Roles: {result.user.roles}")
else:
    print(f"Failed: {result.message}")
```

### Flask Integration (5 lines)

```python
from flask import Flask, request, g, jsonify
from authservice import AuthManager, AuthConfig
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
    return jsonify({'user': g.user.username, 'roles': g.user.roles})
```

**Test it:**

```bash
curl -u admin:password http://localhost:5000/protected
```

---

## Configuration

### Simple YAML Format

```yaml
users:
  admin: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
  user1: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
```

### Extended YAML Format (with metadata)

```yaml
users:
  admin:
    password: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
    is_active: true
    roles: [admin, user]
    email: admin@example.com
    metadata:
      department: IT

  user1:
    password: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
    is_active: true
    roles: [user]
    email: user1@example.com
```

### Environment Variables

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=secure_password
```

```python
config = AuthConfig(use_env_vars=True)
```

---

## Security Features

### Timing Attack Protection

AuthService uses constant-time password comparison to prevent timing attacks:

```python
# Always performs password verification, even for non-existent users
# Uses dummy hash to maintain constant timing
stored_password = self.users.get(username, DUMMY_HASH)
password_valid = self._compare_passwords(password, stored_password)
```

### Username Enumeration Prevention

Returns the same error code for both non-existent users and wrong passwords:

```python
result = auth.verify_credentials('fake_user', 'password')
# Returns: error_code='INVALID_CREDENTIALS'

result = auth.verify_credentials('real_user', 'wrong_password')
# Returns: error_code='INVALID_CREDENTIALS' (same code)
```

### Inactive Account Blocking

```python
# In YAML:
users:
  suspended_user:
    password: $2b$12$hash...
    is_active: false  # Account disabled

# Authentication result:
result = auth.verify_credentials('suspended_user', 'correct_password')
# Returns: error_code='USER_DISABLED'
```

---

## User Management

### Add Users

```python
# Password is automatically hashed
auth.add_user('newuser', 'plaintext_password')

# Authenticate immediately
result = auth.verify_credentials('newuser', 'plaintext_password')
print(result.success)  # True
```

### Change Passwords

```python
# Change password with audit logging
auth.change_password('admin', 'new_secure_password', by_whom='admin')
```

### Persist Changes

```python
# Save in-memory changes back to YAML
auth.add_user('newuser', 'password')
auth.change_password('admin', 'new_password')
auth.persist_changes()  # Writes to YAML file
```

### List Users

```python
users = auth.list_users()
print(users)  # ['admin', 'user1', 'newuser']
```

---

## Framework Examples

### Flask

See `examples/flask_example.py` for complete working example with:
- Decorator-based route protection
- HTTP Basic Auth
- User info endpoints

### Django

See `examples/django_example.py` for complete working example with:
- Decorator for function-based views
- Class-based view support
- Django integration patterns

### FastAPI

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from authservice import AuthManager, AuthConfig

app = FastAPI()
security = HTTPBasic()
auth_manager = AuthManager(AuthConfig(yaml_file='users.yaml'))

def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    result = auth_manager.verify_credentials(
        credentials.username,
        credentials.password
    )
    if not result.success:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result.user

@app.get("/protected")
def protected(user = Depends(verify_auth)):
    return {"user": user.username, "roles": user.roles}
```

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step getting started guide
- **[TECHNICAL.md](TECHNICAL.md)** - Complete API reference and implementation details

---

## Migration from Plaintext Passwords

If you have existing plaintext passwords in YAML files:

```bash
python scripts/migrate_passwords.py config/users.yaml
```

This creates a backup (.bak) and converts all passwords to bcrypt hashes.

---

## Security Considerations

⚠️ **Always use HTTPS in production** - HTTP Basic Auth transmits credentials in headers

⚠️ **Store credentials securely** - Never commit `users.yaml` to version control

⚠️ **Implement rate limiting** - Protect against brute force attacks

⚠️ **Monitor audit logs** - Track suspicious authentication patterns

See [TECHNICAL.md](TECHNICAL.md) for detailed security implementation.

---

## Testing

Run the test suite:

```bash
source ~/.venv_gen/bin/activate
python -m unittest discover tests -v
```

All 122 tests should pass:
- Authentication tests
- Security tests (timing attack protection)
- Extended YAML format tests
- Password change tests
- Persistence tests

---

## API Overview

### AuthManager

```python
# Initialize
auth = AuthManager(config)

# Authenticate
result = auth.verify_credentials(username, password, ip_address)
result = auth.verify_basic_auth_header(auth_header, ip_address)

# User management
auth.add_user(username, password, by_whom, ip_address)
auth.remove_user(username, by_whom, ip_address)
auth.change_password(username, new_password, by_whom, ip_address)
auth.persist_changes()

# Information
users = auth.list_users()
info = auth.get_user_info(username)
```

### AuthConfig

```python
# Initialize
config = AuthConfig(yaml_file='users.yaml')
config = AuthConfig(use_env_vars=True)

# Access
users = config.get_users()
password = config.get_user_password(username)
metadata = config.get_user_metadata(username)

# Management
config.reload()
config.validate(strict=True)
config.save_users(filepath)
```

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/authService/issues)
- **Documentation**: [TECHNICAL.md](TECHNICAL.md)
- **Examples**: See `examples/` directory

---

## Summary

AuthService provides production-ready authentication with:
- ✅ Security best practices built-in
- ✅ 5-minute integration
- ✅ Works with any Python framework
- ✅ Comprehensive audit logging
- ✅ User management with persistence

**Get started:** `pip install authservice` and see [QUICKSTART.md](QUICKSTART.md)
