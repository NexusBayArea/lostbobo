# System Architecture: Graph Visualization Tools

## Overview
As of May 2026, the Entity Graph and WorldState possess production-grade, real-time visualization tooling. These tools provide lightweight, reactive visualization that is fully integrated with the system's temporal probabilistic runtime.

## Backend Components (`backend/app/api/graph_viz.py`)
- **`/api/v1/graph/entity-graph`**: Live snapshot of the Entity Graph with temporal weights.
- **`/api/v1/graph/world-state-graph`**: Combined view of the current `WorldState` and Entity Graph, including regime and entropy metrics.
- **`/api/v1/graph/replay`**: Historical graph reconstruction at a specified timestamp.

## Frontend Components
### 1. `EntityGraphVisualizer.tsx`
- **Technology**: ReactFlow + React Query.
- **Features**: 
    - Live updates (8s interval).
    - Temporal decay visualization (node opacity maps to 1 - uncertainty).
    - Causal hierarchical layout via `dagre`.

### 2. `WorldStateTimeline.tsx`
- Provides a horizontal slider to replay world state and graph data at historical timestamps via the `replay_graph` endpoint.

## Dashboard Integration (`CoreDashboard.tsx`)
- Integrates Live Entity Graph, World State Evolution, and Causal Event Stream.
- SSE subscription (`/api/v1/world-state/stream`) for zero-latency UI updates.
- Grafana dashboard embedding for invariant health monitoring.

## Tooling & Observability
- **Force-Directed Layout**: Automatic hierarchical layout based on causal relationships.
- **Temporal Heatmap**: Opacity decay based on `half_life_s`.
- **Telemetry**: All endpoints are protected by tenant isolation and instrumented with OTEL spans and custom observability metrics.
