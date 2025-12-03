#!/bin/bash

# Start Gunicorn for Flask app on internal port 8002
# Usage: ./start_gunicorn.sh [stop]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv_fileserve"  # Adjust if your venv is named differently

if [ "$1" = "stop" ]; then
    echo "Stopping Gunicorn..."
    pkill -f "gunicorn.*app:app" || true
    exit 0
fi

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found at $VENV_DIR. Create with: python -m venv env && pip install -r requirements.txt"
    exit 1
fi

cd "$PROJECT_DIR"

# Start Gunicorn (4 workers, gevent for async, timeout 120s for large files)
echo "Starting Gunicorn on port 8002..."
exec gunicorn -w 4 --timeout 120 -b 127.0.0.1:8002 app:app