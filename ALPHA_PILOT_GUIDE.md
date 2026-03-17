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
- **System Health Indicators**: Check the left sidebar on the Dashboard. You'll see three status LEDs:
  - **Mercury AI**: Shows if the AI assistant is online (green pulse = connected)
  - **Sim Worker**: Shows if the RunPod worker is warm and ready (green pulse = warm)
  - **Supabase DB**: Shows if the database is connected (green pulse = connected)
  
  If any indicator is red, the service may be temporarily unavailable. The `Recent Jobs` log underneath will show if your job failed or is still queued.

- **Metadata-Only Ping**: The Sim Worker status is checked using a lightweight metadata-only ping that doesn't trigger GPU spin-up, keeping costs low while providing real-time feedback.
  
- **Performance**: We are running on dedicated **RTX 3090/A40 GPU** clusters; however, if a simulation hangs for more than 5 minutes, try a refresh.

**Found a bug?** We’d love to hear from you. Send your feedback directly to **deploy@simhpc.com**.

---

*Thank you for helping us build the future of deterministic simulation!*

---
## Appendix: Mercury AI Usage in Alpha

### 1. Where Mercury Is Used in Alpha

In your current Alpha architecture, **Mercury should only be used in two places**:

#### 1️⃣ Simulation Setup Assistance

Mercury helps interpret user inputs into simulation parameters.

Example:

User input:
```
simulate high temperature stress
```

Mercury converts it into structured parameters:
```
temperature: 45
duration: 48h
wind: moderate
```

Then the simulation module runs.

So the flow is:
```
User Input
↓
Mercury interpretation
↓
Simulation parameters
↓
RunPod simulation
```

#### 2️⃣ Notebook Generation

Mercury writes the **explanatory text** inside the notebook.

Example:

Simulation output:
```
voltage_drop = 8%
temperature = 42C
```

Mercury generates:
```
The simulation indicates that elevated temperatures resulted in an 8% voltage drop,
suggesting increased thermal stress on the battery system.
```

So the flow is:
```
Simulation results
↓
Mercury explanation
↓
Notebook summary
```

### 2. Where Mercury Should NOT Be Used in Alpha

Avoid using Mercury for:

❌ actual physics simulations
❌ experiment selection
❌ simulation validation

### 3. Simple Mercury Health Test

The easiest test is to create a **test endpoint**.

Example:

Node.js example:
```javascript
export async function testMercury(req, res) {
  const response = await fetch("https://api.inceptionlabs.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.MERCURY_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "mercury",
      messages: [
        { role: "user", content: "Return the word SIMHPC_OK" }
      ]
    })
  });

  const data = await response.json();
  res.json(data);
}
```

Expected response:
```
SIMHPC_OK
```

If you get that, Mercury is working.

### 4. Test From Terminal

You can test Mercury directly with curl:
```
curl https://api.inceptionlabs.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mercury",
    "messages": [
      {"role":"user","content":"reply SIMHPC_OK"}
    ]
  }'
```

Expected output:
```
SIMHPC_OK
```

### 5. What Alpha Mercury Usage Should Look Like

Ideal Alpha flow:
```
User runs simulation
↓
RunPod executes model
↓
Results returned
↓
Mercury writes explanation
↓
Notebook generated
```

So Mercury is **assistive**, not core.

### 6. Quick Mercury Test Inside Your System

The fastest test you can run right now:

Add this temporary call inside notebook generation:

Prompt:
```
Explain the following simulation result in one sentence.
```

If the notebook text appears → **Mercury is working**.
