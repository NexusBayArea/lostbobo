# Execution Observability System Spec

## 1. Core Principles
Everything is a versioned, replayable execution graph.

## 2. Canonical Trace Schema
```json
{
  "version": "trace.v1",
  "contract_version": "1.2.0",
  "run_id": "uuid",
  "timestamp": "iso8601",
  "nodes": [
    {
      "id": "lint",
      "type": "ci_gate",
      "status": "pass | fail",
      "start": 1710000000.0,
      "end": 1710000001.2,
      "duration": 1.2,
      "inputs": {},
      "outputs": {},
      "artifacts": [{"type": "log", "path": "logs/lint.txt"}],
      "metrics": {"cpu": 0.12, "mem": 128},
      "error": null
    }
  ]
}
```

## 3. UI Models
### Replay Controls
```json
{
  "run_id": "uuid",
  "mode": "step | full | fork",
  "current_node": "lint",
  "state": {"inputs": {}, "outputs": {}, "artifacts": []},
  "controls": {"play": true, "pause": true, "step": true, "rewind": true}
}
```

### Diff Semantics
- Structural diff (nodes added/removed)
- Behavioral diff (status change)
- Performance diff (duration delta)
- Contract diff (schema/version mismatch)

## 4. System Integration
- CI Run -> DAG Executor -> TRACE_NODES -> capture_trace() -> trace.json -> Dashboard
- Storage: `trace_latest.json` (latest), `ci_history/*.json` (history)
