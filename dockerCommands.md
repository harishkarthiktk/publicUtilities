docker run -d \
  --name qdrant \
  --restart always \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_data:/qdrant/storage \
  docker.io/qdrant/qdrant:latest

docker run -d \
  --gpus=all \
  -v ollama_data:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  docker.io/ollama/ollama


podman run -d \
  --name n8n \
  --restart=always \
≈  -p 5678:5678 \
  -e GENERIC_TIMEZONE="Asia/Kolkata" \
  -e TZ="Asia/Kolkata" \
  -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
  -e N8N_RUNNERS_ENABLED=true \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n


podman system df -v #to show space utilization of VM of podman, in OSX.

podman run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  docker.io/postgres:17

podman run -d --name postgres -e POSTGRES_PASSWORD=mysecret -p 5432:5432 -v postgres_data:/var/lib/postgresql/data docker.io/postgres:17