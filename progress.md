# SimHPC Progress

## April 14, 2026

### Fixed: Explicit pytest paths (already done)

- **system_contract.py**: Uses `["python", "-m", "pytest", "-m", "dag", "tests"]`
- Explicit `tests` path ensures deterministic test discovery in CI
- Already pushed in commit 2a7980d

### Fixed: CI/runtime parity

- **dag-ci.yml**: Added PYTHONPATH, debug steps, explicit path to pytest

### Previously Fixed: CI dependency chain

- **dag-ci.yml**: Changed `api-ci` needs from `[lint]` to `[lint, tests]`

All tests pass:
```
[System Contract] -> DAG Validation
[PASS]
[System Contract] -> Runtime Contract
[PASS]
[System Contract] -> Trace Validation
[PASS]
[SYSTEM CONTRACT PASSED]
```