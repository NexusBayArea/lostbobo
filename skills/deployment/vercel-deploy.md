---
name: vercel-deploy
description: Deploy SimHPC frontend to Vercel with Infisical secret management.
version: 2.5.4
license: MIT
compatibility: opencode
---

# Vercel Deployment Skill

Deploy SimHPC frontend to Vercel with automatic secret injection from Infisical.

## Version: 2.5.4

## Deployment Steps

### 1. Secret Injection

Pull all VITE_ and NEXT_PUBLIC_ variables from Infisical:

```bash
infisical secrets export --env=production --outputFormat=dotenv > .env.vercel
```

### 2. Environment Sync

Ensure local parity with Vercel:

```bash
vercel env pull .env.local
```

### 3. Production Push

Execute deployment with Infisical secrets:

```bash
infisical run --env=production -- vercel --prod --yes
```

### 4. Verification

Confirm deployment URL and verify NEXT_PUBLIC_API_URL:

```bash
# Check deployment
vercel ls

# Verify API URL is set correctly
infisical secrets get NEXT_PUBLIC_API_URL
```

## CLI Prompt (Antigravity)

```
Deploy SimHPC to Vercel:
1. Use infisical export to pull all VITE_ and NEXT_PUBLIC_ variables
2. Run vercel env pull .env.local for local parity
3. Execute infisical run -- vercel --prod --yes
4. Confirm deployment URL matches active RunPod ID
```
