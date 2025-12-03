# Nginx Configuration for Flask File Server

This folder contains project-specific Nginx configurations for the Flask File Server. Nginx is installed system-wide via Homebrew (`brew install nginx`), but configs are kept here for version control and easy management. Sensitive files (e.g., .htpasswd if used) should be .gitignored.

## Overview
- **Purpose**: Nginx acts as a reverse proxy on port 8000, proxying dynamic requests to Flask/Gunicorn on internal port 8002. It handles efficient file serving via X-Accel-Redirect for large files from `serveFolder`.
- **Key Features**:
  - Proxy `/` to Flask (auth and logic handled there).
  - Internal `/internal-files/` for protected static serving (triggered only by Flask's X-Accel-Redirect).
  - Optimizations: `sendfile on` for high-speed LAN transfers; no gzip for binaries.
  - Auth: Solely in Flask (YAML/env); no Nginx auth.
  - Nginx Process User: Common users include `www-data` (Ubuntu/Debian), `nginx` (CentOS/RHEL/Fedora), `_www` (macOS Homebrew), or the user running the service (Windows). Ensure this user has read access to `serveFolder`.

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
- Ensure Python 3.6+ and pip are installed. On most systems, use your package manager:
  - macOS: `brew install python` (if using Homebrew).
  - Ubuntu/Debian: `sudo apt update && sudo apt install python3 python3-pip`.
  - CentOS/RHEL/Fedora: `sudo yum install python3 python3-pip` or `sudo dnf install python3 python3-pip`.
  - Windows: Download from python.org and ensure "Add to PATH" during installation.
- Virtual environment (recommended for isolation): Create and activate a venv in the project root:
  - Unix-like (macOS/Linux): `python -m venv venv && source venv/bin/activate`.
  - Windows: `python -m venv venv && venv\Scripts\activate`.

- Install Python dependencies: `pip install -r requirements.txt` (includes Gunicorn and other Flask requirements).
- Install Nginx: Use your system's package manager or official binaries. Verify with `nginx -v`.
  - macOS (Homebrew): `brew install nginx`.
  - Ubuntu/Debian: `sudo apt update && sudo apt install nginx`.
  - CentOS/RHEL: `sudo yum install nginx` or `sudo dnf install nginx`.
  - Fedora: `sudo dnf install nginx`.
  - Windows: Download from nginx.org (e.g., via Chocolatey: `choco install nginx` if Chocolatey is installed) or extract the zip to a directory like `C:\nginx` and add to PATH.
  Common Nginx paths:
  - macOS (Homebrew): `/opt/homebrew/etc/nginx/` or `/usr/local/etc/nginx/`.
  - Linux (apt/yum): `/etc/nginx/`.
  - Windows: `C:\nginx\conf\`.
- Generate config: `python nginx/setup-config.py` (or `cd nginx && python setup-config.py`). This creates `nginx/nginx.conf` with dynamic, cross-platform paths relative to the project root (supports macOS/Linux/Windows). Add `nginx/nginx.conf` to `.gitignore`.
- Ensure the main Nginx config includes the servers directory: Edit the global nginx.conf (see paths above) to add `include servers/*.conf;` or equivalent (e.g., `include /etc/nginx/conf.d/*.conf;`) in the HTTP block if not present.
- Set read permissions on serveFolder for the Nginx process user:
  - Unix-like: `chmod -R o+r serveFolder` (allows other users like `www-data` or `_www` to read).
  - Windows: Use File Explorer (right-click > Properties > Security > Edit to grant Read to "Everyone") or `icacls serveFolder /grant Everyone:R /T`.
  Common Nginx users: `www-data` (Ubuntu/Debian), `nginx` (CentOS/RHEL), `_www` (macOS), or the user running the service (Windows).
- Make scripts executable:
  - Unix-like: `chmod +x start_gunicorn.sh deploy.sh`.
  - Windows: No action needed (Python scripts run directly; for .sh, use Git Bash or WSL).

### 2. Configuration
Configure Nginx with the project-specific settings.

- Generate the config: Run `python nginx/setup-config.py` (or `cd nginx && python setup-config.py`). This creates `nginx/nginx.conf` with dynamic, cross-platform paths (serveFolder, logs, PID). Add `nginx/nginx.conf` to `.gitignore`.
- Ensure `mime.types` exists in the `nginx/` folder (copied automatically by the script if detected; otherwise, copy manually from your Nginx installation). This `mime.types` is required for conf validation and testing. IF not, move the conf to nginx's location to test. Common locations:
  - macOS (Homebrew): `/opt/homebrew/etc/nginx/mime.types` or `/usr/local/etc/nginx/mime.types`.
  - Linux (apt/yum): `/etc/nginx/mime.types`.
  - Windows: `C:\nginx\conf\mime.types`.
- Copy the generated config to your Nginx configuration directory (adjust based on your installation; regenerate if project moved):
  - Unix-like: `cp nginx/nginx.conf /etc/nginx/conf.d/file-serve.conf` (Linux) or `/usr/local/etc/nginx/servers/file-serve.conf` (macOS Homebrew).
  - Windows: Copy `nginx/nginx.conf` to `C:\nginx\conf\file-serve.conf` (or include it in the main `nginx.conf` via `include conf.d/*.conf;`).
  Ensure the main nginx.conf includes the directory where you place the config (e.g., `include /etc/nginx/conf.d/*.conf;` or `include servers/*.conf;` in the HTTP block).
- Test syntax: `nginx -t -c "nginx/nginx.conf"` (or specify the full path to your config if testing the global setup: `nginx -t`). This fails if `mime.types` is missing or paths are invalid.
- Initial reload/restart (choose based on your OS/service manager):
  - macOS (Homebrew): `brew services restart nginx` or `nginx -s reload`.
  - Linux (systemd): `sudo systemctl reload nginx` or `sudo systemctl restart nginx`.
  - Windows (service): Restart via Services app (search "Services", find "nginx", right-click Restart) or `net stop nginx && net start nginx` (if installed as service).
  - Manual: `nginx -s reload` (if PID file is valid; see Troubleshooting for issues).

### 3. Manual Deployment (Recommended)
For all setups, start and manage services manually. Ensure your virtual environment is activated before starting Gunicorn.

- Start Gunicorn: Use `./start_gunicorn.sh` on Unix-like systems (macOS/Linux) or adapt for Windows (e.g., run `python start_gunicorn.py` if converted, or directly via Command Prompt/PowerShell). Alternatively, run directly:
  - Unix-like: `gunicorn -w 4 -k gevent --timeout 120 -b 127.0.0.1:8002 app:app &` (background with `&`; logs to gunicorn.log).
  - Windows: `gunicorn -w 4 -k gevent --timeout 120 -b 127.0.0.1:8002 app:app` (run in a separate terminal or use `start /B` for background; logs to gunicorn.log).
- Reload or restart Nginx to apply config changes:
  - If running manually: `nginx -s reload` (assumes valid PID; see Troubleshooting if issues).
  - Service-managed:
    - macOS (Homebrew): `brew services restart nginx`.
    - Linux (systemd): `sudo systemctl reload nginx` (or `restart` if needed).
    - Windows (service): Use Services app (search "nginx", right-click Restart) or `net stop nginx && net start nginx` in admin Command Prompt.
- Access the server: Once both are running, visit http://localhost:8000 (or your machine's LAN IP:8000 for network access).

For stopping services, see the "Stop and Cleanup" section below.

## Post-Deployment

### Access and Testing
- Base URL: http://localhost:8000/ (file browser, requires auth). Use a browser or tools like curl/Postman.
- Download test: `curl -u admin:password http://localhost:8000/files/example.txt` (cross-platform; on Windows, use curl from Command Prompt or PowerShell).
- Large file throughput: `curl -u admin:password -L -o /dev/null -w "Speed: %{speed_download} bytes/sec\n" http://localhost:8000/files/largefile.mkv`.
- Unauthorized: `curl -u wrong:wrong http://localhost:8000/files/example.txt` (expect 401).
- Direct internal: `curl http://localhost:8000/internal-files/example.txt` (expect 404, protected).

### Monitoring and Logs
- Flask/Gunicorn: `tail -f gunicorn.log` (Unix-like) or use a text editor/ PowerShell `Get-Content gunicorn.log -Tail 10 -Wait` (Windows); also check `logs/app.log` for auth errors.
- Nginx: `tail -f logs/file-serve.access.log` (requests) and `tail -f logs/file-serve.error.log` (config/serve issues) on Unix-like; on Windows, use text editors or PowerShell equivalents.
- Processes:
  - Unix-like: `ps aux | grep gunicorn` and `ps aux | grep nginx` (or `pgrep -f gunicorn` for PIDs).
  - Windows: `tasklist /fi "imagename eq gunicorn.exe"` and `tasklist /fi "imagename eq nginx.exe"` (or use Task Manager).

### Stop and Cleanup
- Stop Gunicorn:
  - Unix-like: `pkill -f gunicorn` (or kill by PID if known).
  - Windows: Use Task Manager (end task for gunicorn.exe) or `taskkill /f /im gunicorn.exe`.
- Stop Nginx:
  - Manual: `nginx -s stop` or `nginx -s quit` (if PID file is valid; see Troubleshooting).
  - Service-managed:
    - macOS (Homebrew): `brew services stop nginx`.
    - Linux (systemd): `sudo systemctl stop nginx`.
    - Windows (service): Use Services app (right-click nginx > Stop) or `net stop nginx`.
- Remove config: Delete the file-serve.conf from your Nginx config directory (e.g., `rm /etc/nginx/conf.d/file-serve.conf` on Linux, or delete via File Explorer on Windows), then reload/restart Nginx as above to apply.

## Troubleshooting
- **Port Conflicts**: Change the port (e.g., `listen 8000;`) in `nginx.conf.template`, regenerate with `python nginx/setup-config.py`, copy the config, and reload Nginx.
- **Permission Errors**: Ensure the Nginx process user has read access to serveFolder.
  - Unix-like: `chmod -R o+r serveFolder` (for users like `www-data`, `nginx`, or `_www`).
  - Windows: Use File Explorer (Properties > Security > grant Read to the Nginx user or "Everyone") or `icacls serveFolder /grant "Everyone":R /T`.
- **Proxy Issues**: Verify the main nginx.conf includes your config directory (e.g., `include /etc/nginx/conf.d/*.conf;` or `include servers/*.conf;` in the HTTP block).
- **Gunicorn Fails**: Confirm virtual environment is activated, dependencies installed (`pip install -r requirements.txt`), and no port conflicts on 8002.
- **No X-Accel-Redirect**: Check `routes.py` sets the `X-Accel-Redirect` header in the Response; test the Flask app directly (e.g., `python app.py`) without Nginx first.
- **Rollback**: Revert changes to `app.py`/`routes.py`, remove the Nginx config file, reload Nginx, and run the Flask app directly: `python app.py` (listens on 8000 by default).

- **PID File Issues** (Common Across OSes): Nginx signal commands (`nginx -s reload`, `nginx -s stop`, etc.) fail with errors like "invalid PID number" due to stale, empty, or missing PID files after crashes, force kills, or system reboots. This prevents managing the running Nginx process.

  **Problem**: Nginx relies on the PID file (specified in config, e.g., `/var/run/nginx.pid` on Linux, `/opt/homebrew/var/run/nginx.pid` on macOS Homebrew, or custom on Windows) to send signals to its master process.

  **Immediate Fix** (Manual, Cross-Platform):
  - Find the Nginx process PID:
    - Unix-like: `sudo lsof -i :8000` or `sudo netstat -tulpn | grep :8000` (shows PID).
    - Windows: `netstat -ano | findstr :8000` (shows PID), or use Task Manager (Details tab, search nginx.exe).
  - Kill the process: `kill -9 <PID>` (Unix-like) or `taskkill /f /pid <PID>` (Windows).
  - Or kill all Nginx: `sudo killall nginx` (Unix-like) or `taskkill /f /im nginx.exe` (Windows).
  - Remove stale PID file: Delete it manually (e.g., `sudo rm /var/run/nginx.pid` on Linux, `rm /opt/homebrew/var/run/nginx.pid` on macOS; on Windows, delete from the path in config).

  **Permanent Prevention**:
  1. **Explicit PID Path**: Ensure `nginx.conf.template` specifies a writable PID path (e.g., `pid /var/run/nginx.pid;` or project-local). Regenerate and copy the config.
     - Create the directory if needed: `sudo mkdir -p /var/run/nginx` (adjust path).
     - Set permissions: `sudo chown nginx:nginx /var/run/nginx` (Linux; adjust user/group) or equivalent for your OS.
  2. **Run as Service**: Use system services (systemd on Linux, Homebrew/launchd on macOS, Windows Services) for automatic PID management and restarts.
  3. **Custom Restart Script**: Create a cross-platform script or function to clean stale PIDs before starting:
     - Example for Unix-like shells (add to ~/.bashrc or ~/.zshrc):
       ```bash
       nginx-clean-start() {
           PID_FILE=$(nginx -V 2>&1 | grep -o 'pid=.*' | cut -d'=' -f2 | tr -d ';')
           [ -f "$PID_FILE" ] && sudo rm "$PID_FILE"
           sudo killall nginx 2>/dev/null || true
           sudo nginx  # Or your start command
           if sudo lsof -i :8000 | grep -q nginx; then
               echo "Nginx started on port 8000"
           else
               echo "Failed to start"
           fi
       }
       ```
     - For Windows PowerShell: Adapt similarly using `Stop-Process -Name nginx -Force` and `Start-Process nginx.exe`.
     Reload shell config and use the function instead of direct starts.

## Optional Enhancements
- **HTTPS**: Add `listen 443 ssl;` and certificate paths (e.g., `ssl_certificate /path/to/cert.pem; ssl_certificate_key /path/to/key.pem;`) to the server block. Use Let's Encrypt (via certbot) for production or self-signed certs for LAN testing. On Windows, paths use backslashes or forward slashes (Nginx accepts both).
- **Nginx Auth (Duplicate, Optional)**: For additional protection on `/internal-files/`, enable basic auth:
  - Create `.htpasswd`: Use `htpasswd -c .htpasswd admin` (Unix-like; requires Apache utils: `sudo apt install apache2-utils` on Ubuntu or equivalent). On Windows, use online generators or Cygwin/WSL.
  - Add to location block: `auth_basic "Restricted"; auth_basic_user_file /path/to/.htpasswd;`. Add `.htpasswd` to `.gitignore`.
- **Rate Limiting**: Add to http block: `limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;`, then `limit_req zone=api;` in the `/` location.
- **Docker**: For full portability across OSes, containerize with a Dockerfile including Nginx + Gunicorn + Python deps. Use `docker-compose` for easy multi-service setup (e.g., volumes for `serveFolder`).

For full implementation plan, see `../ngnix-plan/nginx-implementation-plan.md`.

**Note on Portability**: The `setup-config.py` script generates configs with cross-platform paths (using forward slashes, which Nginx handles on Windows). Run it after cloning or moving the project. On Windows, invoke with `python setup-config.py` and ensure Python is in PATH. Test config syntax with `nginx -t` after generation.