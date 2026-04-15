# SimHPC Progress

## April 14, 2026

### Fixed: CI/runtime parity

- **dag-ci.yml**: Added PYTHONPATH, debug steps, explicit path to pytest
- **system_contract.py**: Added explicit `tests` path to pytest calls

### Previously Fixed: CI dependency chain

- **dag-ci.yml**: Changed `api-ci` needs from `[lint]` to `[lint, tests]`
- Ensures system contract runs AFTER structural validation

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