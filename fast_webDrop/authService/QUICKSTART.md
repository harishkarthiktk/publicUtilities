# AuthService - Quick Start Guide

Get authentication up and running in your project in **10 minutes**.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Create User Configuration](#2-create-user-configuration)
3. [Basic Usage](#3-basic-usage)
4. [Framework Integration](#4-framework-integration)
5. [Common Tasks](#5-common-tasks)
6. [Enable Audit Logging](#6-enable-audit-logging)
7. [Next Steps](#7-next-steps)

---

## 1. Installation

### Install from PyPI

```bash
pip install authservice
```

### Install from Source

```bash
git clone https://github.com/yourusername/authService.git
cd authService
pip install -e .
```

### Verify Installation

```bash
python -c "from authservice import AuthManager; print('AuthService installed successfully!')"
```

---

## 2. Create User Configuration

### Option A: YAML File (Recommended)

Create `config/users.yaml`:

```yaml
users:
  admin: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
  user1: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
  developer: $2b$12$uVPJhDDZPjpCxKI/3KX1QOHs.XdkFKC8KbIvlvxdR0KHAhAZ2Pkyq
```

**Note:** These are bcrypt hashes. Use `hash_password()` to generate them:

```python
from authservice import hash_password

print(hash_password('my_password'))
# Output: $2b$12$... (use this in YAML)
```

### Option B: Environment Variables

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=admin_password
```

### Option C: In-Memory (Testing Only)

```python
from authservice import AuthConfig

config = AuthConfig()
config.set_users({
    'admin': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK',
    'user1': '$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm'
})
```

### Extended YAML Format (with Metadata)

For advanced features like roles, email, and user metadata:

```yaml
users:
  admin:
    password: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
    is_active: true
    roles: [admin, manager]
    email: admin@example.com
    metadata:
      department: IT
      employee_id: E001

  user1:
    password: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
    is_active: true
    roles: [user]
    email: user1@example.com

  suspended:
    password: $2b$12$...
    is_active: false  # Account disabled
    roles: [user]
```

---

## 3. Basic Usage

### Minimal Example

```python
from authservice import AuthManager, AuthConfig

# 1. Load configuration
config = AuthConfig(yaml_file='config/users.yaml')

# 2. Create auth manager
auth = AuthManager(config)

# 3. Verify credentials
result = auth.verify_credentials('admin', 'admin_password', ip_address='127.0.0.1')

if result.success:
    print(f"✓ Authentication successful")
    print(f"  User: {result.user.username}")
    print(f"  Roles: {result.user.roles}")
    print(f"  Email: {result.user.email}")
else:
    print(f"✗ Authentication failed")
    print(f"  Error: {result.message}")
    print(f"  Code: {result.error_code}")
```

### HTTP Basic Auth

```python
# Parse Authorization header
auth_header = "Basic YWRtaW46cGFzc3dvcmQ="  # Base64 of "admin:password"
result = auth.verify_basic_auth_header(auth_header, ip_address='192.168.1.1')

if result.success:
    print(f"Authenticated: {result.user.username}")
```

---

## 4. Framework Integration

### Flask (10 lines)

```python
from flask import Flask, request, g, jsonify
from authservice import AuthManager, AuthConfig
from functools import wraps

app = Flask(__name__)
auth_manager = AuthManager(AuthConfig(yaml_file='config/users.yaml'))

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

@app.route('/api/protected')
@require_auth
def protected():
    return jsonify({
        'user': g.user.username,
        'roles': g.user.roles,
        'email': g.user.email
    })

@app.route('/api/public')
def public():
    return jsonify({'message': 'This endpoint is public'})

if __name__ == '__main__':
    app.run(debug=True)
```

**Test with curl:**

```bash
# Public endpoint (no auth needed)
curl http://localhost:5000/api/public

# Protected endpoint (requires auth)
curl -u admin:admin_password http://localhost:5000/api/protected
```

### Django

Create `auth_middleware.py`:

```python
from authservice import AuthManager, AuthConfig
from django.http import JsonResponse
from functools import wraps

auth_manager = AuthManager(AuthConfig(yaml_file='config/users.yaml'))

def require_auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Basic '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        result = auth_manager.verify_basic_auth_header(auth_header)
        if not result.success:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        request.auth_user = result.user
        return view_func(request, *args, **kwargs)

    return wrapper
```

Use in `views.py`:

```python
from django.http import JsonResponse
from .auth_middleware import require_auth

@require_auth
def protected_view(request):
    return JsonResponse({
        'user': request.auth_user.username,
        'roles': request.auth_user.roles
    })

def public_view(request):
    return JsonResponse({'message': 'This is public'})
```

### FastAPI

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from authservice import AuthManager, AuthConfig

app = FastAPI()
security = HTTPBasic()
auth_manager = AuthManager(AuthConfig(yaml_file='config/users.yaml'))

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    result = auth_manager.verify_credentials(
        credentials.username,
        credentials.password
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return result.user

@app.get("/api/protected")
def protected(user = Depends(get_current_user)):
    return {
        "user": user.username,
        "roles": user.roles,
        "email": user.email
    }

@app.get("/api/public")
def public():
    return {"message": "This is public"}
```

**Test with curl:**

```bash
curl -u admin:admin_password http://localhost:8000/api/protected
```

---

## 5. Common Tasks

### Add User at Runtime

```python
# Password is automatically hashed
success = auth.add_user('newuser', 'secure_password', by_whom='admin')

if success:
    print("✓ User added successfully")
else:
    print("✗ User already exists")

# Verify immediately
result = auth.verify_credentials('newuser', 'secure_password')
print(f"Can authenticate: {result.success}")
```

### Change Password

```python
success = auth.change_password(
    'admin',
    'new_secure_password',
    by_whom='admin',
    ip_address='192.168.1.1'
)

if success:
    print("✓ Password changed")
    # Old password no longer works
    # New password works immediately
```

### Persist Changes to YAML

```python
# Make changes in-memory
auth.add_user('user2', 'password2')
auth.change_password('admin', 'new_password')

# Save all changes back to YAML file
auth.persist_changes()

# Reload to verify
auth2 = AuthManager(AuthConfig(yaml_file='config/users.yaml'))
print(auth2.list_users())  # Shows 'user2'
```

### List All Users

```python
users = auth.list_users()
print(f"Configured users: {users}")
# Output: ['admin', 'user1', 'developer']
```

### Get User Information

```python
info = auth.get_user_info('admin')
print(info)
# Output: {'username': 'admin', 'exists': True, 'is_active': True}
```

### Check User Roles

```python
result = auth.verify_credentials('admin', 'admin_password')

if result.success:
    user = result.user

    # Check specific role
    if user.has_role('admin'):
        print("User is an admin")

    # List all roles
    print(f"User roles: {user.roles}")
```

---

## 6. Enable Audit Logging

Track all user operations for security and compliance:

```python
from authservice import AuthManager, AuthConfig, setup_logger

# Create logger with separate audit log
logger = setup_logger(
    name='AuthManager',
    log_file='logs/auth.log',
    audit_log_file='logs/audit.log'  # Separate audit trail
)

config = AuthConfig(yaml_file='config/users.yaml')
auth = AuthManager(config, logger=logger)

# All operations are automatically logged
auth.add_user('newuser', 'password', by_whom='admin', ip_address='192.168.1.1')
auth.remove_user('olduser', by_whom='admin', ip_address='192.168.1.1')
auth.change_password('admin', 'newpass', by_whom='admin', ip_address='192.168.1.1')
```

**View audit log:**

```bash
# See all user additions
grep "USER_ADDED" logs/audit.log

# See changes by admin
grep "by=admin" logs/audit.log

# See all operations on a specific user
grep "username=admin" logs/audit.log
```

**Audit log format:**

```
[AUDIT] 2026-01-22 10:15:30 - USER_ADDED: username=newuser, by=admin, ip=192.168.1.1
[AUDIT] 2026-01-22 10:16:45 - PASSWORD_CHANGED: username=admin, by=admin, ip=192.168.1.1
[AUDIT] 2026-01-22 10:17:20 - USER_REMOVED: username=olduser, by=admin, ip=192.168.1.1
```

---

## 7. Next Steps

### Security Best Practices

1. **Use HTTPS in production** - Never use HTTP Basic Auth over HTTP
2. **Store credentials securely** - Add `config/users.yaml` to `.gitignore`
3. **Implement rate limiting** - Protect against brute force attacks
4. **Monitor audit logs** - Set up alerts for suspicious activity

### Advanced Features

Explore advanced features in [TECHNICAL.md](TECHNICAL.md):

- Custom password hashing algorithms
- Role-based access control (RBAC)
- Multi-tenant authentication
- Custom user models
- Integration with databases

### Framework Examples

Check the `examples/` directory for complete working examples:

- `examples/flask_example.py` - Full Flask integration
- `examples/django_example.py` - Full Django integration

### Migrate Existing Passwords

If you have plaintext passwords in YAML:

```bash
python scripts/migrate_passwords.py config/users.yaml
```

This creates a backup and converts all passwords to bcrypt hashes.

---

## Troubleshooting

### "No users configured" Error

**Solution:** Check that `config/users.yaml` exists and has valid YAML:

```yaml
users:
  admin: $2b$12$...
```

Or use environment variables:

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=password
```

### "Invalid credentials" Always Fails

**Solution:** Ensure passwords in YAML are bcrypt hashes, not plaintext:

```python
from authservice import hash_password

# Generate hash
hashed = hash_password('my_password')
print(hashed)  # Use this in YAML
```

### ImportError: No module named 'authservice'

**Solution:** Install the package:

```bash
pip install -e .
```

Or add to Python path:

```python
import sys
sys.path.insert(0, '/path/to/authService')
from authservice import AuthManager
```

### Authentication is Slow

**Solution:** Reduce bcrypt rounds for development (in extended YAML or AppConfig):

```python
# Default is 12 rounds (standard security)
# For faster testing, you can adjust in code:
from authservice import hash_password
hash_password('password', rounds=10)  # Faster, less secure
```

---

## You're Done!

Your application now has secure authentication. You can:

✅ Authenticate users with bcrypt-hashed passwords
✅ Protect routes/endpoints with decorators
✅ Manage users (add/remove/change passwords)
✅ Track operations with audit logging
✅ Support user metadata and roles

**Next:** Read [TECHNICAL.md](TECHNICAL.md) for complete API reference and advanced features.

---

## Quick Reference

```python
# Import
from authservice import AuthManager, AuthConfig, setup_logger, hash_password

# Setup
config = AuthConfig(yaml_file='users.yaml')
auth = AuthManager(config)

# Authenticate
result = auth.verify_credentials(username, password, ip)
result = auth.verify_basic_auth_header(auth_header, ip)

# Manage
auth.add_user(username, password, by_whom, ip)
auth.remove_user(username, by_whom, ip)
auth.change_password(username, new_password, by_whom, ip)
auth.persist_changes()

# Query
users = auth.list_users()
info = auth.get_user_info(username)
```

**For more details, see [TECHNICAL.md](TECHNICAL.md)**
