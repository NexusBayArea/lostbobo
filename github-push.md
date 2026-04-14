# github-safe-push.md

## Version
**v2.7.1**

### 🌐 Frontend URL Sync (MANDATORY)
Before pushing to Vercel, verify the API target is set to the stable Port 8080:
1. Ensure `NEXT_PUBLIC_API_URL` follows the pattern: `https://[POD_ID]-8080.proxy.runpod.net`
2. **NEVER** push hard‑coded Port 8888 or 8000 URLs to production.

### 5. Integrity Check (The "Anti‑Deletion" Guard)
Verify core files are present before the push:
- [ ] `api.py` (Orchestrator) exists.
- [ ] `main.py` (Worker) exists.
- [ ] `start.sh` (Port 8080 config) exists.

If any are missing, STOP the push and restore from local backup.

## CLI Prompt (Antigravity v2.7.1)
```
Secure Push to GitHub:
1. Run `infisical scan` to ensure no raw keys are in the codebase.
2. Run `ruff check . --fix` to clear unused imports (JSONResponse, etc.).
3. VERIFY `api.py` and `main.py` are present in the root.
4. CONFIRM `start.sh` is set to Port 8080 (Stable).
5. Deploy to Vercel ONLY if all local integrity checks pass.
Do not commit .env files.
```