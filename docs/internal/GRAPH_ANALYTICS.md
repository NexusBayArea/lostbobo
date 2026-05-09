# System Architecture: Graph Analytics Layer

## Overview
As of May 2026, the Entity Graph includes a rich set of production-grade analytics algorithms as **first-class runtime primitives**. These algorithms are temporally-aware, probabilistic, and fully integrated with `WorldState`, the `Temporal Engine`, and the `InvariantRegistry`, running efficiently on `Supabase + Postgres`.

## Backend Components (`backend/core/runtime/entity_graph/analytics.py`)
- **`GraphAnalytics`**: Central class for analytics primitives.
    - **`compute_centrality`**: PageRank + Degree centrality using temporal decay weights (`weight * decay * (1 - uncertainty)`).
    - **`detect_communities`**: Louvain-style community detection with regime awareness.
    - **`compute_influence_paths`**: Dijkstra-based shortest causal influence paths with uncertainty propagation.
    - **`temporal_evolution_metrics`**: Change detection for emerging nodes and edge strength evolution over time.

## EntityGraphService Integration
- **Unified Entrypoint**: `run_analytics(algorithm: str, **kwargs)` provides a consistent interface to dispatch requested analytics.
- **Data Access**: `get_nodes_snapshot` provides fast snapshots joined with `WorldState` values via `state_key`.

## Kernel Commands & API
- **Command Bus**: `GRAPH_ANALYTICS_RUN` command handler enables asynchronous execution of graph analytics within the Kernel-centered command flow.
- **REST API**: `/api/v1/graph/analytics` (POST) routes analytic execution to the command bus.

## Frontend Integration (`frontend/src/components/GraphAnalyticsPanel.tsx`)
- **Leaderboards**: Visualizes PageRank-based "Top Influencers".
- **Clustering**: Displays community clusters via colored ReactFlow subgraphs.
- **Heatmaps**: Represents influence paths with edge thickness tied to temporal weights.
- **Evolution**: Visualizes the emergence and decay of nodes/edges over time.

## Observability & Invariants
- **Metrics**: `graph_pagerank_max`, `communities_detected`, `influence_path_length_avg` tracked via `ObservabilityService`.
- **Invariants**: `No zero-weight cycles`, `Connected component stability`, `Weight normalization`.
- **Persistence**: Results cached via `graph_analytics_cache` table.
