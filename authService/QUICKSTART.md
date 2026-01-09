# AuthTemplate - Quick Start Guide

Get authentication up and running in **5 minutes**.

## 1️⃣ Copy AuthTemplate to Your Project

```bash
cp -r authtemplate/ /path/to/your/project/
```

## 2️⃣ Create Configuration File

Create `config/users.yaml`:

```yaml
users:
  admin: admin_password
  user1: user1_password
  developer: dev_secure_password
```

Or use environment variables:

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=admin_password
```

## 3️⃣ Choose Your Framework

### Flask (5 lines of code)

```python
from flask import Flask, request, g, jsonify
from functools import wraps
from authtemplate import AuthManager, AuthConfig

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

@app.route('/protected')
@require_auth
def protected():
    return jsonify({'user': g.user.username})

if __name__ == '__main__':
    app.run()
```

**Test it:**

```bash
# Using curl
curl -u admin:admin_password http://localhost:5000/protected
```

### Express.js (5 lines of code)

```javascript
const express = require('express');
const basicAuth = require('basic-auth');
const app = express();

// Simple auth middleware
const requireAuth = (req, res, next) => {
    const credentials = basicAuth(req);
    if (!credentials || credentials.name !== 'admin' || credentials.pass !== 'admin_password') {
        return res.status(401).json({error: 'Unauthorized'});
    }
    req.user = {username: credentials.name};
    next();
};

app.get('/protected', requireAuth, (req, res) => {
    res.json({user: req.user.username});
});

app.listen(3000);
```

**Test it:**

```bash
curl -u admin:admin_password http://localhost:3000/protected
```

### Django (Decorator)

```python
# auth.py
from authtemplate import AuthManager, AuthConfig
import base64

auth_manager = AuthManager(AuthConfig(yaml_file='config/users.yaml'))

def require_basic_auth(view_func):
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

# views.py
from django.http import JsonResponse
from .auth import require_basic_auth

@require_basic_auth
def protected_view(request):
    return JsonResponse({'user': request.auth_user.username})
```

### Spring Boot (Configuration)

```java
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

@RestController
public class Controller {
    @GetMapping("/protected")
    public ResponseEntity<?> protected() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return ResponseEntity.ok(Map.of("user", auth.getName()));
    }
}
```

## 4️⃣ Test Your Setup

### Using curl

```bash
# Test without authentication (should fail)
curl http://localhost:5000/protected
# Response: 401 Unauthorized

# Test with authentication (should succeed)
curl -u admin:admin_password http://localhost:5000/protected
# Response: {"user": "admin"}

# With different user
curl -u user1:user1_password http://localhost:5000/protected
# Response: {"user": "user1"}
```

### Using Python requests library

```python
import requests

# Invalid credentials
response = requests.get('http://localhost:5000/protected')
print(response.status_code)  # 401

# Valid credentials
response = requests.get(
    'http://localhost:5000/protected',
    auth=('admin', 'admin_password')
)
print(response.json())  # {'user': 'admin'}
```

## 5️⃣ Common Tasks

### Add User at Runtime

```python
from authtemplate import AuthManager, AuthConfig

auth_manager = AuthManager(AuthConfig(yaml_file='config/users.yaml'))

# Add new user
auth_manager.add_user('newuser', 'newpassword')

# Verify new user can authenticate
result = auth_manager.verify_credentials('newuser', 'newpassword')
print(f"User added: {result.success}")  # True
```

### Use Environment Variables

```bash
# Set credentials in environment
export AUTH_USER=admin
export AUTH_PASSWORD=secure_password

# In your code
from authtemplate import AuthManager, AuthConfig

auth_manager = AuthManager(AuthConfig(use_env_vars=True))
```

### Get List of Users

```python
users = auth_manager.list_users()
print(f"Configured users: {users}")
# Output: Configured users: ['admin', 'user1', 'developer']
```

### Check User Information

```python
info = auth_manager.get_user_info('admin')
print(info)
# Output: {'username': 'admin', 'exists': True, 'is_active': True}
```

## 6️⃣ Next Steps

1. **Security**: Hash passwords in production using bcrypt
   ```python
   import bcrypt
   hashed = bcrypt.hashpw(b'password', bcrypt.gensalt())
   ```

2. **Logging**: Configure logging to file
   ```python
   from authtemplate import setup_logger
   logger = setup_logger('MyApp', log_file='logs/auth.log')
   ```

3. **Rate Limiting**: Add protection against brute force attacks
4. **HTTPS**: Always use HTTPS in production
5. **Roles**: Add role-based access control to your User model

## 📚 Learn More

- **Full Documentation**: See `README.md`
- **Framework Examples**: Check `framework_examples/` directory
- **Testing**: See `tests/test_auth.py` for test examples
- **API Reference**: Full API documentation in `README.md`

## 🚀 You're Done!

Your application now has authentication. Protect endpoints by:

- **Flask**: Use `@require_auth` decorator
- **Express**: Use `requireAuth` middleware
- **Django**: Use `@require_basic_auth` decorator
- **Spring Boot**: Configuration handles it automatically

## ❓ Troubleshooting

### "Module not found" error

Ensure authtemplate is in your Python path:

```python
import sys
sys.path.insert(0, '/path/to/authtemplate')
from authtemplate import AuthManager
```

### "No users configured" error

Check that `config/users.yaml` exists:

```bash
ls -la config/users.yaml
cat config/users.yaml
```

Or set environment variables:

```bash
export AUTH_USER=admin
export AUTH_PASSWORD=password
```

### Authentication always fails

Check credentials in config:

```python
from authtemplate import AuthConfig

config = AuthConfig(yaml_file='config/users.yaml')
users = config.get_users()
print(users)  # Should show your users
```

---

**That's it!** You now have a working authentication system. 🎉

For production deployments, see the Security Considerations section in `README.md`.
