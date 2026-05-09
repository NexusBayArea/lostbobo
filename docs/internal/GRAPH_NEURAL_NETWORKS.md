# System Architecture: Graph Neural Networks (GNN) Core

## Overview
As of May 2026, the Entity Graph includes native **Graph Neural Network (GNN)** capabilities as a first-class runtime primitive. This allows for deep structural learning directly on the live world-state graph, accounting for temporal decay, uncertainty propagation, and regime awareness without external graph databases.

## Backend Components (`backend/core/runtime/entity_graph/gnn.py`)
- **`TemporalGNN`**: A lightweight GNN architecture built on `torch_geometric` using `GATConv` (Graph Attention Networks) and `GCNConv`. It incorporates regime-specific embeddings to adjust for different runtime states (e.g., normal, panic, disruption).
- **`GraphNeuralEngine`**: Singleton engine responsible for GNN inference.
    - **`compute_node_embeddings`**: Runs GNN inference on the live Entity Graph, concatenating current WorldState entity features (uncertainty, decay-adjusted values) with learned embeddings.
    - **`predict_link`**: Provides temporal link prediction scores (probability of future influence) between nodes.

## Service Integration (`EntityGraphService`)
- **`get_pyg_data`**: Runtime converter that maps the Entity Graph and temporal edge weights to `torch_geometric.data.Data` objects for GNN consumption.

## Kernel Commands & API
- **Command Bus**: `GNN_COMPUTE_EMBEDDINGS` command handler allows asynchronous GNN inference through the Kernel-centered command flow.
- **REST API**: `/api/v1/graph/gnn/embeddings` (POST) triggers embedding computation.

## Frontend Integration (`frontend/src/components/GNNVisualizer.tsx`)
- **Visual Exploration**: Node colors and sizes reflect GNN embedding clusters (via PCA projection).
- **Influence Prediction**: Real-time link probability visualization and node similarity search.
- **Diagnostics**: Visualizes embedding stability across temporal replays.

## Observability & Invariants
- **Metrics**: `gnn_inference_total` and `gnn_embedding_dim` tracked via `ObservabilityService`.
- **Training**: Periodic self-supervised training conducted in the background via the Flywheel engine, with checkpoints stored in the `model_registry`.
- **Persistence**: Inference results cached via the `gnn_embeddings_cache` table.
