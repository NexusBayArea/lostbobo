#!/bin/bash
# SimHPC Local Build Authority (v3.0.0)
# This script is the ONLY authorized way to build production images.

IMAGE_NAME="simhpcworker/simhpc-unified"
TAG=$(git rev-parse --short HEAD)

echo "🛠️  Starting Local Build Authority (LBA)..."
echo "📦 Image: $IMAGE_NAME"
echo "🏷️  Tag:   $TAG"

# Ensure we are in the root directory
cd "$(dirname "$0")/.." || exit

# 1. Build the unified image
docker build -f docker/images/Dockerfile.unified -t "$IMAGE_NAME:$TAG" .

# 2. Tag as latest for convenience
docker tag "$IMAGE_NAME:$TAG" "$IMAGE_NAME:latest"

echo "✅ Build Complete: $IMAGE_NAME:$TAG"
echo "🚀 To deploy, push and run deployment script:"
echo "   docker push $IMAGE_NAME:$TAG"
echo "   python scripts/deploy_to_runpod.py --tag $TAG"
