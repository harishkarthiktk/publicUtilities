#!/bin/bash

set -euo pipefail

CONTAINER_NAME="fedora"

# Check if container exists
if ! podman container exists "$CONTAINER_NAME" 2>/dev/null; then
    echo "Error: Container '$CONTAINER_NAME' does not exist" >&2
    exit 1
fi

# Check if container is running
if ! podman container inspect "$CONTAINER_NAME" --format='{{.State.Running}}' 2>/dev/null | grep -q "true"; then
    echo "Error: Container '$CONTAINER_NAME' is not running" >&2
    echo "Start it with: podman start $CONTAINER_NAME" >&2
    exit 1
fi

# Execute zsh in the container
podman exec -it "$CONTAINER_NAME" zsh
