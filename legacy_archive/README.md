# Legacy Archive

This directory contains deprecated artifacts from v1.6.0-ALPHA through v2.2.1 that have been superseded by the v2.5.0 Structural Consolidation.

## Contents

| File/Directory | Origin | Replaced By |
|---|---|---|
| `robustness-orchestrator/` | v1.4.0-BETA | `services/api/` + `services/worker/` |
| `idle_timeout.py` | v2.2.1 | `services/worker/autoscaler.py` |
| `Dockerfile.worker` (root) | v2.1.2 | `services/worker/Dockerfile` |
| `requirements.worker.txt` (root) | v2.1.2 | `services/worker/requirements.txt` |

## Safety Note

These files are kept for reference only. Do NOT import from this directory.
Any code referencing `legacy_archive/` paths is a bug.

## When to Delete

Safe to delete after v2.6.0 release (all E2E tests pass against new structure).
