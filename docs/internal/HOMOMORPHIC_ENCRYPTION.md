# System Architecture: Homomorphic Encryption (HE) Graph Layer

## Overview
As of May 2026, the Entity Graph supports **Fully Homomorphic Encryption (HE)** as a first-class, privacy-preserving runtime primitive. This allows for secure computations—such as weighted aggregations and basic GNN inference—to be performed on encrypted entity features and edge weights, ensuring data sovereignty in cross-plugin, tenant, or federated analytics.

## Backend Components (`backend/core/runtime/entity_graph/homomorphic.py`)
- **`HomomorphicGraphEngine`**: Manages HE lifecycle and operations.
    - **Encryption**: Uses `paillier` (additive HE) to encrypt `WorldState` values and edge weights.
    - **`encrypt_graph_snapshot`**: Generates encrypted entity/edge snapshots and persists them to Supabase in a tamper-evident manner.
    - **`homomorphic_aggregate`**: Performs encrypted operations (e.g., sums, means) directly on ciphertexts without decryption.
    - **`homomorphic_gnn_inference`**: Executes inference layers on encrypted node/edge features.

## Service Integration (`EntityGraphService`)
- **`EntityGraphService`**: Serves as the high-level interface for triggering encryption (`encrypt_and_store`) and invoking HE-based analytics (`run_homomorphic_analytics`).

## Kernel Commands & API
- **Command Bus**: `HE_GRAPH_ENCRYPT` and `HE_GRAPH_AGGREGATE` handlers enable secure, asynchronous HE operations.
- **REST API**: `/api/v1/graph/he/encrypt` and `/api/v1/graph/he/aggregate` (POST) provide external access to the HE layer.

## Security & Observability
- **Key Management**: Private keys are restricted to secure contexts (Infisical + runtime enclave), while public keys enable secure encryption for analysis.
- **InvariantRegistry**: Enforces strict cipher-integrity checks and prevents plaintext leakage.
- **Metrics**: `he_operations_total` and `he_decryption_latency_ms` provide granular performance visibility while maintaining privacy.
