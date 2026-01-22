# Authentication Usage Guide

This document explains how authentication is implemented in FastWebDrop using the `authService` module.

## Overview

FastWebDrop uses HTTP Basic Authentication with bcrypt password hashing. The authentication system is built on the `authService` module, which provides:

- Bcrypt password hashing (12 rounds by default)
- HTTP Basic Auth header parsing and verification
- User metadata and roles support
- Comprehensive audit logging
- File-based user configuration (YAML)

## Architecture

### Files

- `fast_api_main.py` - FastAPI backend with protected endpoints
- `users.yaml` - User configuration with bcrypt-hashed passwords
- `manage_users.py` - CLI utility for user management
- `logs/auth.log` - Authentication audit log

### User Configuration Format

The `users.yaml` file supports an extended format with metadata:

```yaml
users:
  admin:
    password: $2b$12$...bcrypt_hash...
    is_active: true
    roles:
      - admin
      - manager
    email: admin@example.com
    metadata:
      department: IT
      notes: Administrator account
```

Fields:
- `password` - Bcrypt hash (starts with `$2b$`)
- `is_active` - Boolean, enables/disables user
- `roles` - List of role strings (for authorization)
- `email` - User email address
- `metadata` - Free-form metadata dictionary

## Test Users

Three test users are pre-configured in `users.yaml`:

| Username | Password | Roles |
|----------|----------|-------|
| admin | admin123 | admin, manager |
| user1 | user123 | user |
| developer | dev@secure! | user, developer |

## Managing Users

### Add a New User

```bash
python manage_users.py add <username> <password> [--email EMAIL] [--role ROLE]
```

Examples:
```bash
# Simple user
python manage_users.py add alice mypass123

# With email and roles
python manage_users.py add bob secure_pwd --email bob@example.com --role user --role admin
```

### Remove a User

```bash
python manage_users.py remove <username>
```

### Change Password

```bash
python manage_users.py change-password <username> <new_password>
```

### List All Users

```bash
python manage_users.py list
```

Output:
```
Found 3 user(s):

  admin
    - Email: admin@example.com
    - Roles: admin, manager
    - Status: Active

  user1
    - Email: user1@example.com
    - Roles: user
    - Status: Active

  developer
    - Email: developer@example.com
    - Roles: user, developer
    - Status: Active
```

### View User Details

```bash
python manage_users.py info <username>
```

## Using the Application

### Login

1. Navigate to `http://localhost:8000`
2. Login modal appears
3. Enter username and password (e.g., `admin` / `admin123`)
4. Click "Login"
5. Credentials stored in browser localStorage (24-hour expiration)

### Making API Calls

All data-modifying endpoints require HTTP Basic Auth:

```bash
# Export links as JSON (requires auth)
curl -u admin:admin123 http://localhost:8000/export-json

# Add a new link (requires auth)
curl -u admin:admin123 -X POST http://localhost:8000/add-link \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Protected Endpoints

These endpoints require HTTP Basic Authentication:

- `POST /add-link` - Add new link
- `POST /delete-link` - Delete link
- `POST /update-category` - Update link category
- `GET /export-json` - Export as JSON
- `GET /export-csv` - Export as CSV
- `GET /export-html` - Export as HTML
- `POST /import-links` - Import links from file

### Public Endpoints

These endpoints do NOT require authentication:

- `GET /` - Home page with embedded links
- `GET /favicon.svg` - Favicon

## Authentication Flow

```
1. Client navigates to /
   ↓
2. Frontend checks localStorage for stored credentials
   ↓
3. If no credentials or expired (>24h): Show login modal
   ↓
4. User submits username/password
   ↓
5. Frontend creates Basic Auth header: Authorization: Basic <base64>
   ↓
6. Frontend sends test request to verify credentials
   ↓
7. AuthManager verifies credentials against users.yaml:
   - Looks up user
   - Verifies password using bcrypt.checkpw()
   - Checks if user is active
   ↓
8. On success:
   - AuthLogger logs attempt (auth.log)
   - User object returned with metadata/roles
   - Frontend stores credentials in localStorage
   - Page reloads and shows links
   ↓
9. On failure:
   - AuthLogger logs failed attempt
   - 401 Unauthorized response
   - Frontend shows error and keeps login modal open
   ↓
10. All subsequent API calls include Authorization header
```

## Logging

Authentication events are logged to `logs/auth.log` with rotation:

- Max file size: 5MB
- Backups: 5 files retained
- Level: INFO

Log entries include:

```
[2024-01-22 15:30:45] AUTH_ATTEMPT username=admin ip=127.0.0.1 success=True
[2024-01-22 15:35:12] INVALID_CREDENTIALS username=baduser ip=192.168.1.100
[2024-01-22 15:40:00] USER_NOT_FOUND username=unknown ip=10.0.0.5
```

## Password Hashing

Passwords are hashed using bcrypt with 12 rounds. To manually generate a bcrypt hash:

```python
from authService import hash_password

# Generate hash
password_hash = hash_password("mypassword", rounds=12)
print(password_hash)  # $2b$12$...
```

## Production Considerations

### Security

1. **Use environment variables for passwords in production:**
   ```bash
   export AUTH_USER=admin
   export AUTH_PASSWORD=secure_password
   uvicorn fast_api_main.py --host 0.0.0.0 --port 8000
   ```

2. **Rotate users.yaml:**
   - Keep in `.gitignore` (never commit user passwords)
   - Use encrypted secrets management for production
   - Regularly audit `logs/auth.log`

3. **HTTPS required:**
   - Always use HTTPS in production (Basic Auth sends base64-encoded credentials)
   - Never use HTTP for authenticated requests

4. **Session timeout:**
   - Frontend credentials expire after 24 hours
   - Implement server-side session management for longer sessions

### Adding Custom Roles

Modify `users.yaml` to add custom roles:

```yaml
users:
  john:
    password: $2b$12$...
    roles:
      - user
      - editor
      - reviewer
```

Then check roles in FastAPI:

```python
@app.get("/admin-panel")
async def admin_panel(user = Depends(verify_auth)):
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"message": "Admin panel"}
```

## Troubleshooting

### "Invalid credentials" error

1. Verify username exists: `python manage_users.py list`
2. Verify password is correct (note: passwords are case-sensitive)
3. Check auth log: `tail -f logs/auth.log`

### Login modal stays open

1. Check browser console for errors
2. Verify FastAPI server is running: `python fast_api_main.py`
3. Clear browser localStorage and try again

### User account disabled

1. Check `users.yaml` - ensure `is_active: true`
2. Update if needed and run: `python manage_users.py info <username>`

## References

- [authService Documentation](./authService/README.md)
- [AuthManager API](./authService/TECHNICAL.md)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/http-basic-auth/)
