# Configuration Reference

Complete reference for all AuthService configuration options. All settings are managed through YAML configuration files.

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [Application Settings](#application-settings)
3. [Logging Configuration](#logging-configuration)
4. [Authentication Settings](#authentication-settings)
5. [User Management](#user-management)
6. [Password Migration](#password-migration)
7. [Error Codes](#error-codes)
8. [Security Policies](#security-policies)
9. [Framework-Specific Settings](#framework-specific-settings)
10. [Environment-Specific Configurations](#environment-specific-configurations)

---

## Configuration Files

AuthService uses YAML configuration files to manage all settings.

### Default Configuration Files

| File | Purpose | Recommended Use |
|------|---------|-----------------|
| `config/app_config.yaml` | Production configuration | Live deployments |
| `config/app_config.dev.yaml` | Development configuration | Local development |
| `config/app_config.test.yaml` | Test configuration | Automated testing |

### Loading Configuration

```python
from authtemplate import AppConfig, AuthManager

# Load from specific config file
app_config = AppConfig('config/app_config.yaml')

# Initialize AuthManager with config
auth_manager = AuthManager.from_config(app_config)
```

---

## Application Settings

### Section: `app`

Basic application metadata and environment settings.

```yaml
app:
  name: "AuthService"           # Application name
  environment: "production"     # Environment: development, staging, production
  version: "1.0.0"              # Application version
```

### Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `name` | string | "AuthService" | Human-readable application name |
| `environment` | string | "production" | Deployment environment (affects defaults) |
| `version` | string | "1.0.0" | Application version (for compatibility tracking) |

### Environment-Specific Behavior

Different environments may use different defaults:
- **production**: HTTPS required, rate limiting enabled, logging restricted
- **development**: HTTPS optional, faster hashing, verbose logging
- **staging**: Similar to production but with debug options

---

## Logging Configuration

### Section: `logging`

Configure application and audit logging behavior.

```yaml
logging:
  general:                      # General application logging
    name: "AuthManager"
    level: "INFO"
    file: "logs/auth.log"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: "%Y-%m-%d %H:%M:%S"
    max_bytes: 5242880
    backup_count: 3

  audit:                        # User operation audit logging
    enabled: true
    file: "logs/audit.log"
    format: "[AUDIT] %(asctime)s - %(message)s"
    date_format: "%Y-%m-%d %H:%M:%S"
    max_bytes: 5242880
    backup_count: 5
```

### General Logging Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `name` | string | "AuthManager" | Logger name (appears in logs) |
| `level` | string | "INFO" | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `file` | string/null | "logs/auth.log" | Log file path (null = console only) |
| `format` | string | Standard format | Log message format (Python logging format) |
| `date_format` | string | "%Y-%m-%d %H:%M:%S" | Date format in logs |
| `max_bytes` | int | 5242880 | Max log file size before rotation (5MB) |
| `backup_count` | int | 3 | Number of backup log files to keep |

### Log Levels

- **DEBUG**: Detailed information (development only)
- **INFO**: General information about operations
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

### Audit Logging Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable separate audit logging |
| `file` | string | "logs/audit.log" | Audit log file path |
| `format` | string | "[AUDIT] ..." | Audit message format |
| `date_format` | string | "%Y-%m-%d %H:%M:%S" | Date format in audit logs |
| `max_bytes` | int | 5242880 | Max audit log file size (5MB) |
| `backup_count` | int | 5 | Number of backup audit logs |

### Audit Events Logged

When audit logging is enabled, the following events are recorded:

- `USER_ADDED`: New user account created
- `USER_REMOVED`: User account deleted
- `USER_MODIFIED`: User information changed
- `PASSWORD_CHANGED`: User password modified
- Authentication attempts (when configured)

Example audit log entry:
```
[AUDIT] 2026-01-11 17:20:55 - USER_ADDED: username=john, by=admin, ip=192.168.1.100
```

---

## Authentication Settings

### Section: `auth`

Configure authentication mechanisms and defaults.

```yaml
auth:
  hashing:
    enabled: true
    algorithm: "bcrypt"
    bcrypt_rounds: 12

  custom_hash_function: null

  defaults:
    ip_address: "unknown"
    by_whom: "system"
    user_role: "user"
    user_is_active: true

  session:
    timeout: 3600
    require_https: true
```

### Hashing Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable password hashing |
| `algorithm` | string | "bcrypt" | Hashing algorithm (bcrypt recommended) |
| `bcrypt_rounds` | int | 12 | Bcrypt salt rounds (10-13 recommended) |

#### Bcrypt Rounds Guide

| Rounds | Speed | Security | Recommended For |
|--------|-------|----------|-----------------|
| 4-8 | Very fast | Low | Testing only |
| 10 | Fast | Good | Development |
| 11-12 | Standard | Recommended | Production |
| 13+ | Slow | Very high | High-security apps |

**Note:** Higher rounds are more secure but slower. Use 12 for production.

### Default Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `ip_address` | string | "unknown" | Default IP when not provided |
| `by_whom` | string | "system" | Default actor for audit logs |
| `user_role` | string | "user" | Default role for new users |
| `user_is_active` | bool | true | Default active status |

### Session Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `timeout` | int | 3600 | Session timeout in seconds (1 hour) |
| `require_https` | bool | true | Require HTTPS in production |

---

## User Management

### Section: `users`

Configure user storage and loading behavior.

```yaml
users:
  config_file: "config/users.yaml"
  auto_load: true
```

### Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `config_file` | string | "config/users.yaml" | Path to YAML file with user credentials |
| `auto_load` | bool | true | Automatically load users on initialization |

### User Configuration File Format

The `config_file` points to a YAML file containing user credentials:

```yaml
users:
  admin: $2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUm
  user1: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYkZH8BgGkK
  developer: $2b$12$uVPJhDDZPjpCxKI/3KX1QOHs.XdkFKC8KbIvlvxdR0KHAhAZ2Pkyq
```

**Important:** All passwords must be bcrypt hashes. Use the migration script for plaintext conversion.

---

## Password Migration

### Section: `migration`

Configure password migration behavior when converting plaintext to bcrypt.

```yaml
migration:
  create_backup: true
  backup_extension: ".bak"
  reserved_keys:
    - "auth_type"
    - "log_level"
    - "log_file"
    - "require_https"
```

### Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `create_backup` | bool | true | Create .bak backup before migration |
| `backup_extension` | string | ".bak" | File extension for backup files |
| `reserved_keys` | list | See default | Keys to skip during migration |

### Reserved Keys

Keys in this list are NOT treated as usernames during migration. Used for non-user configuration that might be stored in the same YAML file.

Default reserved keys:
- `auth_type`
- `log_level`
- `log_file`
- `require_https`

---

## Error Codes

### Section: `error_codes`

Customize error codes returned by authentication operations.

```yaml
error_codes:
  user_not_found: "USER_NOT_FOUND"
  invalid_credentials: "INVALID_CREDENTIALS"
  auth_error: "AUTH_ERROR"
  invalid_header: "INVALID_HEADER"
  invalid_encoding: "INVALID_ENCODING"
  header_parse_error: "HEADER_PARSE_ERROR"
```

### Available Error Codes

| Key | Default Value | When Returned |
|-----|----------------|---------------|
| `user_not_found` | "USER_NOT_FOUND" | Username doesn't exist |
| `invalid_credentials` | "INVALID_CREDENTIALS" | Password doesn't match |
| `auth_error` | "AUTH_ERROR" | Authentication process error |
| `invalid_header` | "INVALID_HEADER" | Authorization header malformed |
| `invalid_encoding` | "INVALID_ENCODING" | Header Base64 decoding failed |
| `header_parse_error` | "HEADER_PARSE_ERROR" | Header parsing failed |

### Custom Error Codes Example

```yaml
error_codes:
  user_not_found: "USER_MISSING"
  invalid_credentials: "BAD_CREDENTIALS"
  auth_error: "AUTH_FAILED"
```

---

## Security Policies

### Section: `security`

Configure security policies and protections.

```yaml
security:
  password_policy:
    min_length: 8
    require_uppercase: false
    require_numbers: false
    require_special: false

  rate_limiting:
    enabled: false
    max_attempts: 5
    window_seconds: 300
```

### Password Policy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `min_length` | int | 8 | Minimum password length (future use) |
| `require_uppercase` | bool | false | Require uppercase letters (future use) |
| `require_numbers` | bool | false | Require numeric digits (future use) |
| `require_special` | bool | false | Require special characters (future use) |

**Note:** Password policy validation is planned for future releases.

### Rate Limiting

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | false | Enable rate limiting |
| `max_attempts` | int | 5 | Failed attempts before lockout |
| `window_seconds` | int | 300 | Time window for attempts (5 min) |

**Rate limiting example:**
- With `max_attempts: 5` and `window_seconds: 300`
- 5 failed login attempts within 300 seconds = account locked
- Lock duration: until window expires

---

## Framework-Specific Settings

### Section: `frameworks`

Configure settings for specific web frameworks.

```yaml
frameworks:
  flask:
    host: "0.0.0.0"
    port: 5000
    debug: false
    cors_origins:
      - "https://trusted-domain.com"

  django:
    allowed_hosts:
      - "example.com"
    auth_type: "basic"

  express:
    port: 3000
    cors_enabled: true

  spring:
    port: 8080
    servlet_path: "/api"
```

### Flask Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `host` | string | "0.0.0.0" | Flask server host |
| `port` | int | 5000 | Flask server port |
| `debug` | bool | false | Flask debug mode |
| `cors_origins` | list | [] | Allowed CORS origins |

### Django Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `allowed_hosts` | list | [] | Django ALLOWED_HOSTS setting |
| `auth_type` | string | "basic" | Authentication type |

### Express Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `port` | int | 3000 | Express server port |
| `cors_enabled` | bool | true | Enable CORS |

### Spring Boot Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `port` | int | 8080 | Spring Boot server port |
| `servlet_path` | string | "/api" | Application servlet context path |

---

## Environment-Specific Configurations

Use different configuration files for different environments.

### Loading Environment-Specific Config

```bash
# Load development config
export AUTH_CONFIG=config/app_config.dev.yaml

# Load test config
export AUTH_CONFIG=config/app_config.test.yaml

# Load production config (default)
export AUTH_CONFIG=config/app_config.yaml
```

### Production Configuration (app_config.yaml)

Recommended for live deployments:
- `environment: "production"`
- `level: "INFO"` (warnings and errors only)
- `require_https: true`
- `bcrypt_rounds: 12` (standard security)
- File logging enabled with rotation
- Audit logging enabled

### Development Configuration (app_config.dev.yaml)

Recommended for local development:
- `environment: "development"`
- `level: "DEBUG"` (verbose logging)
- `require_https: false`
- `bcrypt_rounds: 10` (faster)
- `debug: true` for frameworks
- Shorter session timeout for testing

### Test Configuration (app_config.test.yaml)

Optimized for automated testing:
- `environment: "test"`
- `level: "WARNING"` (minimal output)
- `bcrypt_rounds: 4` (fastest)
- No file logging (console only)
- Audit logging disabled
- Minimum config to speed up tests

---

## Configuration Priority

When loading configuration, settings are resolved in this order:

1. **Explicit parameter** (if provided to AppConfig)
2. **Environment variable** `AUTH_CONFIG`
3. **Default location** `config/app_config.yaml`
4. **Built-in defaults** (if config file missing)

Example:
```python
# Priority 1: Explicit
config = AppConfig('my_custom_config.yaml')

# Priority 2: Environment variable
# export AUTH_CONFIG=custom_config.yaml
# Then: config = AppConfig()

# Priority 3: Default location
# config = AppConfig() → loads config/app_config.yaml
```

---

## Configuration Validation

The AppConfig class validates settings when loaded:

- Missing keys use defaults (never error)
- Invalid data types are coerced when possible
- Invalid YAML files raise `FileNotFoundError`
- Missing config file raises `FileNotFoundError`

---

## Common Configuration Scenarios

### Scenario 1: Disable Audit Logging

```yaml
logging:
  audit:
    enabled: false
```

### Scenario 2: Faster Password Hashing (Development)

```yaml
auth:
  hashing:
    bcrypt_rounds: 8
```

### Scenario 3: Custom Log Directory

```yaml
logging:
  general:
    file: "/var/log/authservice/auth.log"
  audit:
    file: "/var/log/authservice/audit.log"
```

### Scenario 4: High Security (Production)

```yaml
auth:
  hashing:
    bcrypt_rounds: 13
  session:
    require_https: true
security:
  rate_limiting:
    enabled: true
    max_attempts: 3
    window_seconds: 600
```

### Scenario 5: Multiple Frameworks

```yaml
frameworks:
  flask:
    port: 5000
    cors_origins:
      - "https://web.example.com"

  django:
    allowed_hosts:
      - "example.com"
      - "*.example.com"
```

---

## Best Practices

1. **Use environment-specific configs** - Don't use production config for development
2. **Commit configs to version control** - But never commit plaintext passwords
3. **Use `.gitignore` for sensitive configs** - Keep `config/users.yaml` out of VCS
4. **Document custom error codes** - Help your team understand error responses
5. **Test rate limiting** - Verify behavior in staging before production
6. **Monitor log rotation** - Ensure log directories have enough disk space
7. **Set appropriate bcrypt rounds** - Balance security vs. performance for your use case

---

## Troubleshooting

### Config File Not Found

```
FileNotFoundError: Config file not found: config/app_config.yaml
```

**Solution:** Ensure the config file path is correct and file exists.

### Invalid YAML Syntax

```
yaml.YAMLError: ...
```

**Solution:** Validate YAML syntax using online validators or `yaml -v` command.

### Logs Not Being Created

1. Check `logging.general.file` is not `null`
2. Verify log directory exists (created automatically if parent exists)
3. Check file permissions in log directory

### Authentication Slow

1. Check `auth.hashing.bcrypt_rounds` - too high?
2. Consider reducing rounds for development/testing
3. Profile with `bcrypt` timings

---

## Migration from Hardcoded Config

If you have hardcoded configuration, migrate to YAML:

1. Create `config/app_config.yaml` from template
2. Copy your hardcoded values into YAML sections
3. Update code to use `AppConfig`:

```python
# Before: Hardcoded
auth_manager = AuthManager(config)

# After: From config file
app_config = AppConfig('config/app_config.yaml')
auth_manager = AuthManager.from_config(app_config)
```

---

## API Reference

### AppConfig Class

```python
from authtemplate import AppConfig

config = AppConfig('config/app_config.yaml')

# Application
config.get_app_name()
config.get_environment()
config.get_version()

# Logging
config.get_log_file()
config.get_log_level()
config.get_log_format()
config.get_audit_log_file()

# Authentication
config.use_hashing()
config.get_bcrypt_rounds()
config.get_default_ip_address()
config.get_default_by_whom()

# Migration
config.get_migration_backup_enabled()
config.get_migration_reserved_keys()

# Users
config.get_users_config_file()

# Security
config.is_rate_limiting_enabled()
config.get_rate_limit_max_attempts()

# Frameworks
config.get_framework_config('flask')
```

---

For more information, see the main [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md).
