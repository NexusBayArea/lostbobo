#!/bin/bash

echo "[1/5] Running Local Build Test..."
infisical run -- npm run build

if [ $? -ne 0 ]; then
    echo "Local build failed. Fix pathing/imports before pushing."
    exit 1
fi

echo "[2/5] Build passed. Syncing Infisical..."
infisical secrets push

echo "[3/5] Deploying to Vercel..."
infisical run --env=production -- vercel --prod --yes

echo "[4/5] Fixing Git Casing..."
git rm -r --cached .
git add .
git commit -m "fix: resolve APIReference pathing and sync v2.5.4"

echo "[5/5] Pushing to GitHub..."
git push origin main
