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
- **Link Expired**: Alpha links are valid for **7 days**. If yours expired, contact us at **deploy@simhpc.com**.
- **Performance**: We are running on dedicated **RTX 3090/A40 GPU** clusters; however, if a simulation hangs for more than 5 minutes, try a refresh.

**Found a bug?** We’d love to hear from you. Send your feedback directly to **deploy@simhpc.com**.

---

*Thank you for helping us build the future of deterministic simulation!*
