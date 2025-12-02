# Nginx Configuration for Flask File Server

This folder contains project-specific Nginx configurations for the Flask File Server. Nginx is installed system-wide via Homebrew (`brew install nginx`), but configs are kept here for version control and easy management. Sensitive files (e.g., .htpasswd if used) should be .gitignored.

## Overview
- **Purpose**: Nginx acts as a reverse proxy on port 8000, proxying dynamic requests to Flask/Gunicorn on internal port 8002. It handles efficient file serving via X-Accel-Redirect for large files from `serveFolder`.
- **Key Features**:
  - Proxy `/` to Flask (auth and logic handled there).
  - Internal `/internal-files/` for protected static serving (triggered only by Flask's X-Accel-Redirect).
  - Optimizations: `sendfile on` for high-speed LAN transfers; no gzip for binaries.
  - Auth: Solely in Flask (YAML/env); no Nginx auth.

## Config File: nginx.conf
The `nginx.conf` in this folder is generated dynamically from `nginx.conf.template` using `setup-config.py`. It includes:
- Events/worker connections.
- HTTP defaults (mime.types, sendfile, etc.).
- Server block:
  - Listen on 8000.
  - `location /`: Proxy to `http://127.0.0.1:8002` with auth header passing.
  - `location /internal-files/`: Internal alias to `serveFolder/`, with optimizations (paths resolved relative to project root).
  - Logs: Project-local custom access/error logs in `logs/`.

## Deployment Steps
Follow these steps to deploy the Nginx + Gunicorn stack. Estimated time: 10-15 min.

### 1. Preparation (One-Time Setup)
This section covers all prerequisites and initial setup, which should be done only once.

#### Prerequisites
- Ensure Python and pip are installed (via Homebrew or system package manager).
- Ensure Homebrew is installed: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` if not present.
- Virtual environment (recommended): Create and activate a venv in the project root: `python -m venv venv && source venv/bin/activate`.

- Install dependencies: `pip install -r requirements.txt` (includes Gunicorn and other Flask requirements).
- Install Nginx: `brew install nginx` (macOS; on Windows/Linux, use package manager and ensure in PATH). Verify installation: `nginx -v`.
- Generate config: `python nginx/setup-config.py` (or `cd nginx && python setup-config.py`). This creates `nginx/nginx.conf` with dynamic paths relative to the project root. Supports macOS/Linux/Windows. (Add `nginx/nginx.conf` to `.gitignore`.)
- Ensure the main Nginx config (`/usr/local/etc/nginx/nginx.conf`) includes the servers directory: Add `include servers/*.conf;` in the HTTP block if not present.
- Set permissions on serveFolder: `chmod -R o+r serveFolder` (allows Nginx user `_www` to read files).
- Make scripts executable: `chmod +x start_gunicorn.sh deploy.sh`.

### 2. Configuration
Configure Nginx with the project-specific settings.

- Copy the generated config: `cp nginx/nginx.conf /usr/local/etc/nginx/servers/file-serve.conf` (regenerate if project moved).
- Test syntax: `nginx -t`. Fix any errors (e.g., update path to serveFolder in the config if needed).
- Initial reload: `nginx -s reload` or `brew services restart nginx`.

### 3. Manual Deployment
For custom or debugging setups, start services manually.

- Start Gunicorn: `./start_gunicorn.sh` (or directly: `gunicorn -w 4 -k gevent --timeout 120 -b 127.0.0.1:8002 app:app` in the background, logs to gunicorn.log).
- Reload Nginx: `nginx -s reload`.

### 4. Deploy (Recommended)
Use the automated script for quick setup (includes config copy if needed, starts Gunicorn, reloads Nginx).

- Run the project `deploy.sh` script:
  ```
  ./deploy.sh
  ```
  - Starts Gunicorn on 8002 (background).
  - Reloads Nginx.
  - Outputs PIDs and URL: http://localhost:8000 (or LAN IP:8000).

To stop: `./deploy.sh stop` (kills Gunicorn, stops Nginx).

## Post-Deployment

### Access and Testing
- Base URL: http://localhost:8000/ (file browser, requires auth).
- Download test: `curl -u admin:password http://localhost:8000/files/example.txt`.
- Large file throughput: `curl -u admin:password -L -o /dev/null -w "Speed: %{speed_download} bytes/sec\n" http://localhost:8000/files/largefile.mkv`.
- Unauthorized: `curl -u wrong:wrong http://localhost:8000/files/example.txt` (expect 401).
- Direct internal: `curl http://localhost:8000/internal-files/example.txt` (expect 404, protected).

### Monitoring and Logs
- Flask/Gunicorn: `tail -f gunicorn.log` and `logs/app.log` (auth errors).
- Nginx: `tail -f logs/file-serve.access.log` (requests) and `logs/file-serve.error.log` (config/serve issues).
- Processes: `ps aux | grep gunicorn` and `ps aux | grep nginx`.

### Stop and Cleanup
- Using script: `./deploy.sh stop` (kills Gunicorn, stops Nginx).
- Manual: `pkill -f gunicorn` and `nginx -s stop`.
- Remove config: `rm /usr/local/etc/nginx/servers/file-serve.conf && nginx -s reload`.

## Troubleshooting
- **Port Conflicts**: Change `listen 8000;` in nginx/setup-config.py or regenerate after editing template.
- **Permission Errors**: `chmod -R o+r serveFolder` (Nginx user `_www` needs read access).
- **Proxy Issues**: Ensure `include servers/*.conf;` in main nginx.conf.
- **Gunicorn Fails**: Check venv activation and requirements.txt.
- **No X-Accel**: Verify routes.py has the Response with header; test without Nginx first.
- **Rollback**: Revert app.py/routes.py, remove config, run `python app.py` on 8000.

## Optional Enhancements
- **HTTPS**: Add `listen 443 ssl;` and cert paths in server block (use Let's Encrypt or self-signed for LAN).
- **Nginx Auth (Duplicate)**: If adding to `/internal-files/`, create `.htpasswd` (`htpasswd -c .htpasswd admin`), add to location: `auth_basic "Restricted"; auth_basic_user_file /path/to/.htpasswd;`. .gitignore it.
- **Rate Limiting**: Add to http block: `limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;`, then `limit_req zone=api;` in location /.
- **Docker**: For portability, create Dockerfile with Nginx + Gunicorn.

For full implementation plan, see `../ngnix-plan/nginx-implementation-plan.md`.

**Note on Portability**: The setup-config.py ensures the config works when the project is cloned/moved. Run it after changing project location. On Windows, use `python` command and ensure forward slashes in paths.