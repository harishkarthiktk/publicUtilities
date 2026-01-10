# Migration Guide: Plaintext to Bcrypt Hashes

This guide explains how to migrate existing projects using authService with plaintext passwords to the new secure bcrypt hashing system.

## What's Changing

As of version 1.0.0+, authService now uses **bcrypt password hashing by default**. All passwords must be stored as bcrypt hashes - plaintext passwords will no longer be accepted for authentication.

### Why This Change?

- **Security**: Bcrypt is a modern, industry-standard password hashing algorithm with built-in salt and configurable complexity
- **Compliance**: Meets OWASP recommendations for password storage
- **Safety by Default**: New installations are secure by default
- **Production Ready**: No more warnings about plaintext passwords

## Migration Path

### Step 1: Install Dependencies

Ensure bcrypt is installed:

```bash
pip install -r requirements.txt
```

Or:

```bash
pip install bcrypt>=4.0.1
```

### Step 2: Backup Your Files

Before migrating, create backups of your user configuration files:

```bash
cp example_users.yaml example_users.yaml.backup
```

### Step 3: Run Migration Script

Use the provided migration script to automatically hash all plaintext passwords:

```bash
python scripts/migrate_passwords.py example_users.yaml
```

**What the script does:**
- Reads your YAML file
- Identifies plaintext passwords (those not in bcrypt format)
- Creates a backup file with `.bak` extension
- Converts all plaintext passwords to bcrypt hashes
- Validates the migration was successful

**Example output:**

```
📋 Migration Report for: example_users.yaml
   Total users: 2
   Already hashed: 0
   Need migration: 2

🔄 Migrating 2 passwords...
   ✓ Backup created: example_users.yaml.bak

✅ Migration complete!
   File updated: example_users.yaml
   2 passwords hashed with bcrypt
   ✓ Verification passed: all 2 passwords verified as hashed
```

### Step 4: Verify Migration

Check that your YAML file now contains bcrypt hashes:

```bash
# Before migration (plaintext):
users:
  admin: admin_password
  user1: user1_password

# After migration (bcrypt):
users:
  admin: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
  user1: $2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
```

### Step 5: Test Authentication

Test that authentication still works with the new hashed passwords:

```python
from core import AuthManager
from config import AuthConfig
from logger import setup_logger

config = AuthConfig(yaml_file='example_users.yaml')
logger = setup_logger()
manager = AuthManager(config, logger)

# Test authentication
result = manager.verify_credentials('admin', 'admin_password')
print(f"Auth successful: {result.success}")  # Should print: Auth successful: True
```

### Step 6: Update Code (if necessary)

If you call `add_user()` or `remove_user()` methods, update parameter usage:

**Before:**
```python
manager.add_user('newuser', 'password123')
manager.remove_user('olduser')
```

**After (same code works):**
```python
# Passwords are automatically hashed with bcrypt
manager.add_user('newuser', 'password123')
# Passwords are logged to audit log
manager.remove_user('olduser')
```

Optional: You can now specify who performed the action (for audit logging):
```python
manager.add_user('newuser', 'password123', by_whom='admin', ip_address='192.168.1.1')
manager.remove_user('olduser', by_whom='admin', ip_address='192.168.1.1')
```

### Step 7: Deploy Updated Code

1. Update to the latest version of authService
2. Replace your `example_users.yaml` with the migrated version
3. Restart your application
4. Test login functionality

## Manual Migration (Environment Variables)

If you use environment variables for credentials:

**Before:**
```bash
export AUTH_USER=admin
export AUTH_PASSWORD=admin_password
```

**After:**
You'll need to hash the password manually:

```python
from hashing import hash_password

password_hash = hash_password('admin_password')
print(password_hash)
# Output: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK

# Then use in environment:
# export AUTH_PASSWORD=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
```

Or create a simple script:

```python
import os
import sys
from hashing import hash_password

password = os.getenv('AUTH_PASSWORD_PLAIN')
if password:
    hashed = hash_password(password)
    print(f"Set AUTH_PASSWORD={hashed}")
```

## Rollback Instructions

If you need to rollback to plaintext passwords:

1. **Restore from backup:**
   ```bash
   cp example_users.yaml.bak example_users.yaml
   ```

2. **Downgrade authService:**
   ```bash
   pip install authService==0.9.0  # Previous version
   ```

3. **Restart application**

**Note:** Rolling back means losing the security improvements. We don't recommend this.

## Troubleshooting

### "Plaintext password detected" Error

**Error message:**
```
ERROR - Plaintext password detected for verification. Run migration script: python scripts/migrate_passwords.py
```

**Solution:**
Your YAML file still contains plaintext passwords. Run the migration script:
```bash
python scripts/migrate_passwords.py example_users.yaml
```

### Migration Script Not Found

**Error:**
```
ModuleNotFoundError: No module named 'hashing'
```

**Solution:**
Make sure you're in the authService root directory and run:
```bash
cd /path/to/authService
python scripts/migrate_passwords.py example_users.yaml
```

### Bcrypt Not Installed

**Error:**
```
ModuleNotFoundError: No module named 'bcrypt'
```

**Solution:**
Install dependencies:
```bash
pip install -r requirements.txt
```

### Migration Failed

**Error:**
```
❌ Migration failed: [error message]
```

**Solution:**
1. Check that the YAML file is readable and writable
2. Verify the file path is correct
3. Check your backup (.bak) file was created
4. Try manual migration (see Manual Migration section above)

## Migration for Framework Examples

If you use the provided framework examples (Flask, Django, Express), the migration process is the same. Just run the migration script on your users YAML file before using the updated code.

### Flask Example
```bash
python scripts/migrate_passwords.py example_users.yaml
python framework_examples/flask_example.py
# Login with migrated credentials
```

### Django Example
```bash
python scripts/migrate_passwords.py example_users.yaml
python manage.py runserver
# Login with migrated credentials
```

## FAQ

### Q: Will my old plaintext passwords still work?
**A:** No. After migration, only the bcrypt hashes are used. Users must login with the original password (which will be verified against the hash), but the plaintext password is not stored anywhere.

### Q: Can I migrate gradually?
**A:** No. All users must be migrated at once. However, you can keep your backup file in case you need to rollback.

### Q: How secure is bcrypt?
**A:** Very secure. Bcrypt uses:
- Automatic salt generation (prevents rainbow tables)
- Adaptive difficulty (increases security over time)
- Rounds=12 by default (recommended for most use cases)
- Industry standard and vetted by security experts

### Q: Can I use a different hashing algorithm?
**A:** Yes. Pass a custom `hash_function` to AuthManager:
```python
from argon2 import PasswordHasher

hasher = PasswordHasher()

def argon2_verify(password, hash):
    try:
        hasher.verify(hash, password)
        return True
    except:
        return False

manager = AuthManager(config, hash_function=argon2_verify)
```

### Q: What about password changes?
**A:** When users change passwords via `add_user()`, the new password is automatically hashed:
```python
manager.add_user('username', 'new_password')
# Password is hashed automatically
```

### Q: Does this affect performance?
**A:** Bcrypt hashing takes ~100ms per authentication (by design). This is a security trade-off but acceptable for most applications. For high-volume authentication, consider:
- Caching login tokens
- Using session-based authentication
- Implementing rate limiting

## Support

For issues with migration:

1. Check this guide's troubleshooting section
2. Review the error message carefully
3. Ensure your YAML file is valid
4. Check that bcrypt is properly installed
5. Open an issue on GitHub with details

## Success Checklist

- [ ] Backup created
- [ ] Migration script ran successfully
- [ ] Verification passed
- [ ] Authentication tested with original passwords
- [ ] Application restarted with new code
- [ ] Login functionality working
- [ ] Audit logs enabled (optional)
- [ ] Old backup files archived (if desired)

---

**Migration complete!** Your system is now using secure bcrypt password hashing. 🎉
