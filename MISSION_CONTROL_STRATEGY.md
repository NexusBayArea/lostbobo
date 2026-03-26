# SimHPC Mission Control: The Operational Cockpit

## 1. The Decision Architecture: O-D-I-A-V Loop

SimHPC is designed as an **Operational Cockpit** that facilitates the following cognitive loop for high-stakes engineering decisions:

| Phase | System Component | Operator Action | Decision Objective |
| :--- | :--- | :--- | :--- |
| **OBSERVE** | `ActiveSimulations.tsx` | Monitors convergence and GPU telemetry. | Is the physics fleet nominal? |
| **DETECT** | `AuditFeed.tsx` | Filters Rnj-1 AI Auditor anomaly flags. | Is there a discrepancy or risk? |
| **INVESTIGATE** | `SimulationMemory.tsx` | Drills into historical parameter ancestry. | Why did this deviate from baseline? |
| **ACT** | `CommandConsole.tsx` | Executes Intercept, Clone, or Boost. | How do I resolve the drift? |
| **VERIFY** | `GuidanceEngine.tsx` | Validates results against RAG anchors. | Is the final artifact verified? |

---

## 2. Cockpit Components: The Operator Experience

### A. The Temporal Axis: `SimulationTimeline.tsx`

#### "The Flight Path"


An interactive horizontal marquee that treats a simulation run as a life-cycle, not a record.

- **Markers:** 🟢 Dispatch → 💠 Convergence Lock → ⚠️ AI Audit Warning → ⚓ Operator Intercept → ✅ Final Physics Sign-off.
- **Value:** The operator can scrub back through the timeline to see exactly *when* a design began to diverge from the physical bench data.

### B. The Command Surface: `CommandConsole.tsx`

#### "The Action Center"


A centralized dashboard for explicit decision execution.

- **`[INTERCEPT]`**: Puts an active simulation into 'Physics Pause' mode, allowing boundary condition adjustments mid-flight.
- **`[CLONE & RE-RUN]`**: Instant branch creation: "Iteration B" derived from "Iteration A".
- **`[BOOST PRIORITY]`**: Hot-swaps GPU allocation to the critical path.
- **`[EXECUTE CERTIFICATION]`**: Triggers the cryptographic NAFEMS report generation.

### C. Iteration Intelligence: `SimulationMemory.tsx`

#### "The Ancestry Engine"


Proves *why* an engineer made a specific design shift.

- **Lineage Tree:** A visual graph of parent-child relationships between simulation runs.
- **Delta Overlay:** Side-by-side parameter highlighting (Red/Green) for flux and pressure deltas.
- **RAG Anchor:** Direct clickable links to the document (e.g., 'Lab_Report_2024.pdf') that informed the iteration.

### D. Guidance Engine: `GuidanceEngine.tsx`

#### "The Navigator"


Moves beyond "Insights" into "Operator Guidance."

- **Persona:** Professional, directive, and evidence-backed.
- **Output:** *"Guidance: Heat flux (52W) exceeds 2024 Project Alpha safety factor. Recommend 5% reduction in cooling inlet pressure."*

### E. System Health Monitor: `SystemStatus.tsx`

#### "The Heartbeat"


A left-sidebar component for real-time visibility into the distributed alpha infrastructure.

- **Service Telemetry:** Live pulsing LEDs for Mercury AI, RunPod GPUs, Supabase DB, and Sim Worker.
- **Recent Jobs Log:** A fast 20-line debugging scroller to identify GPU timeouts, failed jobs, or stuck dispatch queues.
- **Fleet Dashboard (v2.2.0):** Admin view at `/api/v1/admin/fleet` showing running pods, queue depth, daily cost, and scaling events. Powered by the cost-aware autoscaler with daily budget caps.

---

## 3. 10-Minute Pilot: Panel-Driven Onboarding

| Minute | Panel Focus | Narrative Hook |
| :--- | :--- | :--- |
| **1-2** | `ActiveSimulations` | "Commander, the fleet is nominal. Baseline dispatching now." |
| **3-4** | `AuditFeed` | "Anomaly detected. AI summary contradicts solver reality. Auditor has flagged the run." |
| **5-6** | `SimulationMemory` | "Investigating ancestry... comparison with 2024 benchmark proves the flux is too high." |
| **7-8** | `CommandConsole` | "Intercepting and cloning. We've adjusted the design mid-flight. Re-launching Child-1." |
| **9-10** | `ComplianceExport` | "Physics verified. Final certificate generated. Mission complete." |

---

## 4. Technical Implementation Layer

### API Specification (Control Subsystem)

- **`POST /api/v1/control/command`**: Payload: `{ action: 'intercept' | 'clone' | 'boost', run_id: string, params?: object }`
- **`GET /api/v1/control/timeline`**: Returns an array of temporal events for the `SimulationTimeline` marquee.
- **`GET /api/v1/control/lineage`**: Returns the tree structure of historical iterations.

### Frontend State (Supabase Realtime)

The O-D-I-A-V loop is synchronized via Supabase Realtime channels. The `controlRoomStore.ts` listens for `SOLVER_EVENT` and `AUDIT_ALERT` payloads to hydrate the `CommandConsole` and `SimulationTimeline` without page refreshes.
