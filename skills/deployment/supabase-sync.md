---
name: supabase-sync
description: Sync Supabase secrets between Infisical, Vercel, and RunPod.
version: 2.5.4
license: MIT
compatibility: opencode
---

# Supabase Secret Sync Skill

Sync Supabase secrets between Infisical, Vercel, and RunPod.

## Version: 2.5.4

## Secret Naming Convention

| Infisical | Vercel | RunPod |
|---|---|---|
| `SB_URL` | `VITE_SUPABASE_URL` | `SB_URL` |
| `SB_ANON_KEY` | `VITE_SUPABASE_ANON_KEY` | `SB_ANON_KEY` |
| `SB_SERVICE_ROLE_KEY` | - | `SB_SERVICE_ROLE_KEY` |

## Skill 1: SB-to-SUPA Deployment Wrapper

Sync Supabase secrets and rename them for Vercel builds.

### sb-sync.sh

```bash
#!/bin/bash

echo "Fetching SB secrets from Infisical..."

SB_VARS=$(infisical export --format=dotenv | sed 's/SB_/VITE_SUPABASE_/g')

echo "$SB_VARS" | while read -r line; do
    if [[ $line == VITE_SUPABASE_* ]]; then
        KEY=$(echo $line | cut -d '=' -f 1)
        VALUE=$(echo $line | cut -d '=' -f 2-)
        echo "Updating $KEY on Vercel..."
        echo "$VALUE" | vercel env add "$KEY" production --force
    fi
done

echo "SB Secrets synchronized and translated."
```

### Run Command

```bash
bash scripts/sb-sync.sh
```

## Skill 2: Code Mapping

Use mapping in api.py and worker.py to accept both naming conventions:

```python
import os

SUPABASE_URL = os.getenv("SB_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SB_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Critical Error: SB_URL or SB_KEY missing from environment.")
```

## Skill 3: Database Migration

Run migrations with Infisical-injected secrets:

```bash
infisical login --client-id=$INFISICAL_CLIENT_ID --client-secret=$INFISICAL_CLIENT_SECRET
infisical run -- supabase db push --passphrase $SB_DB_PASSWORD
```

## Examples

- "Sync Supabase secrets to Vercel"
- "Run Supabase database migrations"
- "Update SB_ secrets mapping"
