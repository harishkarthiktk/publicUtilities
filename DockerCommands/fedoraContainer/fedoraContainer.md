# Fedora Container - Persistent Workstation

## Using compose (recommended)

```bash
# build and start
podman compose up -d

# shell into it
podman exec -it fedora bash

# stop
podman compose down

# rebuild after editing Containerfile
podman compose up -d --build
```

Uses `Containerfile` and `compose.yml` in this directory. Base packages (curl, wget, git, net-tools, openssh-clients, iputils) are baked into the image.

## Manual run (without compose)

```bash
podman run -dit \
  --name fedora \
  --restart=unless-stopped \
  -v fedora_home:/root \
  docker.io/library/fedora:latest \
  /bin/bash
```

- `-dit` keeps the container running in background with an interactive tty
- `fedora_home` named volume persists /root (shell history, configs, dotfiles)
- Installed packages persist in the container's filesystem across stop/start cycles

## Day-to-day usage

```bash
# get a shell
podman exec -it fedora bash

# stop (preserves all installed packages and filesystem changes)
podman stop fedora

# restart later - everything is still there
podman start fedora
```

## First-time setup inside the container (manual run only)

Base packages are pre-installed if using compose. For manual run, install them yourself:

```bash
dnf install -y curl wget git net-tools openssh-clients iputils
```

## Snapshot installed packages (save as reusable image)

```bash
# commit current container state to a new image
podman commit -p fedora fedora-custom:latest

# verify
podman images | grep fedora-custom

# if you ever need to recreate from snapshot
podman rm -f fedora
podman run -dit \
  --name fedora \
  --restart=unless-stopped \
  -v fedora_home:/root \
  localhost/fedora-custom:latest \
  /bin/bash
```

## Export/import snapshot to file

```bash
# save image to tar
podman save -o fedora-custom-backup.tar localhost/fedora-custom:latest

# load image from tar (on another machine or after cleanup)
podman load -i fedora-custom-backup.tar
```

## Notes

- **Never `podman rm` the container** unless you have committed a snapshot first, or you will lose all installed packages
- The named volume (`fedora_home`) survives container removal - only /root data is safe without a commit
- `podman commit` captures everything in the container filesystem (installed rpms, configs in /etc, binaries in /usr) but not volume-mounted paths
- Use `podman start fedora` after host reboots - `--restart=unless-stopped` handles this if podman's systemd service is enabled
