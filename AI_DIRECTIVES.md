# 🤖 AI Directives for SimHPC Development

> **Version**: 1.0.0 (March 28, 2026)
> **Priority**: CRITICAL / MANDATORY
> **Status**: ENFORCED

This document defines the strict operational boundaries and security protocols for AI assistants working on the SimHPC codebase. All development actions must conform to these directives without exception.

---

## 🏗️ 1. Strict Repository Separation

SimHPC operates as two decoupled environments to protect intellectual property and ensure runtime stability.

### **Frontend (Client Plane)**

- **Platform**: Vercel (Production)
- **Stack**: React, Vite, Next.js, TypeScript.
- **Scope**: All UI components, client-side routing, and presentation logic.
- **Constraint**: **NEVER** include backend execution logic, GPU orchestration, or heavy Python computation here.

### **Backend (Compute Plane)**

- **Platform**: RunPod / Supabase (Dedicated GPU Pods)
- **Stack**: Python 3.11, FastAPI, NVIDIA CUDA 12.1.
- **Scope**: Database migrations, solver polling, Mercury AI integration, and physics orchestration.
- **Constraint**: This environment is **isolated** from the Vercel edge functions.

---

## 🛡️ 2. Zero-Tolerance Git Security

Security of the repository and its secrets is paramount.

- **Naming Convention**: The Git ignore file **MUST** be named exactly `.gitignore`.
- **Action**: If a file named `_gitignore` is detected, rename it to `.gitignore` immediately.
- **Secret Protection**: You are **strictly forbidden** from staging or committing the following:
  - `.env`, `.env.local`, `.env.production`
  - Any file containing `SUPABASE_SERVICE_ROLE_KEY`, `SIMHPC_API_KEY`, or `STRIPE_SECRET_KEY`.
- **Cleanup**: If a secret is accidentally committed, you must immediately run `git rm --cached <file>` and notify the user to rotate the keys.

---

## 🔑 3. Environment Variable Scoping

Variable access is strictly tiered based on the plane of execution.

| Scope | Allowed Variable Types | Example Keys |
| :--- | :--- | :--- |
| **Frontend** | Public/Browser-prefixed only | `VITE_SUPABASE_URL`, `NEXT_PUBLIC_STRIPE_KEY` |
| **Backend** | High-privilege/System keys | `SUPABASE_SERVICE_ROLE_KEY`, `RUNPOD_API_KEY` |

> [!CAUTION]
> **NEVER** reference `SUPABASE_SERVICE_ROLE_KEY` or `RUNPOD_API_KEY` within the frontend directory or its build configuration.

---

## 🤝 4. Architectural Handshake

The communication between the Frontend and Backend must follow a standardized API pattern.

- **Protocol**: HTTPS / Secure WebSockets.
- **Enforcement**: The Vercel frontend communicates with the backend **ONLY** via:
  - Standardized JSON API endpoints.
  - Stable **RunPod HTTP Proxy URLs** (to handle dynamic pod IPs).
- **Prohibited**: Do not attempt to run backend Python scripts or direct database admin connections directly from Vercel edge functions.

---

## 🚦 Compliance Check

Before every commit or deployment task, the AI assistant must verify:

1. [ ] No high-privilege keys are present in the frontend directory.
2. [ ] `.gitignore` is correctly named and includes `.env`.
3. [ ] No backend Python dependencies are bleeding into the React `package.json`.
4. [ ] All backend-to-frontend communication goes through the API proxy.

---

> [!IMPORTANT]
> Failure to adhere to these directives may result in credential exposure or critical architectural failure. **Safety first.**
