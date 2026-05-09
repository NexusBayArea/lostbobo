# System Architecture: Federated Graph Learning Layer

## Overview
As of May 2026, the Entity Graph supports **Federated Graph Learning** as a core runtime primitive. This system enables multiple plugins, tenants, or external nodes to contribute local graph updates (GNN training) while preserving data sovereignty and respecting temporal-causal invariants.

## Backend Components (`backend/core/runtime/entity_graph/federated_gnn.py`)
- **`FederatedGNN`**: Orchestrates federated learning rounds.
    - **`local_update`**: Performs local training on a plugin/tenant’s subgraph using `TemporalGNN`, extracting parameter deltas.
    - **`aggregate`**: Implements Federated Averaging (FedAvg) using temporal and trust-based weighting, with versions persisted via the `ModelRegistry`.

## Service Integration (`EntityGraphService`)
- **`federated_round`**: Orchestrates the federated training lifecycle: state snapshot, per-participant local updates, global aggregation, and event publishing of the round completion.

## Kernel Commands & API
- **Command Bus**: `FEDERATED_GNN_ROUND` command handler allows asynchronous orchestration of federated learning rounds within the Kernel-centered command flow.
- **REST API**: `/api/v1/graph/federated/round` (POST) triggers a training round.

## Frontend Integration
- **Federated Training Dashboard**: Monitors participating plugins, local vs. global loss, and convergence trends.
- **Embedding Explorer**: Enables cosine similarity search across federated node embeddings with temporal filtering.

## Observability & Invariants
- **Metrics**: `federated_rounds_total`, `local_update_latency_ms`, and `global_model_convergence` tracked via `ObservabilityService`.
- **Privacy & Security**: Federated updates are checked against causal consistency and provenance invariants. Supports differential privacy noise injection.
- **Persistence**: Updates are logged in `federated_model_updates` for auditability.
