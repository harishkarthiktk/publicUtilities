#!/bin/bash

# Deployment script for Flask File Server with Nginx + Gunicorn
# Usage: ./deploy.sh [stop]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/env"  # Adjust if your venv is named differently
NGINX_CONF_SRC="${PROJECT_DIR}/nginx/nginx.conf"
NGINX_CONF_DEST="/usr/local/etc/nginx/servers/file-serve.conf"  # Homebrew default; adjust if custom
NGINX_MAIN_CONF="/usr/local/etc/nginx/nginx.conf"  # Ensure 'include servers/*.conf;' is in this file

if [ "$1" = "stop" ]; then
    echo "Stopping stack..."
    pkill -f "gunicorn.*app:app" || true
    nginx -s stop || true
    brew services stop nginx || true
    exit 0
fi

# Check prerequisites
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found at $VENV_DIR. Create with: python -m venv env && pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "$NGINX_CONF_SRC" ]; then
    echo "Nginx config not found at $NGINX_CONF_SRC. Create it first."
    exit 1
fi

# Step 1: Copy Nginx config to system path
echo "Copying Nginx config to $NGINX_CONF_DEST..."
cp "$NGINX_CONF_SRC" "$NGINX_CONF_DEST"

# Ensure main nginx.conf includes servers/*.conf (commented check; assume user has it)
if ! grep -q "include servers/\*.conf;" "$NGINX_MAIN_CONF" 2>/dev/null; then
    echo "Warning: Add 'include servers/*.conf;' to $NGINX_MAIN_CONF if not present."
fi

# Step 2: Test and reload Nginx
echo "Testing Nginx config..."
nginx -t
if [ $? -eq 0 ]; then
    echo "Reloading Nginx..."
    nginx -s reload || brew services restart nginx
else
    echo "Nginx config test failed. Fix errors and rerun."
    exit 1
fi

# Step 3: Start Gunicorn in background
echo "Starting Gunicorn on port 8002..."
source "$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"
nohup gunicorn -w 4 -k gevent --timeout 120 -b 127.0.0.1:8002 app:app > gunicorn.log 2>&1 &
GUNICORN_PID=$!

# Wait a moment for startup
sleep 2

# Check if Gunicorn started
if ! ps -p $GUNICORN_PID > /dev/null; then
    echo "Gunicorn failed to start. Check gunicorn.log."
    exit 1
fi

echo "Deployment complete!"
echo " - Access URL: http://localhost:8000 (or your LAN IP:8000)"
echo " - Gunicorn PID: $GUNICORN_PID (logs: gunicorn.log)"
echo " - Nginx logs: /usr/local/var/log/nginx/file-serve.*.log"
echo " - Stop stack: ./deploy.sh stop"