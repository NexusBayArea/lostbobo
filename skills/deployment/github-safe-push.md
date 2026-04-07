---
name: github-safe-push
description: Secure push to GitHub with secret scanning and linting.
version: 2.5.4
license: MIT
compatibility: opencode
---

# GitHub Safe Push Skill

Prevent secret leakage by scanning code for keys before pushing to GitHub.

## Version: 2.5.4

## Pre-Push Checklist

### 1. Secret Scan

Run Infisical scan to ensure no raw keys are in codebase:

```bash
infisical scan
```

### 2. Linting

Maintain v2.5.4 code quality with Ruff:

```bash
ruff check . --fix
```

### 3. Commit

Generate conventional commit message:

```bash
git add .
git commit -m "chore: production deploy v2.5.4"
```

### 4. Push

Execute secure push:

```bash
git push origin main
```

## CLI Prompt (Antigravity)

```
Secure Push to GitHub:
1. Run infisical scan to ensure no raw keys in codebase
2. Run ruff check . --fix for code quality
3. Generate conventional commit based on progress.md updates
4. Execute git push origin main
```

## .gitignore Reminders

Ensure these are excluded:
```
.env
.env.*
!.env.example
*.log
__pycache__/
node_modules/
.vercel/
```
