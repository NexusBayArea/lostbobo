#!/bin/bash

echo "Fetching SB secrets from Infisical..."

SB_VARS=$(infisical export --format=dotenv | sed 's/SB_/VITE_SUPABASE_/g')

echo "$SB_VARS" | while read -r line; do
    if [[ $line == VITE_SUPABASE_* ]]; then
        KEY=$(echo $line | cut -d '=' -f 1)
        VALUE=$(echo $line | cut -d '=' -f 2-)
        echo "Updating $KEY on Vercel..."
        echo "$VALUE" | vercel env add "$KEY" production --force 2>/dev/null || true
    fi
done

echo "SB Secrets synchronized and translated."
