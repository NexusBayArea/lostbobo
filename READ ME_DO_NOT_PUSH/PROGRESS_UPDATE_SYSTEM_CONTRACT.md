## v24.3.3: Unified CI Validation Path (April 2026)

### Problem
The CI pipeline had split responsibilities for testing, with both the `tests` job running pytest directly and the `api-ci` job running the system contract. This created non-deterministic CI meaning and violated the principle of a single authoritative validation path.

### Solution
Refactored the CI workflow to establish `system_contract` as the sole authoritative validation path. The `tests` job was streamlined to focus only on structural validation (layout and imports), while `api-ci`'s dependencies were adjusted to ensure `system_contract` runs after linting.

### Changes Applied
- **Modified `.github/workflows/dag-ci.yml`**:
  - Replaced the 'Run pytest' step in the `tests` job with a placeholder, indicating that pytest runs are now exclusively handled within the system contract.
  - Updated the `api-ci` job's `needs` from `[lint, tests]` to `[lint]`, ensuring that the `system_contract` execution depends solely on the `lint` job.
