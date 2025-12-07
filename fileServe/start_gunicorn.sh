#!/bin/bash

# Note: Gunicorn does not work on Windows.
# For Windows, install waitress: pip install waitress
# Then run: waitress-serve --port=8002 --host=127.0.0.1 app:app (adjust port based on mode)

# Start Gunicorn for Flask app, with port based on config mode
# Usage: ./start_gunicorn.sh [stop]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv_fileserve"  # Adjust if your venv is named differently
CONFIG_PATH="${PROJECT_DIR}/config.yaml"

if [ "$1" = "stop" ]; then
    echo "Stopping Gunicorn..."
    pkill -f "gunicorn.*app:app" || true
    # Optionally stop Nginx if running
    if command -v nginx >/dev/null 2>&1; then
        nginx -s quit || true
    fi
    exit 0
fi

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found at $VENV_DIR. Create with: python -m venv .venv_fileserve && pip install -r requirements.txt"
    exit 1
fi

cd "$PROJECT_DIR"

# Read config to determine mode and port
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
else
    PYTHON=python
fi

USE_PURE_FLASK=$( $PYTHON -c "
import yaml
with open('$CONFIG_PATH', 'r') as f:
    config = yaml.safe_load(f)
print('true' if config.get('use_pure_flask', False) else 'false')
" )

if [ "$USE_PURE_FLASK" = "true" ]; then
    PORT=8000
    WORKERS=8  # More workers for pure Flask to handle streaming
    TIMEOUT=300  # Longer timeout for direct serving
    echo "Pure Flask mode: Starting Gunicorn on port $PORT (no Nginx needed)"
    # Skip Nginx start
else
    PORT=8002
    WORKERS=4
    TIMEOUT=120
    echo "Nginx mode: Starting Gunicorn on internal port $PORT"
    # Generate and start Nginx if possible
    if command -v nginx >/dev/null 2>&1; then
        cd nginx
        $PYTHON create-conf.py
        cd ..
        nginx -c $(pwd)/nginx/nginx.conf || echo "Nginx start failed; ensure config is valid"
    else
        echo "Nginx not found in PATH; install for full Nginx mode"
    fi
fi

# Start Gunicorn with mode-specific settings
echo "Starting Gunicorn with $WORKERS workers, timeout $TIMEOUT on port $PORT..."
exec gunicorn -w $WORKERS --timeout $TIMEOUT -k gevent -b 127.0.0.1:$PORT app:app