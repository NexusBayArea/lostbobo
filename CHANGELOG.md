# SimHPC Changelog

> All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.1] - 2026-03-10

### Added
- **Tier-Aware API**: Backend now queries Supabase `profiles` table directly to enforce plan limits (`free` vs `professional`).
- **Supabase Persistence**: Simulation results and summaries are now inserted into the `simulations` table using the Service Role Key.
- **Frontend Mutation Hooks**: Implemented `useMutation` for launching simulations with automated toast notifications and error handling.
- **Payment Success UX**: Added animated success page with confetti and 5-second redirect after Stripe checkout.

### Added
- **ExperimentNotebook Theme Toggle**: Added bright/dark mode toggle to the Experiment Notebook page matching the rest of the website.

### Fixed
- **Footer Logo Color**: Fixed SimHPC logo "Sim" text to inherit parent color for proper visibility in footer across all themes.
- **Global Background Consistency**: Updated all page backgrounds (SignIn, SignUp, Benchmarks, Docs, Pricing, About, Contact, APIReference, etc.) to match homepage color #F1EDE0.
- **Theming**: Updated global day background color to `#F1EDE0` for better visual consistency across all pages.

---

## [1.3.0] - 2026-03-09

### Added
- **Google One Tap Sign-In**: Integrated Google Identity Services (`g_id_onload`, `g_id_signin`) for frictionless authentication.
- **GitHub Pages Deployment**: Migrated frontend hosting to GitHub Pages (https://github.com/NexusBayArea/SimHPC).

---

## [1.2.0] - 2026-03-08

### Added
- **Experiment Notebook**: A persistent research workspace for automated logging, side-by-side experiment comparison, and "Replay" capability for solver parameters.
- **Abuse Prevention System**: Multi-layered security including device fingerprinting, IP-based account limits, honeypot fields, and compute guardrails (60s timeouts, delayed queues).
- **Mercury AI Integration**: Finalized transition to Inception Labs' Mercury AI for engineering-grade reports with numerical anchoring.
- Secure Repo Strategy: Migrated to a split-repository architecture, isolating the frontend in `lostbobo` (https://github.com/NexusBayArea/lostbobo.git) while keeping backend and AI logic closed-source.


### Security
- Implemented frontend-only repository strategy for Vercel deployment.
- Hardened `.gitignore` to prevent accidental exposure of backend orchestrator logic.
- Disconnected Supabase from GitHub sync to prevent unauthorized schema access.

---

## [1.1.0] - 2026-03-06

### Added
- **Mercury AI Migration**: Replaced Kimi AI with Mercury (Inception Labs) for report generation.
- **SimHPC Client Library**: TypeScript client with auto-auth and typed methods.
- **API Proxy**: Next.js route handler with JWT session extraction.

### Fixed
- Resolved circular dependencies in Celery tasks.
- Fixed event loop issues in async backend services.
- Hardened JWT verification logic.

---

## [1.0.0] - 2026-03-04

### Added
- Initial production launch with Stripe integration and PDF export.
- Multi-stage Docker optimization.
- Structured logging and Prometheus metrics.
