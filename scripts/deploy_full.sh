#!/bin/bash

echo "[1/4] Syncing Infisical Secrets..."
infisical secrets push

echo "[2/4] Deploying to Vercel (Production)..."
infisical run --env=production -- vercel --prod --yes

echo "[3/4] Updating GitHub Repository..."
git add .
git commit -m "chore: production deploy v2.5.4 unified plane"
git push origin main

echo "[4/4] Fleet Synchronized."
