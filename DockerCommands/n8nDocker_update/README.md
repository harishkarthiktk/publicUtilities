# Docker Compose Management Guide for n8n

This guide explains how to manage the n8n container using `docker-compose` (via `podman compose`). If you're familiar with `podman run` commands, think of compose as a declarative way to manage the same container with simplified commands.

## Quick Start

### Start the Container
```bash
podman compose up -d
```
- Creates and starts the n8n container in the background
- `-d` flag means "detached" (runs in background)
- Automatically creates the volume `n8n_data` if it doesn't exist
- The container restarts automatically on reboot due to `restart: always` policy

### Stop the Container
```bash
podman compose down
```
- Stops the container gracefully (sends SIGTERM signal)
- Container data and volume are preserved
- You can safely restart it later without losing data

### Restart the Container
```bash
podman compose restart
```
- Restarts the running container
- Equivalent to `stop` + `up -d`, but faster
- Data and settings are preserved

## Important Commands

### View Running Containers
```bash
podman compose ps
```
Shows status, ports, and container info managed by this compose file.

### View Logs
```bash
podman compose logs
```
Shows container output and errors. Use for troubleshooting.

To follow logs in real-time:
```bash
podman compose logs -f
```

### Stop Container Without Removing It
```bash
podman compose stop
```
Container remains stopped but not removed. Can be restarted with `podman compose start`.

### Start a Stopped Container
```bash
podman compose start
```
Starts a previously stopped container.

### Remove Everything (Container + Volume)
```bash
podman compose down -v
```
**WARNING:** This deletes the container AND the `n8n_data` volume. Use only if you want a complete fresh start.

## Important Tips

### 1. Keep docker-compose.yml in This Directory
Always run compose commands from the directory containing `docker-compose.yml`. Compose needs this file to manage the container.

### 2. Volume Persistence
- All n8n data (workflows, settings, credentials) is stored in the `n8n_data` volume
- Located at: `/var/lib/containers/storage/volumes/n8n_data/_data`
- This persists across container restarts
- Even if you delete the container, the volume remains (use `-v` flag to delete it)

### 3. Using Directly vs. Compose
**Do this with compose (recommended):**
```bash
podman compose stop
podman compose start
podman compose logs
```

**Don't do this (breaks compose management):**
```bash
podman stop n8n
podman start n8n
podman rm n8n
```

If you manually use `podman` commands, compose may get confused about the container state.

### 4. Accessing n8n
- URL: `http://localhost:5678`
- Port 5678 is mapped to the host and accessible from your machine

### 5. Updating to a Newer Image
```bash
podman compose pull
podman compose up -d
```
This pulls the latest `docker.n8n.io/n8nio/n8n:latest` image and recreates the container with new code while preserving your data volume.

### 6. Environment Variables
All settings are defined in `docker-compose.yml`:
- **TZ / GENERIC_TIMEZONE**: Set to `Asia/Kolkata`
- **N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS**: Security setting (true)
- **N8N_RUNNERS_ENABLED**: Enables n8n runners (true)
- **Proxy Settings**: HTTP/HTTPS proxies configured for corporate network

To modify any setting, edit `docker-compose.yml` and run `podman compose up -d` to apply changes.

## Troubleshooting

### Container keeps restarting
Check logs:
```bash
podman compose logs
```
Look for error messages that explain why it crashed.

### Can't access n8n at localhost:5678
1. Check if container is running: `podman compose ps`
2. Check if port 5678 is bound: `podman port n8n`
3. Check logs for startup errors: `podman compose logs`

### Forgot what configuration is running
View the compose file:
```bash
cat docker-compose.yml
```
Or inspect the running container:
```bash
podman inspect n8n
```

### Need to debug or run a command inside the container
```bash
podman compose exec n8n sh
```
Opens a shell inside the running container for debugging.

## Comparison: podman run vs docker-compose

### Before (podman run - what you know):
```bash
podman run -d --name n8n --restart=always -p 5678:5678 \
  -e TZ=Asia/Kolkata \
  -e GENERIC_TIMEZONE=Asia/Kolkata \
  -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
  -e N8N_RUNNERS_ENABLED=true \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n:latest
```

### Now (docker-compose - simpler):
```bash
podman compose up -d
```

All configuration is in `docker-compose.yml`, making it:
- Easier to read and maintain
- Version-controllable (track changes to config)
- Reproducible (new machines get identical setup)

## Quick Reference Card

| Task | Command |
|------|---------|
| Start | `podman compose up -d` |
| Stop | `podman compose down` |
| Restart | `podman compose restart` |
| View status | `podman compose ps` |
| View logs | `podman compose logs -f` |
| Shell access | `podman compose exec n8n sh` |
| Update image | `podman compose pull && podman compose up -d` |
| Full cleanup | `podman compose down -v` |

