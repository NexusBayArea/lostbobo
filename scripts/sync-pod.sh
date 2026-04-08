#!/bin/bash
# Usage: ./scripts/sync-pod.sh <POD_ID>

POD_ID=$1

if [ -z "$POD_ID" ]; then
    echo "Error: No Pod ID provided."
    echo "Usage: ./scripts/sync-pod.sh <POD_ID>"
    exit 1
fi

HTTPS_URL="https://${POD_ID}-8888.proxy.runpod.net"

echo "Injecting Pod Metadata into Infisical..."
infisical secrets set RUNPOD_POD_ID=$POD_ID --env=production
infisical secrets set VITE_API_URL=$HTTPS_URL --env=production

echo "Updating Vercel Environment..."
infisical run --env=production -- vercel env add VITE_API_URL production $HTTPS_URL --force

echo "Triggering Production Redeploy..."
infisical run --env=production -- vercel --prod --yes --force

echo "Sync Complete. Frontend now pointing to $HTTPS_URL"
