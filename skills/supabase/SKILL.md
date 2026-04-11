---
name: supabase
description: Supabase DevOps with SB_ prefix naming convention for Infisical compatibility.
version: 1.2.0
license: MIT
compatibility: opencode
---

# Supabase DevOps Skill Set

## Version: 1.2.0

## 🔐 SECURITY RULES (MANDATORY - NO EXCEPTIONS)

### 🚨 NEVER commit to git:
- `.env` files (ANY variant)
- Supabase service role keys
- Database passwords
- API keys or tokens

### ✅ ALWAYS use Infisical:
```bash
# Get secrets at runtime
infisical secrets get SB_SERVICE_ROLE_KEY --env=production --plain

# Run with secrets injected
infisical run --env=production -- supabase db push
```

### GitHub Actions:
- Store `INFISICAL_TOKEN` in GitHub Secrets
- Reference via `${{ secrets.INFISICAL_TOKEN }}`
- NEVER log Supabase keys in workflow output

## Required Infisical Keys (SB Prefix)

| Key | Purpose |
|-----|---------|
| `SB_ACCESS_TOKEN` | CLI Authentication |
| `SB_PROJECT_ID` | Remote project reference |
| `SB_DB_PASSWORD` | Database user password |
| `SB_URL` | API endpoint for the client |
| `SB_ANON_KEY` | Public client key |
| `SB_SERVICE_ROLE_KEY` | Administrative key for worker tasks |

## GitHub Action

```yaml
name: Deploy Supabase

on:
  push:
    branches: [main]
    paths:
      - 'supabase/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Install Infisical CLI
        run: |
          curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo bash
          sudo apt-get install -y infisical

      - name: Deploy to Production
        env:
          INFISICAL_TOKEN: ${{ secrets.INFISICAL_TOKEN }}
        run: |
          infisical run --env=production -- bash -c '
            supabase login --token "$SB_ACCESS_TOKEN"
            supabase link --project-ref "$SB_PROJECT_ID" --password "$SB_DB_PASSWORD"
            supabase db push --password "$SB_DB_PASSWORD"
            supabase functions deploy --project-ref "$SB_PROJECT_ID"
          '
```

## Deployment Commands

```bash
# Push migrations
infisical run --env=production -- supabase db push

# Deploy edge functions
infisical run --env=production -- supabase functions deploy
```

## Current Supabase Project

- **Project Ref**: ldzztrnghaaonparyggz
- **URL**: https://ldzztrnghaaonparyggz.supabase.co
- **Region**: us-east-1