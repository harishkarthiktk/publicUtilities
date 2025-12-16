# Nginx Configuration for Flask File Server

This folder contains project-specific Nginx configurations for the Flask File Server. Nginx is installed system-wide (e.g., `brew install nginx` on macOS), but configs are kept here for version control. Sensitive files (e.g., .htpasswd) should be .gitignored.

## Overview
- **Purpose**: Nginx proxies dynamic requests from port 8000 to Flask/Gunicorn on 8002, serving large files efficiently via X-Accel-Redirect from `serveFolder`.
- **Key Features**:
  - Proxy `/` to Flask (auth/logic in Flask).
  - Internal `/internal-files/` for protected static serving.
  - Optimizations: `sendfile on`, no gzip for binaries.
  - Auth: Flask-only (YAML/env).
  - OS Detection: `create-conf.py` handles Windows/Unix paths, PID, commands.
  - Process User: Ensure read access to `serveFolder` for nginx user (e.g., `www-data`, `_www`).

## Config File: nginx.conf
Generated from `nginx.conf.template` using `create-conf.py`. Includes:
- Worker connections, HTTP defaults (mime.types, sendfile).
- Server block:
  - Listen 8000.
  - `client_max_body_size` from `config.yaml` `max_content_length` (e.g., 5GB → 5g).
  - Proxy `/` to 127.0.0.1:8002 with auth headers.
  - Internal `/internal-files/` alias to `serveFolder/`.
  - Project-local logs in `logs/`.

## Generating and Testing Config
`create-conf.py` substitutes paths, OS adjustments, `client_max_body_size` from `config.yaml`. Supports macOS/Linux/Windows. Requires nginx in PATH (optional). Placeholders: `{SERVE_FOLDER}`, `{ACCESS_LOG}`, `{ERROR_LOG}`, `{PID_PATH}`, `{CLIENT_MAX_BODY_SIZE}`. Add `nginx.conf` to `.gitignore`.

### Run Script
- `cd nginx && python create-conf.py` or `python nginx/create-conf.py`.
- Creates `logs/`, loads `config.yaml` (defaults 10m if error).
- Outputs paths, warnings, testing commands.

### Standalone Testing
- Copy `mime.types` to `nginx/` if missing (from Nginx install).
- Syntax: `nginx -t -c nginx/nginx.conf` (`nginx.exe` on Windows).
- Start: `nginx -c nginx/nginx.conf`.
- Verify: http://localhost:8000.
- Stop: `nginx -s quit` or kill process.
- Deploy: Copy to Nginx conf dir (script prints path).

## Deployment Steps
Estimated time: 10-15 min.

### Preparation
- Install Python 3.6+, pip, dependencies: `pip install -r requirements.txt`.
- Install Nginx, verify `nginx -v`.
- Generate config: `python nginx/create-conf.py`.
- Edit main nginx.conf to include conf dir (e.g., `include /etc/nginx/conf.d/*.conf;`).
- Permissions: `chmod -R o+r serveFolder` (Unix); grant read to Everyone (Windows).
- Venv: `python -m venv venv` and activate.

### Configuration
- Generate config (above).
- Copy `nginx.conf` to conf dir (e.g., `/etc/nginx/conf.d/file-serve.conf`).
- Test syntax: `nginx -t`.
- Reload: `nginx -s reload` or service restart (e.g., `sudo systemctl reload nginx`).

### Start Services
- Gunicorn: `./start_gunicorn.sh` or `gunicorn -w 4 -k gevent --timeout 120 -b 127.0.0.1:8002 app:app`.
- Nginx: Reload/restart as above.
- Access: http://localhost:8000.

## Post-Deployment
### Testing
- Download: `curl -u admin:password http://localhost:8000/files/example.txt`.
- Unauthorized: Expect 401.
- Logs: `tail -f logs/file-serve.access.log`, `logs/app.log`.

### Stop
- Gunicorn: `pkill -f gunicorn` (Unix) or `taskkill /f /im gunicorn.exe` (Windows).
- Nginx: `nginx -s quit` or service stop.
- Remove config, reload Nginx.

## Troubleshooting
- Port conflicts: Edit template port, regenerate, reload.
- Permissions: Grant read to serveFolder for nginx user.
- Proxy: Ensure main conf includes dir.
- Gunicorn: Activate venv, install deps, check port 8002.
- PID issues: Kill process (`killall nginx`), remove stale PID, restart.
- Syntax fail: Check mime.types, paths.

## Optional Enhancements
- HTTPS: Add SSL directives, certs.
- Auth: Basic auth on `/internal-files/`.
- Rate limiting: `limit_req_zone` in http.
- Docker: Containerize for portability.

See `../ngnix-plan/nginx-implementation-plan.md` for full plan.

**Portability Note**: `create-conf.py` uses forward slashes for cross-platform. Run after project moves; test with `nginx -t`.