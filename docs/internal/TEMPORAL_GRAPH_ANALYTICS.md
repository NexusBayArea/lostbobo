# System Architecture: Temporal Graph Analytics Layer

## Overview
As of May 2026, the Entity Graph supports native **temporal analytics** as core runtime primitives. These algorithms are time-aware, probabilistic, and respect causal ordering and regime shifts—tightly integrated with the `TemporalEngine`, `WorldState`, and `Event Fabric`.

## Backend Components (`backend/core/runtime/entity_graph/temporal_analytics.py`)
- **`TemporalGraphAnalytics`**: Central engine for time-decayed graph analysis.
    - **`temporal_centrality`**: Computes time-decayed PageRank and degree centrality. Includes a "burst score" for detecting sudden weight increases in specific nodes.
    - **`temporal_community_evolution`**: Tracks community splits, merges, and changes across specified temporal windows.
    - **`shortest_temporal_paths`**: Finds time-respecting causal paths, factoring in uncertainty accumulation.
    - **`change_point_detection`**: Analyzes statistical shifts in graph structure and centrality to flag regime changes.

## Service Integration (`EntityGraphService`)
- **Unified Dispatcher**: `run_temporal_analytics(algorithm, **kwargs)` provides a consistent interface to dispatch requested analytics.
- **Data Model**: Leverages `networkx` for lightweight, in-memory graph representation derived from current/historical Supabase snapshots.

## Kernel Commands & API
- **Command Bus**: `TEMPORAL_GRAPH_ANALYTICS` handler supports async execution of analytic routines.
- **REST API**: `/api/v1/graph/temporal-analytics` (POST) routes requests to the Kernel command bus.

## Frontend Integration (`frontend/src/components/TemporalGraphAnalytics.tsx`)
- **Centrality Tab**: Leaderboards for influencers and real-time burst alerts.
- **Timeline Explorer**: Visualizes community evolution (splits/merges) over time.
- **Causal Path Explorer**: Interactive node selection to view influence chains with uncertainty metrics.
- **Change Point Alerts**: UI alerts on structural regime shifts.

## Observability & Invariants
- **Metrics**: `temporal_pagerank_computed`, `change_points_detected`, `temporal_path_length_avg` (via `ObservabilityService`).
- **Invariants**: `no negative weights after decay`, `causal paths respect vector clocks`.
- **Regime Awareness**: All analytic routines automatically ingest current regime state from the `TemporalEngine`.
