# SimHPC Development Guidelines

## Project Structure
We follow a strict monorepo structure to separate concerns and protect intellectual property.

- **`apps/`**: Deployable applications (e.g., React frontend, Next.js starter).
- **`services/`**: Backend microservices and workers.
- **`packages/`**: Shared libraries, SDKs, and internal tools.
- **`docs/`**: Centralized documentation.

## Best Practices
1. **Isolation**: Maintain clear boundaries between apps and services. Do not cross-import code directly between them; use shared `packages/` if necessary.
2. **Environment**: Store all secrets in `.env` (root or per-service). Never commit `.env` files. For Vercel, inject `VITE_` vars via Dashboard or `vercel-envs` in workflow. For GitHub Pages, pass secrets in the `env:` block of the build step.
3. **Documentation**: Keep `README.md` and `ARCHITECTURE.md` updated with any structural changes.
4. **Consistency**: Follow existing naming conventions (kebab-case for folders).
5. **Cleanliness**: Regularly clean up temporary files, build artifacts, and logs.

## Deployment Notes
- **Vercel is Production Primary**: Handles `VITE_` env injection, SPA routing, and CSP for Stripe/Supabase automatically.
- **GitHub Pages is Backup/Staging**: Requires manual env var injection in workflow and CSP meta tag in `index.html`.
- **Known Issue (v1.6.0-ALPHA)**: GitHub Pages fails with "Supabase Credentials Missing" and CSP violations. Fix: add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to GitHub Secrets and pass them in the build step.
- **Custom Domain (v2.1.2)**: App at `simhpc.com`, Auth at `auth.simhpc.com`. DNS: A `@ → 76.76.21.21`, CNAME `auth → [project-ref].supabase.co`. Update Supabase Redirect URLs and Stripe JS Origins after domain is live.
- **Double-Key Strategy (v2.2.1)**: Frontend uses `VITE_SUPABASE_ANON_KEY` (RLS enforced). Worker uses `SUPABASE_SERVICE_ROLE_KEY` (RLS bypassed) for telemetry and artifact sync.
- **Stable RunPod Proxy (v2.2.1)**: Always use the RunPod HTTP Proxy URL (e.g., `https://x613fv0zoyvtx9-8000.proxy.runpod.net`) for `VITE_API_URL` to prevent "Offline" errors caused by IP changes.
- **Google Auth (v2.2.1)**: Google Client ID `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`. Redirects must point to `https://simhpc.com/api/auth/callback/google`.

## Toast System (v2.1.2)
- **Library**: sonner (`^2.0.7`)
- **Mount Point**: `<Toaster />` in `src/App.tsx`
- **Config**: 6s default, 8s success, 10s error, 350px min-width, bottom-right, cyan theme `#00f2ff`, rounded corners
- **Pattern**: `toast.promise()` for submission; `toast.loading()` → `toast.success/error()` with same ID for other async ops
- **CSS**: Overrides in `src/index.css` for dark terminal styling
- **Realtime**: `useSimulationUpdates` hook subscribes to Supabase `simulation_history` table — triggers 10s completion toast at top-center

## Tooling
- **PowerShell**: Used for local environment management.
- **Docker Compose**: Used for local orchestration of services.
- **Vercel**: Primary hosting and deployment platform for the frontend.
- **Git**: Primary version control. Do not stage/commit unless requested.

---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
