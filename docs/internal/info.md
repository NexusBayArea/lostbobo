# Documentation Info

Using Node.js 20, Tailwind CSS v3.4.19, and Vite v7.2.4

Tailwind CSS has been set up with the shadcn theme

Setup complete: /mnt/okcomputer/output/app

Components (40+):
  accordion, alert-dialog, alert, aspect-ratio, avatar, badge, breadcrumb,
  button-group, button, calendar, card, carousel, chart, checkbox, collapsible,
  command, context-menu, dialog, drawer, dropdown-menu, empty, field, form,
  hover-card, input-group, input-otp, input, item, kbd, label, menubar,
  navigation-menu, pagination, popover, progress, radio-group, resizable,
  scroll-area, select, separator, sheet, sidebar, skeleton, slider, sonner,
  spinner, switch, table, tabs, textarea, toggle-group, toggle, tooltip

Usage:
    import { Button } from '@/components/ui/button'
    import { Card, CardHeader, CardTitle } from '@/components/ui/card'

Structure:
    src/sections/        Page sections
    src/hooks/           Custom hooks
    src/types/           Type definitions
    src/App.css          Styles specific to the Webapp
    src/App.tsx          Root React component
    src/index.css        Global styles
    src/main.tsx         Entry point for rendering the Webapp
    index.html           Entry point for the Webapp
    tailwind.config.js   Configures Tailwind's theme, plugins, etc.
    vite.config.ts       Main build and dev server settings for Vite
    postcss.config.js    Config file for CSS post-processing tools

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

---

## Session Log: April 15, 2026 - DAG Trace & Replay Features

### Features Implemented

1. **Extended Trace Layer** (`tools/runtime/trace.py`)
   - Node structure now includes: status, start, end, duration, error, stdout, stderr, command
   - `end_node()` captures result.stdout, result.stderr, result.args

2. **Kernel Integration** (`tools/runtime/kernel.py`)
   - `run_node()` now passes result to trace for recording
   - Captures exact command used for each node execution

3. **Replay Engine** (`tools/runtime/replay.py`)
   - Deterministic reproduction of CI failures locally
   - Usage: `python tools/runtime/replay.py` (failed nodes)
   - Usage: `python tools/runtime/replay.py full` (entire DAG)
   - Zero-drift debugging with CI parity

4. **Admin API Endpoints** (`src/app/api/admin/observability.py`)
   - `POST /admin/replay` - replay failed nodes
   - `POST /admin/replay/full` - replay entire DAG
   - Uses subprocess.Popen for async execution

5. **Admin UI Updates** (`frontend/src/pages/admin/AdminAnalyticsPage.tsx`)
   - New "DAG Trace" tab in sidebar
   - Table showing nodes with status, duration, actions
   - "View" button opens dialog with stdout/stderr/command
   - "Replay Failed" and "Replay Full" buttons

6. **API Client** (`frontend/src/lib/api.ts`)
   - Added: `getTrace()`, `replayFailed()`, `replayFull()`
   - Added: `getFleetStatus()`, `getFleetMetrics()`, `stopPod()`, `terminatePod()`

### Commands Run

```bash
# Ruff lint check (found unused import)
python -m ruff check . --exit-non-zero-on-fix

# Fix and commit
git add -f tools/runtime/kernel.py tools/runtime/trace.py ...
git commit -m "feat(trace): Add DAG trace with replay engine..."
git push origin main

# Ruff fix for bootstrap.py
python -m ruff check . --exit-non-zero-on-fix --fix
git commit -m "fix: Remove unused CONTRACT import in bootstrap.py"
git push origin main
```

### Files Modified

- `tools/runtime/trace.py` - Extended node structure
- `tools/runtime/kernel.py` - Pass result to trace
- `tools/runtime/replay.py` - Replay engine (new file)
- `src/app/api/admin/observability.py` - Added replay endpoints
- `frontend/src/lib/api.ts` - Added API methods
- `frontend/src/pages/admin/AdminAnalyticsPage.tsx` - Trace tab UI
- `tools/bootstrap.py` - Removed unused import (ruff fix)
- `frontend/README.md` - Updated kernel entry (ruff fix)

### Not Committed (per user request)

- `ROADMAP.md` - Updated with v2.6.0 features

---

## Session Log: April 15, 2026 - Unified CI Gate

### Features Implemented

1. **Pre-commit Config** (`.pre-commit-config.yaml`)
   - ruff v0.4.4 with --fix and ruff-format
   - Auto-formats on every commit

2. **Unified CI Gate** (`tools/ci_gate.py`)
   - Single deterministic pipeline in order:
     1. format-check: `ruff format . --check`
     2. lint: `ruff check . --exit-non-zero-on-fix`
     3. import-graph: `python -c "import tools.runtime.kernel"`
     4. contract: `python tools/bootstrap.py ci`
   - Local == CI identical ordering
   - Failures reproducible, no "works locally" drift

3. **Makefile Alias**
   - `make ci` runs the unified gate
   - Drop-in implementation for developers

### Commands Run

```bash
# Test the gate
python tools/ci_gate.py

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Files Created

- `.pre-commit-config.yaml` - Pre-commit configuration
- `tools/ci_gate.py` - Unified CI gate
- `Makefile` - Make alias

### Not Committed (per user request)

- `ROADMAP.md` - Updated with v2.6.0 features (not pushed)
- `docs/internal/info.md` - Session log (not pushed)

---

## Session Log: April 15, 2026 - Distributed Kernel v2

### Features Implemented

1. **Distributed Kernel Core** (`tools/runtime/kernel.py`)
   - `Task` dataclass: id, fn, deps, retries
   - `Lease` dataclass: task_id, worker_id, lease_id, expires_at (crash-safety)
   - `TaskState` dataclass: status (pending/leased/running/success/failed), attempt, result
   - `Queue` abstraction with `InMemoryQueue` implementation
   - `Kernel` class with:
     - `add_task()` - register tasks
     - `lease_task()` - assign task to worker with lease
     - `report_success()` / `report_failure()` - worker results
     - `snapshot()` - observability
   - `Worker` class: stateless executor that leases and reports

2. **Architecture Change**
   - Kernel = scheduler + lease management (no direct execution)
   - Workers = execution plane only
   - Queue = decoupling layer
   - Enables horizontal scaling, crash-safe execution, retry-safe DAG

3. **Legacy Support**
   - DAG kernel functions retained for bootstrap compatibility

### Files Modified

- `tools/runtime/kernel.py` - Added distributed Kernel v2 classes

### Not Committed (per user request)

- `ROADMAP.md` - Will be updated

---

## Session Log: April 15, 2026 - CI Gate Update

### Changes Made

1. **CI Workflow** (`.github/workflows/dag-ci.yml`)
   - Added: `pip install -e .` after pip upgrade
   - Changed: `python tools/bootstrap.py ci` → `python -m tools.bootstrap ci`

### Files Modified

- `.github/workflows/dag-ci.yml` - CI gate workflow

---

## Session Log: April 15, 2026 - pyproject.toml Fix

### Changes Made

1. **pyproject.toml**
   - Changed: `include = ["tools*"]` → `include = ["tools", "tools.*"]`
   - Enables proper editable install for nested packages

### Verification

```bash
pip install -e .
python -c "from tools.runtime.deps import validate_lock; print('OK')"
```
Output: `OK`

### Files Modified

- `pyproject.toml` - Package discovery configuration

---

## Session Log: April 15, 2026 - Explicit Package Fix

### Changes Made

1. **pyproject.toml** (explicit packages)
   ```toml
   [tool.setuptools]
   packages = ["tools", "tools.runtime"]
   ```
   - Removed auto-discovery, using explicit package list

### Verification

```bash
pip install -e .
python -c "from tools.runtime.deps import validate_lock; print('OK')"
```
Output: `OK`

### Files Modified

- `pyproject.toml` - Explicit packages configuration
