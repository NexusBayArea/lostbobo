# SimHPC Alpha Pilot - User Guide

Welcome to the **SimHPC Alpha Pilot**! This guide will help you run your first physics-based simulation and generate an AI-interpreted engineering report.

---

## 1. Quick Start: Your Magic Link

You should have received a **Magic Link** via email (e.g., `https://simhpc.com/demo/ABC-123`). 

1. **Click the Link**: This will automatically authenticate your session.
2. **Dashboard**: You'll be redirected to the Alpha Dashboard.
3. **Usage Banner**: Look for the blue banner at the top showing your remaining demo runs (typically 5).

---

## 2. Running a Simulation

1. **Navigate to Simulations**: Click the "New Simulation" button in the sidebar.
2. **Configure Parameters**:
   - **Sampling Method**: Select **±10%** for a quick sweep or **Sobol GSA** for a deep sensitivity study.
   - **Parameters**: Adjust values like `Charge Current (A)` or `Cathode Thickness (µm)`.
3. **Launch**: Click **"Run Robustness Analysis"**.
4. **Watch Live Telemetry**: You'll see real-time convergence plots and solver heartbeats as the NVIDIA GPU instance processes your job.

---

## 3. Reviewing Your Report

Once the simulation completes:

1. **AI Insights**: A **Mercury AI** generated report will appear on the dashboard, interpreting the sensitivity rankings and identifying potential failure points.
2. **Download PDF**: Click the **"Export PDF"** button for a professional engineering record containing:
   - Baseline results
   - Statistical variance plots
   - Sobol sensitivity rankings
   - AI-driven design recommendations

---

## 4. Troubleshooting & Feedback

- **404 on Refresh**: If you refresh the page and see a 404, just navigate back to the root URL (https://simhpc.com). We are optimizing our Nginx routing for the pilot.
- **"Supabase Credentials Missing" on GitHub Pages**: The backup site (https://NexusBayArea.github.io/lostbobo) may show this error because GitHub Pages does not inject environment variables at build time. **Use https://simhpc.com (Vercel) instead** — it works out of the box.
- **Stripe/CSP Errors on GitHub Pages**: `github.io` domains block inline styles and third-party cookies. Stripe checkout and Supabase Auth may fail. **Use https://simhpc.com (Vercel) instead.**
- **Link Expired**: Alpha links are valid for **7 days**. If yours expired, contact us at **deploy@simhpc.com**.
- **System Health Indicators**: Check the left sidebar on the Dashboard. You'll see three status LEDs:
  - **Mercury AI**: Shows if the AI assistant is online (green pulse = connected)
  - **Sim Worker**: Shows if the RunPod GPU Pod is running and connected (green pulse = active)
  - **Supabase DB**: Shows if the database is connected (green pulse = connected)
  
  If any indicator is red, the service may be temporarily unavailable. The `Recent Jobs` log underneath will show if your job failed or is still queued.

- **Worker Status**: GPU Pods are managed by a cost-aware autoscaler (v2.2.0) that spins pods up when jobs are queued and terminates them after 5 minutes idle. If no worker is shown, your job will be queued and a pod will start automatically.
  
- **Performance**: We are running on dedicated **RTX 3090/A40 GPU** clusters. The autoscaler enforces daily cost caps to keep infrastructure lean. If a simulation hangs for more than 5 minutes, try a refresh.

**Found a bug?** We’d love to hear from you. Send your feedback directly to **deploy@simhpc.com**.

---

*Thank you for helping us build the future of deterministic simulation!*
---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
