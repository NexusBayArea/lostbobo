#!/bin/bash
IMAGE_NAME="ghcr.io/nexusbayarea/simhpc-worker:latest"
CONTAINER_NAME="simhpc-worker-active"
echo "--- 🔄 SimHPC Alpha: Checking for Updates ---"
docker pull $IMAGE_NAME | grep "Image is up to date" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Worker is already running the latest version."
else
    echo "🚀 New version detected! Restarting worker..."
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
    docker run -d --name $CONTAINER_NAME --runtime=nvidia --gpus all --env-file .env --restart always $IMAGE_NAME
fi
