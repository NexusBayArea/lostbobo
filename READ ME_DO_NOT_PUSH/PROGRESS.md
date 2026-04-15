# Progress Update

DO NOT PUSH!!!!

# SimHPC Progress

## April 14, 2026

### Fixed: src layout and CI workflow

- **pyproject.toml**: 
  - Added `src = ["src"]` to ruff config
  - Added `packages = ["app", "worker"]` to setuptools
  - Fixed `license = { text = "MIT" }`
  - Added `uv>=0.4.0` to dev/ci deps
  - Added dag/runtime/trace markers to pytest config
  
- **dag-ci.yml**:
  - Changed lint to `src/ tests/ tools/` paths
  - Changed tests to check `src/app/ src/worker/ tests/ tools/`
  - Added explicit pytest run in tests job
  - Simplified api-ci to run only system contract

- **hardened-build.yml**: (NEW)
  - Added workflow_run trigger to gate on deterministic-api-ci
  - Hardcoded IMAGE_NAME to avoid case issues
  - Removed unused id-token: write permission
  - Explicit Dockerfile path
  - Tag with SHA only at build time
  - Promote-to-prod job with immutable digest

- **Lint fixes**: Ran `ruff check . --fix` - fixed 13 unused import errors

- **dag-ci.yml**: Replaced with Unified CI Gate
  - Single `ci-gate` job instead of multiple jobs
  - Phase 1: Static checks (ruff lint, format)
  - Phase 2: Contract system (bootstrap.py)
  - Phase 3: Tests (pytest)
  - Phase 4: Docker build
  - Hard stop at every layer

- **dag-ci.yml (Strict mode)**:
  - Added `--exit-non-zero-on-fix` to ruff lint
  - Added `--strict-markers --strict-config` to pytest
  - Added pytest-asyncio to deps
  - Contract system as HARD GATE (no continuation on failure)

- **pytest.ini**: Added `asyncio_mode = auto` for async test support

- **Contract Manifest + DAG Validator**: (NEW)
  - Created `tools/ci_manifest.yml` - declares required system nodes
  - Created `tools/ci_gates/dag_validator.py` - validates manifest integrity
  - Updated `tools/bootstrap.py` - runs dag_validator before system_contract
  - CI now fails immediately if any required node is missing

- **Runtime DAG Executor**: (NEW)
  - Created `tools/runtime/dag_executor.py` - deterministic execution engine
  - Topological ordering based on `depends_on` in manifest
  - Updated `tools/ci_manifest.yml` with dependency edges
  - Created `tools/runtime/test_isolation.py` - test isolation layer
  - `tools/bootstrap.py` now runs dag_executor instead of individual steps

- **Self-healing Dependency System**: (NEW)
  - Created `tools/deps/dependency_scanner.py` - extracts imports from DAG nodes
  - Created `tools/deps/self_heal_deps.py` - resolves missing dependencies
  - Added `ALLOWED_AUTO_INSTALL` whitelist for safety
  - Updated `tools/bootstrap.py` to run healing phase before DAG execution
  - Healing only runs BEFORE DAG execution (not during)

- **Dependency Drift Detection Workflow**: (NEW)
  - Created `.github/workflows/dependency-drift.yml`
  - Checks lockfile drift with `uv pip compile`
  - Verifies resolution consistency
  - Tests runtime import capability

- **Lock Validation in Bootstrap**: (NEW)
  - Added dependency lock validation to `tools/bootstrap.py`
  - Runs BEFORE healing phase
  - Compares requirements.lock with fresh compile from pyproject.toml
  - Fails CI if drift detected
  - Regenerated requirements.lock with latest resolved versions

- **Runtime Kernel**: (NEW)
  - Created `tools/runtime/kernel.py` - single execution kernel
  - Updated `tools/runtime/dag_executor.py` to delegate to kernel
  - DAG executor now uses `[KERNEL]` prefix for logging
  - Added `tools` to STANDARD_LIBRARY to fix import detection
  - Kernel enforces topological ordering with dependency validation

- **Dependency Drift Workflow Fix**: (UPDATED)
  - Removed freeze validation (not deterministic)
  - Replaced with install consistency check (`import fastapi, pydantic, yaml`)
  - Now validates "can locked graph actually execute"

- **Bootstrap Fix**: Fixed ambiguous variable name (`l` → `line`)

- **Self-Contained Dependency Kernel**: (NEW)
  - Replaced uv-based validation with self-contained validator
  - No external tools required at runtime
  - Validates lockfile format, pinned versions only
  - Removed compilation step (only verifies committed artifacts)

- **DAG Execution Fix**: Replaced dag_executor with dag_compiler
  - bootstrap now runs `tools/ci_gates/dag_compiler.py` instead of dag_executor
  - Compiler outputs JSON execution plan (not runtime execution)

- **Bootstrap Cleanup**: Removed runtime DAG executor completely
  - Deleted `tools/runtime/dag_executor.py`
  - Added DAG contract validation step
  - Validates JSON output from dag_compiler
  - Bootstrap now only validates, no execution orchestration

- **Lock Normalization**: Added `normalize_lock()` for stable ordering

- **Zero-Drift Dependency Kernel**: (NEW)
  - Created `tools/deps/lock.py` for deterministic lock generation
  - Replaced old dependency validation with kernel-based validation
  - Uses `uv pip compile` with `--no-header` for clean output
  - `--write` flag to update lockfile when needed
  - Normalizes and sorts dependencies for stable comparison

- **Hermetic Dependency Kernel**: (NEW)
  - Created `tools/deps/hermetic_lock.py` with cryptographic validation
  - Uses SHA256 hash instead of diff-based comparison
  - Generates `.requirements.lock.hash` for sealed verification
  - `--write` updates lock and seals with hash
  - Eliminates environment-based formatting drift

- **CI Toolchain Fix**: Added uv install to dag-ci.yml and dependency-drift.yml
  - Added uv install step before bootstrap in both workflows
  - Added `$HOME/.local/bin` to GITHUB_ENV (not GITHUB_PATH)
  - Added pyyaml to Python deps for hermetic_lock.py

All tests pass locally:
```
[System Contract] -> DAG Validation
[PASS]
[System Contract] -> Runtime Contract
[PASS]
[System Contract] -> Trace Validation
[PASS]
[SYSTEM CONTRACT PASSED]
```

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


## Session: April 14, 2026 (YYYY-MM-DD)

### Task 1: Fix dag-ci.yml and Update PROGRESS.md (Initial Request)
- **Problem**: `dag-ci.yml` had incorrect flat layout assertions and linting paths. `PROGRESS.md` needed updating.
- **Solution**:
  - Corrected `ruff` commands in the `lint` job to target `app/ worker/ tests/`.
  - Modified `Assert flat layout integrity` step in the `tests` job to correctly check `app/`, `worker/`, and `tests/`.
  - Modified `Verify package imports` step in the `tests` job to check both `app` and `worker` imports.
  - Attempted to update `READ ME_DO_NOT_PUSH/PROGRESS.md` (first attempt).
- **Outcome**: `dag-ci.yml` was fixed. `READ ME_DO_NOT_PUSH/PROGRESS.md` was not successfully updated by the agent due to file access issues, but the changes were prepared.

### Task 2: Implement System Contract and Unify CI Validation Path
- **Problem**: CI lacked a unified validation path; `pytest` ran directly in the `tests` job, and `api-ci` ran system contract checks, leading to non-deterministic CI. `PROGRESS.md` still needed updating.
- **Solution**:
  - Created `tools/ci_gates/system_contract.py` as a thin orchestration layer for CI checks.
  - Overwrote `tools/bootstrap.py` to call `system_contract.py`.
  - Modified `dag-ci.yml` to:
    - Replace individual validation steps in `api-ci` with a single call to `python tools/bootstrap.py ci`.
    - Replace the `Run pytest` step in the `tests` job with a placeholder.
    - Adjusted `api-ci`'s `needs` from `[lint, tests]` to `[lint]`.
  - Attempted to update `READ ME_DO_NOT_PUSH/PROGRESS.md` (second attempt via workaround file) but was eventually resolved by user manual update.
- **Outcome**: `system_contract.py` was created, `bootstrap.py` and `dag-ci.yml` were updated to establish a unified CI validation path. `READ ME_DO_NOT_PUSH/PROGRESS.md` was updated manually by the user with the provided content.

### Task 3: Implement Trace Validation
- **Problem**: Need to prove deterministic execution behavior (same DAG + same inputs -> identical execution trace).
- **Solution**:
  - Created `tests/trace/test_trace_determinism.py` with a test that runs a DAG, captures its trace, runs it again, and compares normalized traces for determinism.
  - Modified `tools/ci_gates/system_contract.py` to include a "Trace Validation" step calling `pytest -m trace`.
- **Outcome**: Trace validation implemented and integrated into the system contract.

### General Notes
- Encountered persistent issues with `read_file` and `write_file` for files under `READ ME_DO_NOT_PUSH/` due to `.gitignore` interactions, leading to manual user intervention for `PROGRESS.md` updates.
- Implemented a new memory to strictly adhere to "DO NOT PUSH" directives for specified paths.

## v24.3.3: Unified CI Validation Path (April 2026)

### Problem
The CI pipeline had split responsibilities for testing, with both the `tests` job running pytest directly and the `api-ci` job running the system contract. This created non-deterministic CI meaning and violated the principle of a single authoritative validation path.

### Solution
Refactored the CI workflow to establish `system_contract` as the sole authoritative validation path. The `tests` job was streamlined to focus only on structural validation (layout and imports), while `api-ci`'s dependencies were adjusted to ensure `system_contract` runs after linting.

### Changes Applied
- **Modified `.github/workflows/dag-ci.yml`**:
  - Replaced the 'Run pytest' step in the `tests` job with a placeholder, indicating that pytest runs are now exclusively handled within the system contract.
  - Updated the `api-ci` job's `needs` from `[lint, tests]` to `[lint]`, ensuring that the `system_contract` execution depends solely on the `lint` job.


---

## v24.3.1: CI dag-ci.yml Layout Fix (April 2026)

### Problem
The `dag-ci.yml` CI workflow was not correctly asserting the flat layout and package imports for `app/`, `worker/`, and `tests/` directories. This could lead to issues not being caught in CI related to project structure.

### Solution
Updated `dag-ci.yml` to correctly check for the flat layout of `app/`, `worker/`, and `tests/` directories, and to verify package imports for both `app` and `worker`.

### Changes Applied
- **Fixed `dag-ci.yml`**:
  - Modified the `lint` job to run `ruff check` and `ruff format --check` on `app/ worker/ tests/`.
  - Modified the `tests` job's `Assert src layout integrity` step to `Assert flat layout integrity` and updated the `run` command to check for `app/`, `worker/`, and `tests/`.
  - Modified the `tests` job's `Verify package import` step to `Verify package imports` and updated the `run` command to import both `app` and `worker`.

---

## v24.3.0: CI Final Stabilization & Layout Verification (April 2026)

### Problem
Minor workflow redundancies and non-optimal step exit codes were identified in the CI pipeline. Diagnostic prints were overly verbose for standard passes.

### Solution
Applied a final refined CI configuration with streamlined layout verification and optimized status reporting. Standardized package import checks for concise "OK" signals.

### Changes Applied
- **Finalized API CI**: Updated .github/workflows/dag-ci.yml with:
  - Streamlined 'Assert src layout integrity' implementation in the primary 'tests' gate.
  - Optimized 'Verify package import' and 'Verify full import graph' for clean, production-grade output.
  - Hard-coded exit failure on Dockerfile absence in 'worker-build' for immediate job termination.
  - Standardized linting sequence to ensure consistent signal quality.

---

## v24.2.0: CI DAG Optimization & Import Diagnostic Upgrade (April 2026)

### Problem
Redundant layout checks in downstream jobs were cluttering the pipeline. Use of 'outputs: sha' was logically unnecessary and fragile. Basic 'python -c' imports lacked deep diagnostic detail.

### Solution
Centralized structure assertions in the 'tests' job. Replaced custom outputs with global '${{ github.sha }}' for worker builds. Upgraded import checks to use 'importlib' for superior stack traces.

### Changes Applied
- **Optimized API CI**: Updated .github/workflows/dag-ci.yml with:
  - Centralized 'Assert src layout integrity' in 'tests' job only.
  - Removed 'outputs: sha' from 'api-ci' job; updated 'worker-build' to use global 'github.sha'.
  - Upgraded import validation to use 'importlib.import_module' for better error reporting.

---

## v24.1.1: YAML Syntax Guard — Workflow Hardening (April 2026)

### Problem
`Invalid workflow file: .github/workflows/dag-ci.yml#L66` — Plain scalar parsing error in YAML due to a colon followed by a space `: ` inside a single-line `run` command.

### Solution
Converted the single-line `run` command to a multi-line pipe `|` block. This informs the YAML parser to treat the content as a literal block, preventing it from misinterpreting colons or special characters as key-value separators.

### Changes Applied
- **Fixed `dag-ci.yml`**: Wrapped line 66 in a `|` block for safe execution of Python one-liners containing colons and emojis.

---

## v24.1.0: Deterministic CI Hardening & Import Validation (April 2026)

### Problem
Potential for silent packaging regressions if the src layout is partially missing or if dependencies are only partially installed. Linting signals were also slightly out of order.

### Solution
Added hard assertion for src layout integrity and full import graph validation (app + worker). Reordered ruff tasks for better signal quality.

### Changes Applied
- **Hardened API CI**: Updated .github/workflows/dag-ci.yml with:
  - 'Assert src layout integrity' step using explicit 'test -d src/app' checks.
  - 'Verify full import graph (app + worker)' to ensure both packages are correctly installed and importable.
  - Swapped ruff order to run 'ruff format --check' before 'ruff check'.

---

## v24.0.0: Final Deterministic CI & src Layout Alignment (April 2026)

### Problem
CI paths were still assuming a flat layout or were non-deterministic with ruff pathing. Import validation was missing, leading to potential silent packaging regressions.

### Solution
Hard-locked the CI to use 'pip install -e ".[dev]"' and explicit 'python -c "import app"' validation. Standardized ruff to check the entire root with src layout awareness.

### Changes Applied
- **Deterministic API CI**: Updated .github/workflows/dag-ci.yml with:
  - 'ruff check .' and 'ruff format --check .' for full project coverage.
  - Mandatory 'pip install -e ".[dev]"' in all jobs requiring the package.
  - Added 'Verify package import' step to fail fast on packaging issues.
  - Removed status gating in favor of standard 'needs:' dependency flow.

- Deleted root-level old files (main.py, api.py, utils.py, worker.py, entry.py, pytest.ini) after migration.
- Added Import Manifest Compiler (IMC) to enforce import legality, build ordering, runtime DAG correctness, CI reproducibility, and cross-language resolution.
- Removed skills folder from git tracking, kept locally.
- Implemented production‑grade IMC architecture: content‑addressed incremental DAG, cache layer, engine, and distributed sync modules.
- Migrated code to src/ layout for deterministic imports and CI consistency.
- Applied migration fixes from migration guide:
  * Consolidated main.py and api.py into app/main.py
  * Moved root-level utils.py, worker.py, entry.py to appropriate directories
  * Updated pyproject.toml with consolidated configuration
  * Removed pytest.ini (config moved to pyproject.toml)
- Fixed dependency drift detector script to validate pyproject.toml vs requirements.lock sync
- Resolved all MD041 markdown violations by adding top-level headings to files missing them
- Fixed import issues by creating missing DAG modules (adaptive_scheduler.py, autoscaler.py, etc.)
- Fixed bootstrapping validation by adding environment variable requirements to tests
- Verified local build and test success with pip install -e ".[dev]" and pytest



\- Deleted root-level old files (main.py, api.py, utils.py, worker.py, entry.py, pytest.ini) after migration.

\- Removed READ ME\_DO NOT PUSH folder from git tracking (kept locally).



\---



\## v23.0.0: API Consolidation \& Performance Hardening (April 2026)



\### Problem

Fragmented entrypoints (`main.py` vs `api.py`) led to logic drift. Startup side-effects at module scope caused issues in tests and CI. Blocking HTTP calls and non-atomic Redis operations impacted performance and reliability.



\### Solution

Consolidated the backend into a clean, modular structure with hardened async patterns.



\### Changes Applied



\*\*1. `app/main.py`\*\* â€” Unified Entrypoint:

\- Merged `main.py` and `api.py`.

\- Moved `run\_boot\_dag()` and route initialization inside the `lifespan` context manager.

\- Updated `call\_mercury\_ai()` to be fully async using a shared `httpx.AsyncClient`.

\- Hardened `enforce\_rate\_limit()` using atomic `SET NX` + `INCR`.

\- Improved `set\_job()` reliability by removing redundant pipeline deletes.



\*\*2. `app/utils.py`\*\* â€” Resilient Usage Tracking:

\- Implemented lazy settings loading to prevent import-time crashes.

\- Added re-queuing of failed usage batches to prevent data loss.



\*\*3. Directory Cleanup \& Packaging\*\*:

\- Removed all deprecated root-level files (`main.py`, `api.py`, `utils.py`, `worker.py`, `entry.py`, `pytest.ini`).

\- Standardized on `app/` and `worker/` packages.

\- Removed `sys.path` hacks in favor of `pip install -e .`.



\*\*4. Dependency \& Config Modernization\*\*:

\- Migrated to Pydantic v2 `@field\_validator`.

\- Unified `pytest` configuration within `pyproject.toml`.



\---



\## v22.0.0: Deterministic API CI \& Boot Hardening (April 2026)



\### Problem

CI pipeline was inconsistent and prone to false greens. Startup sequence had hidden execution order dependencies.



\### Solution

Implemented a deterministic boot pipeline and hardened the API CI workflow.



\### New Components



\*\*1. `app/core/boot/engine.py`\*\* — Deterministic Boot Engine:

\- Idempotent startup sequence.

\- Validates environment, normalizes secrets, and builds configuration singleton.

\- Prevents double-initialization in tests.



\*\*2. `.github/workflows/dag-ci.yml`\*\* — Deterministic API CI:

\- Hard-locked linting and test stages.

\- Explicit needs-based dependency tree.

\- Dependency drift check included in API CI.

\- Validates Boot System and DAG Orchestrator integrity.



\*\*3. `tools/check\_dependency\_drift.py`\*\* — Environment Validator:

\- Ensures the runtime can boot and import core modules without side-effect crashes.



\---



\## v21.0.0: Execution Trace System (April 2026)



\### Problem

No observability into DAG execution - can't debug failures or profile performance.



\### Solution

Added execution trace layer - immutable record of every node execution.



\### New Components



\*\*1. `app/runtime/trace.py`\*\* — Trace model:

```python

@dataclass

class TraceEvent:

&#x20;   trace\_id: str

&#x20;   node: str

&#x20;   inputs: Dict\[str, Any]

&#x20;   outputs: Dict\[str, Any]

&#x20;   start\_ms: float

&#x20;   end\_ms: float

&#x20;   duration\_ms: float

&#x20;   status: str  # success, failed

&#x20;   error: str

```



\*\*2. Updated `app/runtime/executor.py`\*\* — Records trace events:

```python

self.trace.record(TraceEvent(

&#x20;   node=name,

&#x20;   inputs=inputs,

&#x20;   outputs=output,

&#x20;   duration\_ms=...,

&#x20;   status=status,

))

```



\*\*3. Updated API contract\*\* — Returns trace in response:

```python

class RunResponse(BaseModel):

&#x20;   ...

&#x20;   trace: List\[Dict\[str, Any]]  # NEW

```



\### What This Enables

\- \*\*Debugging:\*\* which node failed, what inputs caused it

\- \*\*Performance profiling:\*\* bottleneck detection per node

\- \*\*Replay system:\*\* rerun failed nodes (next step)

\- \*\*Future UI:\*\* trace data for visualization



\### Execution Flow

```

Compiled DAG → Execution Plan → Executor → Trace Events → API Response

```



\---



\## v4.1.0: Strict Dependency Contract (April 2026)

\### Infrastructure Baseline

Eliminated the configuration drift between CI definitions and app limits out in production runtimes.

\- Added explicit segregation between `requirements.txt` (App) and `requirements-dev.txt` (pytest, asyncio, ruff, mypy).

\- Engineered the `tools/ci\_gates/runtime\_contract.py` validation layer to formally check deployment configuration definitions upfront before executing unit test harnesses or app logic validations.



\---



\## v4.0.0: Declarative CI DAG Shift (April 2026)



\### Radical Deprecation

Removed the massive custom Python-based CI orchestration systems:

\- Deleted all scripts inside `ci/` except `workflow.yml` and a tiny runner file.

\- Deprecated imperative Python orchestration. Removed all recursive loop logic that acted as a secondary application runtime.



\### New Architecture

The Action CI is now a pure YAML DAG executor mapping simple abstract terminal tasks.

\- `ci/workflow.yml` as the declarative graph state.

\- Single unified shell-executed `ci/runner.py` wrapper resolving execution barriers.

\- Integrated `tools/ci\_gates/` paths restricting and blocking system pollution.



\---



\## v3.5.1: CI-Ready Enforcement Bundle (April 2026)



\### Hard-Locked Execution Pipelines

Injected the gamma-grade enforcement bundle containing strict checks preventing state drift:



| Component | Responsibility |

|-----------|----------------|

| `.github/workflows/ci.yml` | Strict pipeline. Tests dependencies, enforces boundaries, triggers isolated PyTest layers. |

| `pytest.ini` | Root-level module referencing enforced with standardized outputs. |

| `tools/import\_guard.py` | Strict abstract-syntax-tree boundary checker preventing upward CI / local leak violations. |

| `app/api/kernel.py` | Isolated runtime enforcement node to restrict path execution paths via rigorous argparse `--mode` validation. |

| `app/runtime/dag.py` | Execution manifest structure mapping bootstrapping sequences directly to `app/core/telemetry`. |

| `docker/images/Dockerfile.base` | Augmented with `$PYTHONPATH` targeting and mapped testing libraries. |



This secures deterministic operations uniformly across Docker + Action contexts.



\---



\## v3.5.1: Controlled Intelligence CI Layer (April 2026)



\### Learning CI System Addition

Added a structured observation loop to the Gamma CI pipeline: \*\*observe → learn → predict → assist\*\*.



| Component | Function |

|-----------|----------|

| `ci/learning/failure\_store.py` | Minimal, persistent storage mapping error fingerprints to fix resolutions. |

| `ci/learning/fingerprint.py` | Normalizes paths and numerical IDs from stack traces to isolate bounded error signatures. |

| `ci/learning/fix\_registry.py` | Constrained whitelist of executable fixes mapped to recognized failures (e.g., F841 warnings). |

| `ci/learning/predictor.py`| Engine matching error traces against the fix registry before attempting repair. |

| `ci/learning/executor.py` | Safe subprocess executor handling bounded auto-corrections. |



\### Upgraded Kernel Integration

\- Upgraded `ci/kernel.py` to route all execution through `run\_with\_learning()`.

\- Bounded Self-Healing Constraints ENFORCED: Max 1 attempt per module, whitelisted commands only, and strict records preserved without wild mutation.

\- Successfully expanded bounded auto-fix from hardcoded ruff calls to predicted rule sets mapped back to DAG module testing loops.



\---



\## v3.5.1: PYTHONPATH Module Context Fix (April 2026)



\### Problem

`ModuleNotFoundError: No module named 'ci'` — Python executing script path instead of module context.



\### Root Cause

Running `python ci/kernel.py` treats it as a script, not a package, so `ci.\*` imports fail.



\### Fix Applied



\*\*1. CI Workflow\*\* — Changed to `-m` module execution:

```yaml

\# Before

python ci/kernel.py --module ${{ matrix.module }}

python ci/dag\_compiler.py > dag.json



\# After

python -m ci.kernel --module ${{ matrix.module }}

python -m ci.dag\_compiler > dag.json

```



\*\*2. Guard Rails\*\* — Added runtime enforcement in CI modules:

```python

if \_\_name\_\_ == "\_\_main\_\_":

&#x20;   if \_\_package\_\_ is None:

&#x20;       raise RuntimeError("Must run as module: python -m ci.kernel")

```



\### Rule Enforced

"No file-path execution of internal modules" — all internal modules must run via `-m`.



\---



\## v20.0.0: Compiled DAG Execution Model (April 2026)



\### Problem

Runtime DAG construction creates ambiguity and non-determinism at execution time.



\### Solution

Separated DAG definition from execution plan — compile at request time, execute from immutable plan.



\### New Components



\*\*1. `app/runtime/plan.py`\*\* — Execution plan model:

```python

@dataclass

class ExecutionPlan:

&#x20;   order: List\[str]           # fixed execution order

&#x20;   dependencies: Dict\[...]    # fixed dependency map

&#x20;   payloads: Dict\[...]       # node definitions

```



\*\*2. `app/runtime/compiler.py`\*\* — DAG compiler:

```python

def compile\_dag(dag) -> ExecutionPlan:

&#x20;   # validate → topological sort → serialize → return plan

```



\*\*3. `app/runtime/executor.py`\*\* — Plan-based executor:

```python

class Executor:

&#x20;   def run(dispatch, context):

&#x20;       # execute in fixed plan.order, no runtime decisions

```



\*\*4. Updated `app/api/kernel.py`\*\* — Compile then execute:

```python

dag = build\_dag\_from\_request(req.dag)

plan = compile\_dag(dag)

executor = Executor(plan)

results = executor.run(dispatch, context=req.context)

```



\### Benefits

\- \*\*Determinism:\*\* same input → same execution plan → same output

\- \*\*CI simplification:\*\* validates plan, not runtime behavior

\- \*\*Security:\*\* no runtime DAG mutation risk

\- \*\*Scalability:\*\* workers execute plan segments independently (future)



\### Execution Flow

```

Frontend → API → DAG Compiler → Execution Plan → Executor → Workers

```



\---



\## v19.0.0: Frontend ↔ Backend Contract Layer (April 2026)



\### Problem

Split repo needs strict boundary to prevent coupling reintroduction.



\### Solution

Created API contract layer as ONLY interface between frontend and backend.



\### New Components



\*\*1. `app/api/contract.py`\*\* — Strict schema boundary:

```python

class RunRequest(BaseModel):

&#x20;   dag: Dict\[str, DAGNodeSchema]

&#x20;   context: Dict\[str, Any]

&#x20;   mode: str  # local, subprocess, remote



class RunResponse(BaseModel):

&#x20;   results: Dict\[str, Any]

&#x20;   execution\_time\_ms: float

&#x20;   status: str

&#x20;   version: str

```



\*\*2. `app/api/kernel.py`\*\* — FastAPI entry point:

```python

@app.post("/run", response\_model=RunResponse)

def run(req: RunRequest):

&#x20;   # Validate → Build DAG → Execute → Return results

```



\### Contract Rules

\- \*\*Frontend ONLY:\*\* sends DAG definitions, receives results

\- \*\*Frontend NEVER:\*\* imports backend logic, knows worker model

\- \*\*Validation:\*\* DAG size limit (1000), context size limit (10000)

\- \*\*Error isolation:\*\* No internal stack traces exposed



\### Versioning

```python

API\_VERSION = "v1"

```



\### Architecture After Contract

```

Public repo:

&#x20; frontend + API client only



Private repo:

&#x20; DAG + scheduler + workers + Redis + CI



Bridge:

&#x20; strict FastAPI contract (v1)

```



\---



\## v18.0.0: Repository Security Hardening — Leak Prevention (April 2026)



\### Problem

Full backend execution system (DAG, workers, Redis, CI) exposed in public GitHub repo — IP + attack surface risk.



\### Solution

Hardened `.gitignore` + `.gitattributes` to prevent backend leakage.



\### Changes



\*\*1. `.gitignore` — Core system blocked:\*\*

```

app/

worker/

autoscaler/

ci/

tools/

infra/

docker/

scripts/

runtime/

packages/

requirements\*.txt

pyproject.toml

```



\*\*2. `.gitattributes` — Export-ignore rules:\*\*

```

app/\*\* export-ignore

worker/\*\* export-ignore

ci/\*\* export-ignore

tools/\*\* export-ignore

runtime/\*\* export-ignore

```



\### Architecture After Hardening



\*\*PUBLIC (safe surface):\*\*

```

frontend/

docs/

README.md

vercel.json

```



\*\*PROTECTED (in git but blocked from export):\*\*

```

app/          — execution core

worker/       — distributed workers

ci/           — bootstrapping

tools/        — dependency system

runtime/      — DAG + scheduler

infra/        — deployment contracts

```



\### Recommended Next Step

Split into dual-repo:

\- \*\*PUBLIC\*\*: frontend only

\- \*\*PRIVATE\*\*: full backend system



\---



\## v17.0.0: Redis Queue + Multi-Process Workers (April 2026)



\### New Components



\*\*1. `app/runtime/queue.py`\*\* — Redis-backed queue:

```python

class TaskQueue:

&#x20;   def \_\_init\_\_(self, url="redis://localhost:6379/0")

&#x20;   def push(task), def pop() -> Optional\[dict]

```



\*\*2. `app/runtime/state.py`\*\* — Redis result store:

```python

class ResultStore:

&#x20;   def set(name, value), def get(name), def exists(name)

```



\*\*3. `worker/worker.py`\*\* — Independent worker process:

```python

def worker\_loop(dag, context, queue\_url):

&#x20;   # pulls from Redis queue

&#x20;   # checks deps in Redis store

&#x20;   # executes via dispatch

&#x20;   # stores results in Redis

&#x20;   # enqueues dependents

```



\### System Flow

```

DAG → Redis queue → multiple worker processes → shared result store → dispatch → execution

```



\### How to Run



\*\*Start Redis:\*\*

```bash

docker run -p 6379:6379 redis

```



\*\*Seed DAG (from kernel):\*\*

```python

queue = TaskQueue()

for name, node in dag.nodes.items():

&#x20;   if not node.deps:

&#x20;       queue.push({"name": name})

```



\*\*Start workers (multiple terminals):\*\*

```bash

python -m worker.worker

python -m worker.worker

python -m worker.worker

```



\### Guarantees

\- \*\*Horizontal scaling\*\*: add workers → more throughput

\- \*\*Fault tolerance\*\*: worker dies → task stays in queue

\- \*\*Isolation\*\*: each worker is independent process



\### Gemma Bridge

Replace dispatch with remote GPU/model endpoint without changing DAG/scheduler.



\---



\## v16.0.0: Multi-Worker Parallel Scheduler (April 2026)



\### New Components



\*\*1. `app/runtime/queue.py`\*\* — Thread-safe queue (using stdlib Queue):

```python

class TaskQueue:

&#x20;   def push(task), def pop(), def task\_done(), def join()

```



\*\*2. `app/runtime/scheduler.py`\*\* — Multi-worker execution:

```python

class Scheduler:

&#x20;   def run(dispatch, context, workers=4):

&#x20;       # spawns N worker threads

&#x20;       # each pulls from queue, executes, pushes dependents

&#x20;       # thread-safe with minimal locking

```



\### Thread Safety

\- Lock protects: checking readiness, reading/writing results

\- Not locked: dispatch execution (no contention bottleneck)

\- Duplicate scheduling safe (results check prevents double execution)



\### Guarantees

\- DAG integrity under concurrency

\- Deterministic results (same inputs → same outputs)

\- Dependency safety: node only runs when deps satisfied



\### Validation

```bash

python -m app.api.kernel --mode=test

\# Runs with workers=1 then workers=4, both must match

```



\### What This Unlocks

\- Parallel deterministic execution

\- Ready for: external queue (Redis), multi-process workers, horizontal scaling



\---



\## v15.1.0: Dependency Scanner False Positive Fix (April 2026)



\### Problem

Dependency scanner treating stdlib + local modules as external dependencies, causing false positive failures.



\### Root Cause

Scanner not filtering:

\- stdlib modules

\- local project modules (app, worker, tests, etc.)



\### Fix

Updated `tools/ci\_gates/dependency\_scan.py` to:

1\. Extended STDLIB set (argparse, logging, threading, etc.)

2\. Dynamically detect local modules from project root

3\. Filter: stdlib → local modules → only enforce external



\### Before (broken)

```

app, logging, threading, tests ❌

```



\### After (correct)

```

numpy, openai, runpod ✓

```



\---



\## v15.0.0: Dispatch Layer + Queue-Aware Scheduler (April 2026)



\### New Components



\*\*1. `app/runtime/dispatch.py`\*\* — Single control point for execution:

```python

def dispatch(node, inputs, context):

&#x20;   mode = context.get("mode", "local")

&#x20;   if mode == "local":

&#x20;       return node.fn(inputs, context)

&#x20;   elif mode == "subprocess":

&#x20;       return run\_subprocess(node.name, inputs, context)

```



\*\*2. `app/runtime/queue.py`\*\* — Simple in-memory queue:

```python

class TaskQueue:

&#x20;   def push(task), def pop() -> Optional\[Any], def empty()

```



\*\*3. `app/runtime/scheduler.py`\*\* — Extended with queue-driven execution:

```python

class Scheduler:

&#x20;   def seed()   # enqueue root nodes

&#x20;   def ready()  # check dependencies satisfied

&#x20;   def run()    # queue-driven execution loop

```



\*\*4. `worker/entry.py`\*\* — Worker subprocess entry point



\### System Flow

```

DAG → Queue → Dispatch → Execution Backend

```



\### Guarantees

\- \*\*Backpressure\*\*: natural queue-based flow control

\- \*\*Decoupled execution\*\*: worker can run separately

\- \*\*Pull model\*\*: foundation for autoscaling/distributed systems

\- \*\*Isolation\*\*: subprocess mode = crash-safe boundary



\### Validation

```bash

python -m app.api.kernel --mode=test

\# Expected: task\_a: {value: 1}, task\_b: {value: 2}

```



\### Gemma-Ready

Execution abstraction now supports:

\- local execution

\- subprocess isolation

\- Ready for: remote worker, container, GPU node, Gemma inference routing



\---



\## v14.0.0: DAG Execution Foundation (April 2026)



\### Target Architecture

```

app/

&#x20; runtime/

&#x20;   dag.py       # Node + DAG definition

&#x20;   scheduler.py # topological sort

&#x20;   executor.py  # core runtime engine



worker/

&#x20; tasks.py      # pure function tasks

```



\### New Components



\*\*1. `app/runtime/dag.py`\*\* — DAG definition:

```python

class Node:

&#x20;   def \_\_init\_\_(self, name: str, fn: Callable, deps: List\[str] = None)



class DAG:

&#x20;   def add(name, fn, deps) -> DAG

&#x20;   def validate() -> None

```



\*\*2. `app/runtime/scheduler.py`\*\* — Topological execution order:

```python

def topological\_sort(nodes) -> List\[str]

```



\*\*3. `app/runtime/executor.py`\*\* — Core runtime engine:

```python

class Executor:

&#x20;   def run(context) -> Dict\[str, Any]

```



\*\*4. `worker/tasks.py`\*\* — Pure function tasks:

```python

def task\_a(inputs, context) -> Dict\[str, Any]

def task\_b(inputs, context) -> Dict\[str, Any]

```



\*\*5. Updated `app/api/kernel.py`\*\* — Added `--mode=test`:

```bash

python -m app.api.kernel --mode=test

```



\### System Guarantees

\- \*\*Determinism\*\*: execution order fixed by DAG, no hidden dependencies

\- \*\*Isolation\*\*: workers are pure functions, no cross-layer leakage

\- \*\*Composability\*\*: nodes can be rearranged safely



\### Gemma-Ready

Execution abstraction point ready for dispatch layer:

```python

self.results\[name] = dispatch(node, inputs, context)  # local/remote/GPU

```



\### Validation

```bash

python -m app.api.kernel --mode=test

\# Expected: task\_a: {value: 1}, task\_b: {value: 2}

```



\---



\## v13.1.0: Final Stabilization Pass (April 2026)



\### Consolidation

Removed redundant CI files:

\- `ci/runner.py` ❌ (replaced by bootstrap)

\- `ci/workflow.yml` ❌ (replaced by bootstrap)



\### Final Execution Contract

\*\*Single entrypoint everywhere:\*\*

```bash

python tools/bootstrap.py ci

```

Used in CI, Docker, local validation — no exceptions.



\### Bootstrap Pipeline (Final Order - DO NOT CHANGE)

```

1\. compile\_deps.py       # generate requirements

2\. fingerprint.py        # create environment fingerprint

3\. dependency\_scan.py   # verify contract

4\. import\_guard.py      # structural integrity

5\. dag\_compiler.py      # DAG validation

6\. app.api.kernel --dry-run  # runtime contract

7\. worker\_isolation.py  # worker safety

8\. pytest               # tests

```



\### Dependency Freeze

\- `requirements.lock.txt` is authoritative

\- NEVER manually edit

\- ONLY regenerate via `python tools/deps/compile\_deps.py`



\### CI File (Final Form)

```yaml

\- name: Run System

&#x20; run: python tools/bootstrap.py ci

```



\### System State

```

Code

&#x20;↓

Dependency Compiler

&#x20;↓

Locked Environment

&#x20;↓

Fingerprint Verification

&#x20;↓

CI Gate (structure)

&#x20;↓

Runtime Contract

&#x20;↓

Tests

```



\### What Not To Do Next

\- Add more CI layers

\- Add more validation scripts

\- Reorganize directories

\- Reintroduce ci/\* logic



\### Rule Going Forward

\*\*"Freeze infra, build capability"\*\* — Focus on runtime execution, not infrastructure.



\---



\## v13.0.0: Reproducible Build System with Fingerprint Parity (April 2026)



\### Problem

Dependency drift between CI, Docker, and worker environments causing "works in CI but not in worker" failures.



\### Solution

Added environment fingerprint system for cryptographic parity across all execution layers.



\### New Components



\*\*1. `tools/deps/fingerprint.py`\*\*:

\- Generates SHA256 fingerprint of requirements.lock.txt + requirements.txt

\- Creates build.fingerprint artifact



\*\*2. `tools/deps/verify\_fingerprint.py`\*\*:

\- Validates fingerprint matches across builds

\- Ensures CI == Docker == Worker parity



\*\*3. `tools/deps/compile\_deps.py`\*\*:

\- Scans codebase imports

\- Generates requirements.txt and requirements.lock.txt

\- Authoritative dependency artifact



\### Bootstrap Pipeline (Final Form)

```python

run("python tools/deps/compile\_deps.py")  # generate deps

run("python tools/deps/fingerprint.py")  # create fingerprint

run("python tools/ci\_gates/dependency\_scan.py")  # verify contract

run("python tools/ci\_gates/import\_guard.py")

run("python tools/ci\_gates/dag\_compiler.py")

run(f"python -m app.api.kernel --mode={mode} --dry-run")

run("python tools/ci\_gates/worker\_isolation.py")

if mode == "ci":

&#x20;   run("python -m pytest tests/ --tb=short -q")

```



\### What This Solves Permanently

\- Missing module errors (redis, dotenv)

\- Version drift between CI/Docker/worker

\- Environment mismatch bugs

\- "it works locally" failures



\### Gemma-Ready Foundation

Any node = identical execution environment — required for distributed inference.



\---



\## v12.3.0: Dependency Scanner + Requirements Sync (April 2026)



\### Problem

Missing runtime dependencies (redis, dotenv) discovered too late at runtime instead of at CI preflight.



\### Solution

Added dependency preflight gate + synced requirements.txt with pyproject.toml.



\### Changes



\*\*1. Added `tools/ci\_gates/dependency\_scan.py`\*\*:

\- Scans all Python imports in codebase

\- Compares against requirements.txt

\- Fails CI BEFORE runtime executes if deps missing

\- Stdlib excluded automatically



\*\*2. Synced `requirements.txt`\*\* with `pyproject.toml`:

\- Added all runtime dependencies from pyproject.toml dependencies list



\*\*3. Updated bootstrap\*\* to run dependency\_scan FIRST:

```python

run("python tools/ci\_gates/dependency\_scan.py")

```



\*\*4. Updated `ci/workflow.yml`\*\* with dependency\_scan step



\### System Flow Now

```

1\. Dependency scan (NEW - fails fast)

2\. Import guard

3\. DAG compiler

4\. Runtime contract

5\. Worker isolation

6\. Tests

```



\### What This Fixes Permanently

\- Missing dependency errors discovered at compile-time, not runtime

\- No more redis/dotenv-style runtime crashes

\- CI fails before any execution if contract broken



\---



\## v12.2.0: Runtime Dependency Contract Fix (April 2026)



\### Problem

`ModuleNotFoundError: No module named 'dotenv'` — runtime dependency missing from requirements.txt.



\### Root Cause

`python-dotenv` is used in `app/main.py` and `app/api.py` but was missing from `requirements.txt` (despite being in pyproject.toml).



\### Fix Applied

Added `python-dotenv` to `requirements.txt`:

```txt

python-dotenv

```



\### System Insight

This is a new failure class: \*\*"implicit runtime dependency leakage"\*\* — code imports external libs but dependency contract doesn't declare them.



\### Hardening Rule

All runtime dependencies must be declared in `requirements.txt`. CI should verify this.



\---



\## v12.1.0: Golden CI Bootstrap (Single Source of Truth) (April 2026)



\### Problem

CI logic spread across multiple files, multi-entrypoint drift, hidden execution paths.



\### Solution

Collapsed all enforcement into single bootstrap gate: `tools/bootstrap.py`



\### New Components



\*\*`tools/bootstrap.py`\*\* — Single deterministic gate:

```python

def main(mode: str = "ci"):

&#x20;   # 1. Structural integrity

&#x20;   run("python tools/ci\_gates/import\_guard.py")

&#x20;   run("python tools/ci\_gates/dag\_compiler.py")

&#x20;   # 2. Runtime contract validation

&#x20;   run(f"python -m app.api.kernel --mode={mode} --dry-run")

&#x20;   # 3. Worker isolation safety

&#x20;   run("python tools/ci\_gates/worker\_isolation.py")

&#x20;   # 4. Tests only after structure validated

&#x20;   if mode == "ci":

&#x20;       run("python -m pytest tests/ --tb=short -q")

```



\*\*`.github/workflows/ci.yml`\*\* — Simplified to single entrypoint:

```yaml

\- name: Run Bootstrap Gate

&#x20; run: python tools/bootstrap.py ci

```



\### Execution Flow

```

GitHub CI

&#x20;  ↓

bootstrap.py

&#x20;  ↓

import guard → dag compiler → runtime contract → worker isolation → pytest

```



\### What This Fixes Permanently

\- CI vs runtime divergence

\- Import graph explosions

\- Accidental architecture rewrites

\- Partial enforcement failures

\- Inconsistent local vs CI behavior



\### Rule

\*\*"No file may reintroduce CI-side business logic or learning systems"\*\*



\---



\## v12.0.0: Production Baseline Contract (April 2026)



\### System Contract (Immutable Baseline)



Repository layout:

```

app/

&#x20; api/

&#x20;   kernel.py          # single entrypoint only



&#x20; runtime/

&#x20;   dag.py             # execution graph

&#x20;   executor.py        # node execution

&#x20;   scheduler.py       # ordering



&#x20; core/

&#x20;   telemetry.py       # events

&#x20;   config.py

&#x20;   health.py          # stability scoring (NEW)



worker/

&#x20; tasks/               # isolated execution units



tests/



tools/

&#x20; ci\_gates/            # enforcement only (no domain logic)



ci/

&#x20; runner.py           # DAG executor ONLY (no business logic)

&#x20; workflow.yml        # declarative CI definition

```



\### Hard Rules (Non-Negotiable)



\*\*Rule A — Dependency Direction\*\*

```

ci → app/api → app/runtime → app/core → worker

```

Forbidden: worker → app/core, runtime → ci, any → ci internals



\*\*Rule B — CI is NOT Python Architecture\*\*

CI = YAML DAG + shell execution only. No domain logic, learning systems, or policy engines.



\*\*Rule C — Single Runtime Entrypoint\*\*

```bash

python -m app.api.kernel

```



\*\*Rule D — No File-Path Execution\*\*

```bash

python app/api/kernel.py ❌

python ci/kernel.py ❌

```



\### CI System (Declarative)



`ci/workflow.yml`:

\- entry: validate

\- parallel gates: import\_guard, dag\_compile, runtime\_contract, worker\_isolation

\- test: pytest tests/

\- edges: validate → test



`ci/runner.py`: Minimal deterministic executor (rewritten per spec)



\### New Components

\- `app/core/health.py`: Module stability scoring for future Gemma routing



\### What Stops Now

\- No more folder reshuffling

\- No more architectural redesign cycles

\- No more subsystem reclassification

\- Focus: stabilization, observability, performance, scaling



\---



\## v11.5.0: Remove Legacy Module Enforcement Guards (April 2026)



\### Problem

`RuntimeError: Must run as module: python -m ci.dag\_compiler` — leftover guards in tools/ci\_gates and app/api.



\### Root Cause

Old architecture enforced `python -m` execution, but current system uses script-based execution:

\- `ci/runner.py` → `tools/ci\_gates/\*.py` (scripts, not packages)

\- `ci/workflow.yml` defines execution flow



\### Fix Applied

Removed `\_\_package\_\_` enforcement blocks from:

| File | Change |

|------|--------|

| `tools/ci\_gates/dag\_compiler.py` | Removed guard block |

| `app/api/kernel.py` | Removed guard block |



\### CI Rule Enforced

\*\*"No file may enforce its own execution mode"\*\* — only CI runner enforces execution flow, not individual scripts.



\### Final Execution Model

```bash

\# CI path

python ci/runner.py



\# direct validation

python tools/ci\_gates/dag\_compiler.py

```



\---



\## v11.4.0: Dev Dependencies Baked Into Docker Image (April 2026)



\### Problem

`ModuleNotFoundError: No module named pytest` — test dependencies not in container.



\### Root Cause

Docker image only installed runtime dependencies, not dev/CI dependencies (pytest, ruff, mypy).



\### Fix Applied

Added `\[dev]` extras to Dockerfile.base install:

```dockerfile

RUN uv pip install --system --no-cache -e ".\[dev]"

```



\### Additional Fix: Test Directory Path

Updated MODULE\_TARGETS in ci/kernel.py to point to `tests/` instead of `ci/`:

```python

MODULE\_TARGETS = {

&#x20;   "api": \["tests/"],

&#x20;   "worker": \["tests/"],

&#x20;   "ci": \["tests/"],

}

```

Tests are in `tests/`, not `ci/`.



\---



\## v11.3.0: PYTHONPATH Module Context Fix (April 2026)



\### Problem

`tini exec` failure due to `python` vs `python3` inconsistency across containers.



\### Fix Applied

Added `ln -sf /usr/bin/python3 /usr/bin/python` to base Docker images:



| File | Change |

|------|--------|

| `docker/images/Dockerfile.base` | Added symlink after python3 install |

| `docker/images/Dockerfile.unified` | Added symlink after python3 install |



\### Why This Works

\- Fixes `tini exec` failure immediately

\- Preserves all existing CI + supervisor configs

\- Keeps runtime deterministic across all workers/nodes

\- No downstream script edits required



\### Validation

```bash

docker run --rm <image> python --version

\# Expected: Python 3.x.x

```



\---



\## v11.1.0: Layered Architecture Reorganization (April 2026)



\### The Problem

`scripts/` folder was acting as CLI + CI + deployment + runtime control + infra adapters + hotfixes - multiple systems in one directory.



\### Target Structure

```

simhpc/

├── app/                # API (runtime)

├── worker/             # execution (runtime)

├── ci/                 # CI/DAG/intelligence (build-time)

├── infra/              # deployment + external systems (RunPod, Supabase)

├── scripts/            # thin CLI wrappers ONLY

├── docker/             # container definitions

```



\### What Was Moved



| File | Destination | Reason |

|------|-------------|--------|

| `restart\_pod.py` | `infra/runpod/` | RunPod control-plane integration |

| `restart\_runpod\_pod.py` | DELETED | Duplicate of restart\_pod.py |

| `deploy\_runpod.py` | `infra/runpod/` | RunPod deployment |

| `deploy\_to\_runpod.py` | DELETED | Duplicate of deploy\_runpod.py |

| `deploy\_unified.py` | `infra/deploy/` | Unified deployment |

| `deploy\_unified\_manual.py` | DELETED | Duplicate |

| `deploy\_worker.py` | `infra/deploy/` | Worker deployment |

| `sb-sync.sh` | `infra/supabase/` | Supabase sync |

| `detect\_changes.py` | `ci/` | CI logic (already existed) |

| `dependency\_drift\_detector.py` | `ci/` | CI logic (already existed) |

| `check\_docker\_context.py` | `ci/` | CI logic (already existed) |

| `guard\_files.sh` | `ci/policies/` | Policy node |

| `guard\_frontend.sh` | `ci/policies/` | Policy node |

| `supervisord.conf` | `docker/` | Container runtime config |

| `sync-pod.sh` | `scripts/dev/` | Local dev utility |

| `generate\_openapi\_types.sh` | `scripts/dev/` | Local dev utility |

| `deploy\_full.sh` | DELETED | Duplicate |

| `saas\_fix.sh` | DELETED | Duplicate |



\### Final scripts/ Structure

```

scripts/

├── simhpc.sh           # main CLI

├── deploy\_all.sh       # thin wrapper → infra/

├── build.sh            # local dev convenience

└── dev/

&#x20;   ├── sync-pod.sh

&#x20;   └── generate\_openapi\_types.sh

```



\### Key Rules Enforced

1\. \*\*scripts/ must NOT contain logic\*\* - thin wrappers only

2\. \*\*CI never calls scripts\*\* - calls `python ci/kernel.py` directly

3\. \*\*infra owns external systems\*\* - RunPod, Supabase, Docker registry

4\. \*\*no duplication tolerated\*\* - duplicates collapsed



\### Why This Fixes Current Problems

\- Deterministic CI (no circular dependencies)

\- Stable deployment pipeline

\- Clean evolution path to gamma

\- Single responsibility per layer



\---



\## v11.0.0: Gamma-Stable CI Stack (April 2026)



\### Architecture Lock

Single entrypoint, zero duplication. Everything is subordinate to this DAG:



```

.github/workflows/dag-ci.yml  → ONLY entrypoint

ci/kernel.py                  → orchestrator

ci/dag\_compiler.py            → builds execution graph

container (digest)            → executes jobs

build-manifest.json           → system state artifact

```



\### What Was Built



| File | Change |

|------|--------|

| `.github/workflows/dag-ci.yml` | Full replacement — Gamma-stable deterministic DAG pipeline. Removed deprecated `.install: true` from setup-buildx-action, now relying natively on `BUILDX\_BUILDER`. |

| `docker/images/Dockerfile.base` | Stable base image: CUDA 12.1, uv, tini+supervisord, port 8080 only. Fixed `uv` editable install context by shifting `COPY . .` order. |

| `docker/supervisord.conf` | Unified runtime: api + worker, all logs streamed to stdout/stderr |

| `ci/dag\_compiler.py` | Clean rewrite — incremental diff, first-push safe, structured JSON output |

| `ci/kernel.py` | Clean rewrite — single bounded self-healing retry (ruff fix only), no unsafe mutations |

| `ci/policy.py` | New — immutability policy node, fails build on `:latest`/`:stable` Docker tags |



\### Guarantees



\- \*\*Deterministic\*\*: SHA → digest → container. Never `latest`, never `stable`.

\- \*\*DAG-aware\*\*: Only affected modules execute. `noop` skips gracefully.

\- \*\*Self-healing (bounded)\*\*: One retry with `ruff --fix` only. No speculative edits. No LLM patching.

\- \*\*Container-native\*\*: Identical runtime in CI and RunPod.

\- \*\*Zero duplication\*\*: One workflow files → one kernel → one DAG compiler.



\### Ruff F841 Fixes

\- `app/core/runtime/boot.py`: Removed unused `settings =` assignment.

\- `tests/test\_boot\_failfast.py`: Removed redundant `original\_stages` assignments.



\---



\## v3.5.0: Boot DAG System \& Pipeline Hardening (April 2026)



\### Architectural Initialization (v3.4.0 - v3.5.0)

\- \*\*App Boot DAG System (v3.5.0)\*\*: Fully implemented a deterministic boot pipeline in `app/core/boot/`.

&#x20; - Stages: `env`, `validate`, `normalize`, `config`.

&#x20; - Unified DAG entrypoint in `app/core/runtime/dag.py` for API, Worker, and CI modes.

&#x20; - Eliminated import-time side effects by shifting initialization to an explicit `run\_boot\_dag()` call.

&#x20; - Updated `app/main.py` and `app/core/config.py` to use the new boot context.

\- \*\*Unified Entrypoint Consolidation (v3.5.0)\*\*: Merged `./api.py` with `./app/api/api.py` to create a single, feature-rich FastAPI entrypoint using the Boot DAG.

\- \*\*CI/CD Pipeline Hardening (v3.5.0)\*\*: Fixed `IMAGE\_REF` resolution in `ci-kernel.yml`.

&#x20; - Resolved "Context access might be invalid: IMAGE\_REF" warnings by shifting to shell-variable access in `run` blocks.

&#x20; - Added digest validation to ensure `IMAGE\_REF` is never empty.

&#x20; - Standardized digest-only pull and run strategy for GHCR artifacts.

\- \*\*App Boot DAG (v3.4.0)\*\*: Shifted module loading into a rigid runtime application DAG structure starting in `app/main.py`.

\- Evaluated side-effect boundaries and built `app/core/runtime/ci.py` and `app/core/runtime/boot.py` to enable declarative boot testing with `RUNTIME\_MODE=ci`.

\- \*\*Docker Alignments\*\*: Generated `docker-compose.yml` to mirror exact deployment requirements in `Dockerfile.api` vs `Dockerfile.worker` passing required specific secrets via strict environment variables structure in CI/CD pipeline.



\---



\# SimHPC Pipeline Hardening - GHCR Registry



\## Current Status



Transitioning from fragile Docker-based pipeline to hardened GHCR artifact registry.



\---



\## Target State



\### ✅ Implemented



\- Deterministic image naming: `ghcr.io/nexusbayarea/simhpc-worker` (lowercase, single namespace)

\- Explicit environment promotion model: dev → staging → prod

\- Safe GHCR auth with `packages: write` permission

\- Immutable build artifacts via SHA tagging

\- No `latest` tag overwrite

\- CI-safe tagging tied to commit SHA



\---



\## Action Items



\### 1. Docker Build Setup

\- \[ ] Update workflow to use docker/build-push-action@v5

\- \[ ] Configure cache-from/cache-to with GHA

\- \[ ] Tag with SHA + branch refs



\### 2. GHCR Permissions

\- \[ ] Ensure workflow has `packages: write`

\- \[ ] Add docker/login-action@v3



\### 3. Promotion Layer

\- \[ ] Implement digest-based promotion (pull → tag → push)

\- \[ ] Add digest inspection step



\### 4. Immutability Rules

\- \[ ] Never overwrite SHA tags

\- \[ ] Document digest pinning for deployments



\---



\## Recent Change



\*\*Error encountered\*\*: `denied: installation not allowed to Create organization package`



\*\*Root cause\*\*: Missing `packages: write` permission in workflow OR org policy blocking package creation.



\*\*Fix applied\*\*: Hardcoded image name to `ghcr.io/nexusbayarea/simhpc-worker` to match expected package namespace.



\# Progress Log



> \*\*Note\*\*: This file tracks high-level development milestones.

> For detailed changelog, see \[CHANGELOG.md](./CHANGELOG.md).



\## Documentation (v2.6.7)



Consolidated to 5-pillar structure:

\- \*\*README.md\*\* - High-level overview

\- \*\*CHANGELOG.md\*\* - Version history

\- \*\*PROGRESS.md\*\* - This file



Deleted: GEMINI.md, GUIDE.md, ALPHA\_PILOT\_GUIDE.md, COMPREHENSIVE\_AUDIT.md, ARCHITECTURE.md, DEPLOYMENT.md, MISSION\_CONTROL\_STRATEGY.md, ROADMAP.md, INFISICAL\_SECRETS\_TEMPLATE.md (internal AI guides)



\---



\## v2.6.8: Production Hardening Audit Fixes (April 2026)



\### Issues Fixed



\#### 1. Queue Contract (✅ Already Correct)

\- \*\*Status\*\*: FIXED - API enqueues full JSON, worker pulls full JSON via brpoplpush



\#### 2. Redis Data Structure (✅ Already Correct)  

\- \*\*Status\*\*: FIXED - Using JSON strings consistently



\#### 3. Double Execution Risk (⚠️ Partial)

\- \*\*Issue\*\*: Both local worker AND RunPod can execute same job

\- \*\*Fix\*\*: Added `RUNPOD\_ENABLED` flag in worker config



\#### 4. Idempotency at Execution Layer (✅ FIXED)

\- \*\*Fix\*\*: Added execution guard in worker - checks `job:{id}:executed` before run, sets in finally block



\#### 5. Locking (✅ Verified)

\- \*\*Status\*\*: Already using `nx=True, ex=TTL` - FIXED



\#### 6. Active Runs Counter Drift (✅ FIXED)

\- \*\*Fix\*\*: Decrement in finally block AND failure paths



\#### 7. DLQ Replay (✅ Already Implemented)

\- \*\*Status\*\*: `replay\_dlq\_job()` function exists



\#### 8. Supabase as Source of Truth (✅ Verified)



\#### 9. Polling Loop (✅ FIXED)

\- \*\*Fix\*\*: Added exponential backoff for Redis polling



\#### 10. Recovery Worker KEYS Scan (✅ FIXED)

\- \*\*Fix\*\*: Uses SCAN instead of KEYS + JSON string instead of hash



\---



\## v2.6.11: Canonical Job Schema (April 2026)



\### Single Source of Truth

Created strict schemas enforced everywhere:



\*\*`app/models/job.py`\*\* - Job schema

\- id, user\_id, status, progress, input\_params, result, error, retries

\- created\_at, updated\_at, completed\_at timestamps



\*\*`app/models/event.py`\*\* - JobEvent schema  

\- type, job\_id, user\_id, status, progress, result, error, timestamp



\*\*`app/core/job\_store.py`\*\* - Serialization helpers

\- serialize\_job(), deserialize\_job()

\- serialize\_event(), deserialize\_event()

\- job\_to\_dict() for Supabase



\### Enforcement

\- Worker uses canonical Job model for all mutations

\- Event emission uses JobEvent schema

\- Supabase upsert uses job\_to\_dict() format



\### Data Model Fix (v2.6.11.1)

\- \*\*ALL job storage now JSON via Pydantic\*\* (GET/SET) - strict shape

\- \*\*ALL events now JobEvent schema\*\* - no drift

\- Redis = ephemeral cache, Supabase = source of truth



\---



\## Current Status



\- \*\*v2.6.19\*\*: Docker Build Path Verification (all paths correct)

\- \*\*v2.6.18\*\*: Softened Worker Check (debug mode - no blocking)

\- \*\*v2.6.17\*\*: Start.sh Port Cleanup (8080/8000 only, no 8888)



\---



\## v2.6.19: Docker Build Path Verification (April 2026)



\### Verified Files Exist

All paths in Dockerfile.unified and Dockerfile.worker are correct:



| File in Dockerfile | Actual Location | Status |

|--------------------|-----------------|--------|

| `app/services/worker/requirements.txt` | ✅ `app/services/worker/requirements.txt` | OK |

| `app/services/worker/requirements-autoscaler.txt` | ✅ `app/services/worker/requirements-autoscaler.txt` | OK |

| `app/services/worker/start.sh` | ✅ `app/services/worker/start.sh` | OK |



\---



\## v2.6.20: Dockerfile Unified Audit Fixes (April 2026)



\### Issues Fixed



| Issue | Fix |

|-------|-----|

| `apt-get upgrade -y` | Removed (breaks reproducibility, bloats image) |

| CUDA version | Changed from 12.1.1 to 12.2.0 for A40 compatibility |

| Unnecessary packages | Removed: git, gcc, jq, redis-tools (saved \~200MB) |

| User UID | Changed from 1000 to 10001 (avoids RunPod conflicts) |

| Duplicate build notes | Removed duplicate section at end |

| Layer efficiency | Preserved multi-stage build pattern |



\### Files Updated

\- `Dockerfile.unified` → v2.6.20

\- `skills/docker/SKILL.md` → v2.6.7 (audit notes added)



\---



\## v2.6.21: Docker Audit Fixes (April 2026)



\### Issues Fixed



| Issue | Fix |

|-------|-----|

| No docker history SOP | Added to skills/docker/SKILL.md |

| Unified COPY path | Changed from `python3.10/dist-packages` to `/usr/local` |

| EXPOSE misuse | Removed 8888 (only worker needs 8080/8000) |

| start.sh fragile | Added `trap "kill 0" SIGINT SIGTERM EXIT` for clean shutdowns |

| .dockerignore | Already exists and comprehensive |



\### Files Updated

\- `app/services/worker/start.sh` → Added signal handling

\- `Dockerfile.unified` → v2.6.21 (COPY /usr/local, EXPOSE 8080/8000)

\- `skills/docker/SKILL.md` → v2.6.8 (docker history SOP, trap guidance)



\---



\## v2.6.21: Pipeline \& Job Execution Audit (April 2026)



\### Pipeline Verification Gates



| Issue | Fix |

|-------|-----|

| Docker push silent failures | Use `set -e` + exit on error |

| podReset fire-and-forget | Parse GraphQL response, check for errors |

| Tagging with `latest` | Use SHA tags (`${{ github.sha }}`) |

| RunPod cached image | Deploy exact SHA, not tag |



\### Job Execution Pipeline Audit



| Issue | Fix |

|-------|-----|

| Double execution (Redis + RunPod) | Add EXECUTION\_MODE env var |

| Full jobs in Redis (state drift) | Use status-only in Redis |

| Idempotency not propagated | Propagate idempotency\_key to all layers |

| Retry fork | Add attempt lock guard |

| Weak locking | UUID-based lock with ownership |

| Progress UI regression | Add monotonic guard |

| Recovery worker duplication | Check RunPod status before recovery |



\### Files Updated

\- `skills/deployment/SKILL.md` → v2.6.21 (full audit, SHA tags, job pipeline fixes)



\---



\## v2.7.0: Full System Audit (April 2026)



\### Audit Scope

Full codebase audit against v2.7 reference architecture.



\### Key Findings



| Issue | Severity | Count |

|-------|----------|-------|

| Redis dependency | 🔴 Critical | 157 references |

| Dual ports (8080/8000) | 🟠 High | 1 file |

| Raw bash backgrounding | 🟠 High | start.sh |

| No schema\_version in Job | 🟠 High | app/models/job.py |

| Scattered Dockerfiles | 🟡 Medium | 4 files |

| Redis pub/sub in WS | 🟡 Medium | 3 files |



\### v2.7 Reference Architecture Principles



1\. Supabase = Single Source of Truth (no Redis)

2\. No Redis anywhere

3\. One primary port (8080 only)

4\. Stateless API

5\. Worker = pull-based executor (Supabase polling)

6\. WebSockets = thin layer (in-memory, no Redis)

7\. Deployment = podReset only

8\. Process manager (tini/supervisord)



\### Files Created

\- `V2.7\_AUDIT.md` → Full system audit document



\### Migration Path



\*\*Phase 1:\*\* Remove Redis (Week 1)

\- Create Supabase job store

\- Update worker to poll Supabase

\- Remove Redis from API

\- WS use in-memory events



\*\*Phase 2:\*\* Schema v2 (Week 2)

\- Add schema\_version to Job model

\- Add migration layer



\*\*Phase 3:\*\* Docker Cleanup (Week 3)

\- Consolidate to /docker

\- Remove port 8000

\- Add tini



\*\*Phase 4:\*\* CI/CD Hardening (Week 4)

\- SHA tagging only

\- podReset verification

\- Size budget enforcement



\---



\## v2.6.22: Docker Folder Structure (April 2026)



\### Changes Made



| Change | File |

|--------|------|

| Created `/docker` folder | New structure |

| Created `/docker/images/` | Dockerfiles |

| Created `/docker/scripts/` | start.sh |

| Created `/docker/ci/` | Build scripts (empty) |

| Created `/docker/compose/` | Docker compose |

| Created `/docker/docs/` | Documentation |

| Removed port 8000 | Single port 8080 |

| Updated Dockerfile paths | `docker/images/` |

| Updated start.sh | Single API process |



\### Updated Files

\- `docker/images/Dockerfile.unified` - Path updates

\- `docker/scripts/start.sh` - Single port, single API

\- `.dockerignore` - Added docker/ exclusion

\- `skills/docker/SKILL.md` → v2.6.9 (new structure)

\- `skills/deployment/SKILL.md` → v2.6.22 (Docker paths)



\### Build Command (v2.7)



```bash

docker build -f docker/images/Dockerfile.unified -t simhpcworker/simhpc-unified:${{ github.sha }} .

```



\---



\## v2.7.0: Docker Folder Consolidation (April 2026)



\### Audit Results



| Location | Issue |

|----------|-------|

| Root `Dockerfile.unified` | Duplicate of `docker/images/` |

| Root `Dockerfile.worker` | Duplicate, older version |

| Root `Dockerfile.api` | Duplicate, different structure |

| Root `Dockerfile.autoscaler` | Duplicate |

| `app/services/worker/Dockerfile` | Worker-only build (legacy) |

| `legacy\_archive/runpod-worker\_deprecated/Dockerfile` | Deprecated, keep for reference |



\### Consolidation Actions



1\. \*\*Removed duplicates from root\*\*: Dockerfile.{unified,worker,api,autoscaler}

2\. \*\*Updated docker/images/Dockerfile.unified\*\*:

&#x20;  - Version → v2.7.0

&#x20;  - Port 8000 removed (single port 8080)

&#x20;  - Added build command comment

3\. \*\*Updated skills/docker/SKILL.md\*\* → v2.7.0



\### Final Structure



```

docker/

&#x20; images/

&#x20;   Dockerfile.unified     ← Primary (used by CI)

&#x20;   Dockerfile.worker      ← Standalone worker

&#x20;   Dockerfile.api         ← API only

&#x20;   Dockerfile.autoscaler  ← Autoscaler only

&#x20; scripts/

&#x20;   start.sh

```



\### Deprecated (kept for reference)

\- `legacy\_archive/runpod-worker\_deprecated/Dockerfile`

\- `app/services/worker/Dockerfile` (worker-only)



\---



\## v2.7.1: Docker Compose \& Dockerignore Consolidation (April 2026)



\### Audit Results



| File | Location | Action |

|------|----------|--------|

| docker-compose.yml | Root | Moved to docker/compose/ |

| .dockerignore | Root | Already correct |

| .dockerignore | app/services/robustness/ | Keep (legacy, different scope) |

| Dockerfile | app/services/worker/ | Keep (legacy, not in docker/) |



\### Changes Made



1\. \*\*Moved docker-compose.yml\*\* → `docker/compose/docker-compose.yml`

2\. \*\*Updated docker-compose.yml\*\*:

&#x20;  - Removed Redis service (Supabase is source of truth)

&#x20;  - Updated context: `../..` and dockerfile: `docker/images/Dockerfile.unified`

&#x20;  - Single port 8080 only



\### Final Structure (v2.7.1)



```

docker/

&#x20; images/

&#x20;   Dockerfile.unified    ← Primary (CI uses this)

&#x20;   Dockerfile.worker

&#x20;   Dockerfile.api

&#x20;   Dockerfile.autoscaler

&#x20; scripts/

&#x20;   start.sh

&#x20; compose/

&#x20;   docker-compose.yml    ← v2.7 updated (no Redis)

```



\---



\## v2.6.18: Softened Worker Check (April 2026)



\### Issue

\- `check\_compute\_availability()` was blocking job submissions when no workers registered

\- Causes "no\_active\_pods" errors during deployment transitions



\### Fix



\*\*app/api/api.py\*\* and \*\*app/main.py\*\*:

```python

async def check\_compute\_availability():

&#x20;   """Softened for deployment debugging - no longer blocks job submissions."""

&#x20;   workers = get\_active\_workers()

&#x20;   if not workers:

&#x20;       logger.warning("No active workers detected — continuing anyway (debug mode)")

&#x20;       return \[]

&#x20;   return workers

```



\### Files Modified



| File | Change |

|------|--------|

| `app/api/api.py` | Softened worker check |

| `app/main.py` | Softened worker check |



\---



\## v2.6.17: Start.sh Port Cleanup (April 2026)



\### Issue

\- start.sh still referenced port 8888 (Jupyter conflict)

\- Needed strict 8080/8000 dual-HTTPS configuration



\### Fix



\*\*app/services/worker/start.sh\*\*:

\- Removed all 8888 references

\- Clears only 8080 and 8000

\- Worker already configured to use 8080 (POD\_PORT defaults to 8080)



\### Files Modified



| File | Change |

|------|--------|

| `app/services/worker/start.sh` | Removed 8888 port references |



\---



\## v2.6.16: Deploy Workflow Dynamic RUNPOD\_ID (April 2026)



\### Root Cause

\- deploy.yml had \*\*hardcoded pod ID\*\* (`ikzejthq1q7yt9`)

\- Infisical syncs `RUNPOD\_ID` to GitHub secrets, but workflow ignored it

\- Result: workflow passes, but wrong pod (or non-existent) gets reset



\### Fix



\*\*.github/workflows/deploy.yml\*\*:

```yaml

\# Before (hardcoded - WRONG)

RUNPOD\_ID: ikzejthq1q7yt9



\# After (dynamic from secrets - CORRECT)

RUNPOD\_ID: ${{ secrets.RUNPOD\_ID }}

```



\### Files Modified



| File | Change |

|------|--------|

| `.github/workflows/deploy.yml` | Hardcoded pod ID → ${{ secrets.RUNPOD\_ID }} |



\---



\## v2.6.15: Dual-Port Architecture (April 2026)



\### Why No 8888

\- JupyterLab (JL) reserves port 8888

\- SimHPC now uses \*\*8080 (Primary)\*\* and \*\*8000 (Backup)\*\*



\### Changes



\*\*app/api/api.py\*\* - Default port from 8888 → 8080:

```python

port = int(os.getenv("PORT", "8080"))

```



\*\*app/services/worker/worker.py\*\* - Worker port from 8888 → 8080:

```python

POD\_PORT = os.getenv("WORKER\_PORT", "8080")

```



\*\*app/services/worker/start.sh\*\* - Already correct (8080/8000)



\### Architecture

\- \*\*8080\*\*: Primary API (main traffic)

\- \*\*8000\*\*: Backup API (failover)

\- Both run identical FastAPI instances in same container



\### Files Modified



| File | Change |

|------|--------|

| `app/api/api.py` | Default port 8888 → 8080 |

| `app/services/worker/worker.py` | Worker port 8888 → 8080 |



\---



\## v2.6.14: Dockerfile \& Start Script Path Fixes (April 2026)



\### Dockerfile.unified



Fixed COPY paths from deprecated `services/` to `app/`:

```dockerfile

\# Before (wrong)

COPY --chown=simuser:simuser services/api/api.py .

COPY --chown=simuser:simuser services/worker/worker.py .



\# After (correct)

COPY --chown=simuser:simuser app/ ./app/

```



\### start.sh



Fixed uvicorn module reference from `api:app` to `app.main:app`:

```bash

\# Before (wrong)

python3 -m uvicorn api:app --host 0.0.0.0 --port 8080



\# After (correct)

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080

```



\### Files Modified



| File | Change |

|------|--------|

| `Dockerfile.unified` | Fixed COPY paths to use `app/` directory |

| `app/services/worker/start.sh` | Fixed uvicorn module to `app.main:app` |



\---



\## v2.6.13: Schema Versioning with Migration Support (April 2026)



\### Strict Schema Validation at Redis Boundary



Created `app/core/validated\_job\_store.py` with `ValidatedJobStore` class:



\- \*\*set\_job(job)\*\* - Validates Job Pydantic schema BEFORE write to Redis

\- \*\*get\_job(job\_id)\*\* - Reads and validates job from Redis, quarantines corrupted data

\- \*\*update\_job(job\_id, \*\*updates)\*\* - Safe update with validation

\- \*\*delete\_job(job\_id)\*\* - Cleanup job and related keys



\### Enforcement in Worker



Patched `app/services/worker/worker.py` to use validated store:

\- Job deserialization uses `Job.model\_validate()` 

\- All writes use `job\_store.set\_job(job)` with fallback

\- Error handling updated to use `job.id`, `job.retries`, etc.



\### Files Created/Modified



| File | Change |

|------|--------|

| `app/core/validated\_job\_store.py` | NEW - schema validation layer |

| `app/services/worker/worker.py` | PATCHED - use validated job store |



\---



\## v2.6.13: Schema Versioning with Migration Support (April 2026)



\### Version Constant



Created `app/models/version.py`:

```python

CURRENT\_JOB\_SCHEMA\_VERSION = 1

```



\### Job Model Update



Added `schema\_version` field to `Job` model:

```python

class Job(BaseModel):

&#x20;   schema\_version: int = CURRENT\_JOB\_SCHEMA\_VERSION

&#x20;   ...

```



\### Migration Layer



Created `app/core/job\_migrations.py`:

\- `migrate\_job(data)` - central migration router

\- `migrate\_v0\_to\_v1()` - adds missing progress/retries fields

\- Throws `RuntimeError` if unsupported version after migration



\### ValidatedJobStore Updates



\- \*\*set\_job\*\*: Enforces `CURRENT\_JOB\_SCHEMA\_VERSION` on write

\- \*\*get\_job\*\*: Runs migration BEFORE Pydantic validation

\- \*\*update\_job\*\*: Ensures version doesn't downgrade



\### Backward Compatibility Test



```python

old\_job = {"id": "123", "user\_id": "u1", "status": "queued", ...}

migrated = migrate\_job(old\_job)  # Auto-upgraded to v1

```



\### Files Created/Modified



| File | Change |

|------|--------|

| `app/models/version.py` | NEW - version constant |

| `app/models/job.py` | PATCHED - added schema\_version field |

| `app/core/job\_migrations.py` | NEW - migration layer |

| `app/core/validated\_job\_store.py` | PATCHED - integrate migrations |



\---



\## v2.6.7: Dual-Port + Async Integrity + Authority Alignment (April 2026)



\### Dual-Port Strategy

\- \*\*Primary API:\*\* Port 8080 (main traffic, batch flush to Supabase)

\- \*\*Backup API:\*\* Port 8000 (redundancy if 8080 fails)

\- \*\*Jupyter:\*\* Port 8888 (development only)



\### Async Integrity (httpx.AsyncClient)

\- Replaced blocking `requests` with `httpx.AsyncClient` singleton in lifespan

\- Connection pooling: 20 keepalive, 100 max connections, 60s timeout

\- Non-blocking HTTP calls prevent event loop starvation



\### Authority Alignment

\- \*\*Supabase as single source of truth\*\* - removed Redis usage tracking

\- \*\*Batch Flush Pattern\*\* - buffers usage events, flushes every 10s to prevent write pressure

\- \*\*SQL RPC\*\* - `decrement\_usage\_atomic()` for atomic credit deduction (prevents race conditions)

\- \*\*Vercel Cron\*\* - `/api/v1/internal/force-flush` for guaranteed flush even on pod scale-down



\### Port Standardization

\- All 8000→8080/8000 for RunPod compatibility

\- start.sh: `fuser -k 8080/tcp 8000/tcp 8888/tcp || true` clears port conflicts



\### Pod ID

\- Current: `ikzejthq1q7yt9` (dynamic - get from Infisical)

\- Check: `infisical secrets get RUNPOD\_ID --plain`



\## v2.6.27: Authority Alignment (April 2026)



\### Fixes Applied



1\. \*\*Supabase Usage Authority\*\* - Eliminated the split Redis/Supabase usage tracking logic.

&#x20;  - Refactored `get\_user\_usage` to compute stats directly from the Supabase `simulations` table.

&#x20;  - Removed all `usage:{user\_id}` Redis key management to prevent data drift and race conditions.

2\. \*\*Simplified Increment Logic\*\* - Deprecated `increment\_user\_usage` as a no-op. Usage is now implicitly incremented by the atomic database insert of a new simulation record.

3\. \*\*Rolling Window Integrity\*\* - Verified that usage enforcement strictly follows the 7-day rolling window defined by actual database timestamps.



\---



\## v2.6.25: Distributed System Architecture + Port 8888 Standardization (April 2026)



\### SERVICE\_ROLE NOT NEEDED (Single-Pod Unified)

\*\*No SERVICE\_ROLE env var\*\* - Unified pod runs everything together:



\- Pod is "self-aware" - initializes API + Worker + Autoscaler simultaneously

\- No external role configuration needed

\- Lifespan handles startup sequence automatically



\*\*start.sh\*\* runs all 3 in same process:

```bash

uvicorn api:app --port 8888 \&   # API (HTTP)

python3 -u worker.py \&           # Worker (background)

python3 -u autoscaler.py \&       # Autoscaler (background)

wait

```



\## v2.6.26: Production Safety - Idempotency, Retry, DLQ (April 2026)



\### 1. Atomic Idempotency (Redis-first)

\- `SETNX` with TTL for duplicate prevention

\- Generates hash from user\_id + payload as idempotency key

\- Returns `{"status": "duplicate", "job\_id": "existing"}` on collision



\### 2. Controlled Retry System

\- Config: `MAX\_RETRIES=3`, `RETRY\_DELAY=5s`

\- Exponential backoff: `sleep(RETRY\_DELAY \* retries)`

\- After max retries → moves to DLQ



\### 3. Dead Letter Queue (DLQ)

\- Failed jobs after max retries → `simhpc\_dlq`

\- Admin endpoint to inspect + replay

\- `GET /admin/dlq`, `POST /admin/dlq/replay/{job\_id}`



\### 4. Processing Queue (Crash Recovery)

\- Uses `BRPOPLPUSH` to move job to `simhproc\_processing`

\- On success: remove from processing

\- On crash: job stays in processing, can be recovered



\### 5. No More "no\_active\_pods"

\- API always succeeds: enqueue job, autoscaler triggers

\- Queue-based: pod spins up AFTER job queued



\### Files Modified

| File | Change |

|------|--------|

| `job\_queue.py` | Idempotency key generation, DLQ functions, retry tracking |

| `worker.py` | BRPOPLPUSH, retry with backoff, DLQ move |



\### Queue Architecture

```

simhpc\_jobs        → active queue

simhpc\_processing   → in-flight (crash-safe)

simhpc\_dlq          → permanently failed

```



\---



\## v2.6.25: Distributed System + Events + WebSocket (April 2026)



\### 1. Event-Driven Architecture (Redis Pub/Sub)

\- \*\*Channel\*\*: `jobs:events`

\- \*\*Events emitted\*\*: `job\_queued`, `job\_started`, `job\_progress`, `job\_completed`, `job\_failed`



\### 2. Auth Passthrough (user\_id + tier)

\- Job queue now carries user context:

&#x20; ```python

&#x20; job\_input\["user\_id"] = user\_context.get("user\_id")

&#x20; job\_input\["tier"] = user\_context.get("tier", "free")

&#x20; ```

\- Tier-based routing ready (future: priority queues)



\### 3. WebSocket Real-time Updates

\- \*\*New endpoint\*\*: `/ws/jobs/{job\_id}` - per-job updates

\- \*\*New endpoint\*\*: `/ws/all` - all events (admin)

\- Frontend connects once, receives live progress/completion/failure



\### 4. Worker Event Emission

\- `publish\_event()` sends to Redis pub/sub

\- Progress updates stream to UI

\- Completion triggers autoscaler scale-down



\### 5. Event-Driven Autoscaler

\- Subscribes to `jobs:events` instead of polling

\- Reacts to `job\_queued` → `job\_completed` → `job\_failed`

\- Single-pod: logs status only (no scaling)



\### Files Modified

| File | Change |

|------|--------|

| `job\_queue.py` | Added `publish\_event()`, user context |

| `ws.py` (new) | WebSocket endpoints for real-time updates |

| `api.py` | Include ws\_router |

| `worker.py` | Event emission on job lifecycle |

| `autoscaler.py` | Event-driven instead of polling |



\### Architecture (Single-Pod)

```

Frontend → API → Redis Queue + Events → Worker

&#x20;                                   ↓

&#x20;                             WebSocket → Frontend

&#x20;                                   ↓

&#x20;                             Autoscaler (events)

```

All 8000 references converted to 8888:

\- `Dockerfile.worker` - EXPOSE 8888

\- `services/robustness-orchestrator/run\_with\_cors.py` - port 8888

\- `apps/frontend/src/sections/Hero.tsx` - Uses VITE\_API\_URL env



\### vLLM Persistence Paths Added

```dockerfile

ENV HF\_HOME=/workspace/huggingface

ENV VLLM\_CACHE=/workspace/vllm\_cache

```

Ensures model cache persists on pod resets.



\### Entrypoint Verified

\- `services/api/api.py` contains `app = FastAPI(...)`

\- start.sh runs `uvicorn api:app --port 8888`

\- No separate main.py needed



\### Ghost Files Warning

⚠️ These .md files are tracked (should be ignored):

\- `CHANGELOG.md`

\- `GEMINI.md`

\- `progress.md`



Run `git rm --cached \*.md` before deploy if needed.

All internal/external communication standardized on Port 8888:



| File | Change |

|------|--------|

| `services/worker/worker.py` | `POD\_PORT = "8888"` |

| `services/worker/run\_with\_cors.py` | `port=8888` |

| `run\_api.py` | `port=8888` |

| `Dockerfile.api` | `EXPOSE 8888`, `--bind 0.0.0.0:8888` |

| `services/api/Dockerfile` | `EXPOSE 8888`, `--bind 0.0.0.0:8888` |

| `.env.example` | `VITE\_API\_URL=http://localhost:8888` |

| `apps/frontend/src/lib/apiClient.ts` | `localhost:8888` |

| `apps/frontend/src/pages/admin/AdminAnalyticsPage.tsx` | `localhost:8888` |

| `scripts/simhpc.sh` | `lsof -i:8888`, `--port 8888` |



\### Phase 0: Fix Container

1\. \*\*Dockerfile.unified\*\* - Direct worker start, no Jupyter:

&#x20;  ```dockerfile

&#x20;  CMD \["python3", "-u", "worker.py"]

&#x20;  ```

&#x20;  - Removed `./start.sh` that was launching Jupyter

&#x20;  - Worker now starts immediately on pod boot



\### Phase 1: API = Control Plane Only

1\. \*\*Removed\*\*: Direct RunPod calls from API

2\. \*\*Removed\*\*: `no\_active\_pods` logic blocking submissions

3\. \*\*API Responsibility\*\*:

&#x20;  - Auth (Supabase JWT)

&#x20;  - Validate payload

&#x20;  - Enforce usage limits (free tier)

&#x20;  - Idempotency (create\_or\_get\_job)

&#x20;  - Enqueue to Redis

&#x20;  - Publish `autoscaler:tick` event



\### Phase 2: Worker = Execution Plane

1\. \*\*Job ownership\*\*:

&#x20;  ```python

&#x20;  WORKER\_ID = os.getenv("WORKER\_ID", os.uname().nodename)

&#x20;  job\["worker\_id"] = WORKER\_ID

&#x20;  job\["started\_at"] = int(time.time())

&#x20;  redis\_client.hset("jobs:active", job\_id, WORKER\_ID)

&#x20;  ```

2\. \*\*Telemetry events\*\*:

&#x20;  - `job\_started`

&#x20;  - `job\_progress`

&#x20;  - `job\_completed`



\### Phase 3: Redis = Event Bus (Channels)

```

events                → all system events

autoscaler:tick      → trigger scaling

jobs:updates         → job state changes

```



\### Phase 4: Autoscaler = Event-Driven (Not Polling)

```python

def autoscaler\_listener():

&#x20;   pubsub = redis\_client.pubsub()

&#x20;   pubsub.subscribe("autoscaler:tick")

&#x20;   for message in pubsub.listen():

&#x20;       autoscale()

```



\### Phase 5-8: Future (WebSockets, Smart Scheduling, Observability)



\---



\## v2.6.24: Atomic Idempotency \& O(1) Concurrency (April 2026)



\### Fixes Applied



1\. \*\*Atomic Idempotency\*\* - Refactored `reserve\_idempotency` to use Redis `SETNX`, ensuring that duplicate requests are blocked atomically at the point of entry.

2\. \*\*O(1) Concurrency Tracking\*\* - Replaced O(N) Redis `KEYS` scans with O(1) per-user counters (`user:{user\_id}:active\_runs`).

&#x20;  - Implemented `increment\_active\_runs` in the API (on enqueue).

&#x20;  - Implemented `decrement\_active\_runs` in the Worker (on job completion/failure).

3\. \*\*Registry-Aware Discovery\*\* - Integrated the Full Infra registry into the simulation creation flow, ensuring jobs are only accepted when healthy workers are heartbeating.



\---



\## v2.6.14: Frontend API \& GitHub Workflow Fix (April 2026)



\### Fixes Applied



1\. \*\*Duplicate API Declaration\*\* - Merged the second `api` object into the `ApiClient` class in `apps/frontend/src/lib/api.ts`.

&#x20;  - Unified `getUserProfile`, `subscribe`, `startRobustnessRun`, and other methods into the `api` instance.

&#x20;  - All methods now consistently use the internal `request` helper for error handling and toasts.



2\. \*\*GitHub Workflow Fix (v2.6.7)\*\* - Repaired the corrupted `deploy-runpod.yml` file.

&#x20;  - Replaced "Frankenstein" script (containing git diff markers and duplicate steps) with the clean v2.6.7 protocol.

&#x20;  - Implemented STAGE 1 (podReset) and Fallback Cycle (Stop -> Resume) for resilient deployments.



3\. \*\*Vercel Build Stability\*\* - Resolved the "symbol already declared" error in TypeScript build.



\---



\## v2.6.6: API-Only Deployment (April 2026)



\### Changes Applied



1\. \*\*All SSH steps removed\*\* - Replaced with podReset GraphQL mutation

&#x20;  - `deploy.yml` - Uses podReset

&#x20;  - `auto-deploy-runpod.yml` - Uses podReset

&#x20;  - `deploy-beta-runpod.yml` - Uses podReset

&#x20;  - `deploy-runpod.yml` - Uses podReset



2\. \*\*GraphQL fixes\*\* - Removed `status` field from mutations (API schema change)

&#x20;  - podReset returns `{ id }` only

&#x20;  - Status query uses `desiredStatus`



3\. \*\*Lean Secrets\*\* - Only CRITICAL vars:

&#x20;  - `RUNPOD\_API\_KEY` (CRITICAL)

&#x20;  - `RUNPOD\_ID` (CRITICAL)

&#x20;  - `DOCKER\_LOGIN` (CRITICAL)

&#x20;  - `DOCKER\_PW\_TOKEN` (CRITICAL)

&#x20;  - Delete: `RUNPOD\_SSH\_KEY`, `RUNPOD\_SSH`, `RUNPOD\_TCP\_PORT\_22`, `RUNPOD\_USERNAME`



\### PodReset vs PodRestart



| Action | Effect | Use Case |

|--------|--------|----------|

| `podRestart` | Reboots container, uses cached image | Quick debug |

| `podReset` | Wipes container, pulls fresh image | \*\*CI/CD deployments (REQUIRED)\*\* |



\---



\## v2.6.5: API-Only Deployment (April 2026)



\### Changes Applied



1\. \*\*GitHub Actions deploy.yml\*\* - Replaced `podStop` → `podResume` with atomic `podReset` GraphQL mutation

&#x20;  - Fixes "not enough free GPUs" error that occurred when trying to resume on same host

&#x20;  - Removed SSH deployment (no more `appleboy/ssh-action`)



2\. \*\*Enhanced api.ts\*\* - Added toast error handling with sonner integration

&#x20;  - Automatic error toasts for failed API calls

&#x20;  - Cleaner request/response handling



3\. \*\*Documentation Updated\*\*

&#x20;  - README.md: API-only deployment (no SSH)

&#x20;  - skills/deployment/SKILL.md: Removed SSH secrets, added podReset

&#x20;  - skills/runpod/SKILL.md: Removed SSH references, uses GraphQL API



\### Secrets (v2.6.5)



| Secret | Purpose |

|--------|---------|

| `DOCKER\_LOGIN` | Docker Hub username |

| `DOCKER\_PW\_TOKEN` | Docker Hub PAT |

| `RUNPOD\_API\_KEY` | RunPod GraphQL API key |

| `RUNPOD\_ID` | Pod identifier |



No SSH secrets needed - deployment is fully API-based.



\---



\## v2.6.13: AlphaControlRoom Fix (April 2026)



\### Fix Applied



1\. \*\*Simplified AlphaControlRoom.tsx\*\* - Removed broken imports

2\. \*\*Added route\*\* `/dashboard/alpha` → AlphaControlRoom

3\. \*\*Sidebar link\*\* now points to `/dashboard/alpha`



\---



\## v2.6.12: AlphaControlRoom Route (April 2026)



\### Fix Applied



1\. \*\*Added AlphaControlRoom import\*\* to App.tsx

2\. \*\*Added route\*\* `/dashboard/alpha` pointing to AlphaControlRoom

3\. \*\*Fixed sidebar link\*\* - Alpha Control now links to `/dashboard/alpha` (opens in new tab)



\---



\## v2.6.11: Manifest Cleanup (April 2026)



\### Fix Applied



1\. \*\*Simplified Manifest\*\* - Removed broken icon references from `site.webmanifest`:

&#x20;  ```json

&#x20;  {

&#x20;    "name": "SimHPC",

&#x20;    "short\_name": "SimHPC",

&#x20;    "start\_url": "/",

&#x20;    "display": "standalone",

&#x20;    "background\_color": "#0f172a",

&#x20;    "theme\_color": "#0f172a"

&#x20;  }

&#x20;  ```



2\. \*\*Removed broken icon references\*\* - Icons don't exist in public folder



\---



\## v2.6.10: Manifest Fix (April 2026)



\### Fix Applied



1\. \*\*Manifest Link\*\* - Uncommented and added `crossorigin="use-credentials"`:

&#x20;  ```html

&#x20;  <link rel="manifest" href="/site.webmanifest" crossorigin="use-credentials" />

&#x20;  ```



2\. \*\*Alpha Control\*\* - Opens in new tab, links to `/admin/analytics`



\---



\## v2.6.9: Alpha Control Room Integration (April 2026)



\### Fix Applied



Added \*\*Alpha Control Room\*\* to Dashboard sidebar:



1\. \*\*Sidebar Items\*\* - Added `Alpha Control` tab with Cpu icon

2\. \*\*Content Area\*\* - Added Alpha Control Room tab content

3\. \*\*Active Tab Default\*\* - Set to 'robustness' (existing)



\### Sidebar Structure



```tsx

const sidebarItems = \[

&#x20; { id: 'alpha', label: 'Alpha Control', icon: Cpu },

&#x20; { id: 'simulations', label: 'Simulations', icon: Play },

&#x20; { id: 'robustness', label: 'Robustness', icon: BarChart3 },

&#x20; { id: 'reports', label: 'Reports', icon: FileText },

&#x20; { id: 'settings', label: 'Settings', icon: Settings },

];

```



\---



\## v2.6.8: User Profile Endpoint (April 2026)



\### Fix Applied



Added `/api/v1/user/profile` endpoint to `services/api/api.py`:



```python

@app.get("/api/v1/user/profile")

async def get\_user\_profile(authorization: str = Header(None)):

&#x20;   # Returns user profile with tier and usage

```



This fixes "Failed to fetch user profile" error.



\---



\## v2.6.7: Manifest Fix (April 2026)



\### Fix Applied



1\. \*\*Disabled manifest link\*\* - Commented out in `index.html` to bypass Vercel auth issues

&#x20;  - `<link rel="manifest" href="/site.webmanifest" />` is now disabled



\### If You Still Have Issues



In Vercel Dashboard → Settings → Deployment Protection:



1\. \*\*Vercel Authentication\*\* - Ensure it's OFF (disable)

2\. If there's a "Require Owner role" checkbox - \*\*uncheck it\*\*

3\. Save changes



\---



\## v2.6.6: Manifest \& CLI Fix (April 2026)



\### Fixes Applied



1\. \*\*site.webmanifest Created\*\* - Added `apps/frontend/public/site.webmanifest` to fix 401 error

2\. \*\*Infisical CLI\*\* - Removed `infisical upgrade` command (not available in all versions)



\### 401 Error Fix (Vercel Deployment Protection)



If `site.webmanifest` still returns 401:

1\. Go to Vercel Dashboard → Settings → Deployment Protection

2\. Disable Vercel Authentication for preview/production

3\. OR add manifest link with crossorigin in index.html



\---



\## v2.6.5: AlphaControlRoom Integration (April 2026)



\### 1. AlphaControlRoom Integration



\*\*Problem:\*\* Cockpit wasn't appearing on dashboard due to routing mismatch.



\*\*Fix:\*\* Integrate AlphaControlRoom as a tab inside Dashboard:



```tsx

// Dashboard.tsx - Update activeTab default

const \[activeTab, setActiveTab] = useState('cockpit');



// Add tab trigger

<TabsTrigger value="cockpit">Alpha Cockpit</TabsTrigger>



// Add content

{activeTab === 'cockpit' \&\& <AlphaControlRoom />}

```



\### 2. Routing Fix



\*\*App.tsx:\*\* Simplified routes - Dashboard is the parent, AlphaControlRoom nested inside.



\### 3. 401/Manifest Fix



\*\*Problem:\*\* `site.webmanifest` returning 401 due to Vercel Deployment Protection.



\*\*Fix:\*\*

\- Go to Vercel Dashboard → Settings → Deployment Protection

\- Disable Vercel Authentication for preview branches

\- OR ensure `site.webmanifest` exists in `public/` folder



\### 4. User Profile Fetch Fix



\*\*Problem:\*\* "Failed to fetch user profile" - missing or invalid Supabase keys.



\*\*Fix:\*\* Ensure these environment variables are set in Vercel:

\- `VITE\_SUPABASE\_URL` - Must match Supabase Dashboard exactly

\- `VITE\_SUPABASE\_ANON\_KEY` - Must match Supabase Dashboard exactly

\- `VITE\_API\_URL` - Must match current RunPod ID



\### 5. Health Check Checklist



Run this before deploying to verify everything works:



1\. \*\*Vercel Auth:\*\* Is Deployment Protection OFF? (Prevents 401 on manifest)

2\. \*\*Pod Identity:\*\* Does `VITE\_API\_URL` match the current active RunPod ID?

3\. \*\*Supabase Auth:\*\* Can you manually log in via `/login` page? (Tests if keys work)



\---



\## v2.6.4: Infisical CLI Fix (April 2026)



\### Fixes Applied



1\. \*\*Infisical CLI Upgrade\*\* - Added `sudo infisical upgrade` after installation

2\. \*\*Project Init\*\* - Added `.infisical.json` creation with workspace ID

3\. \*\*Token Auth\*\* - Using `--token=$INFISICAL\_TOKEN` instead of env var



\### Workflow Files Fixed



\- `deploy-beta-runpod.yml` - Added project init + token flag

\- `auto-deploy-runpod.yml` - Added project init + token flag

\- `deploy\_all.sh` - Updated with project ID



\### Fixes Applied



1\. \*\*Infisical Project ID\*\* - Added `--projectId="f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4"` to all `infisical export` and `infisical run` commands

&#x20;  - `deploy-beta-runpod.yml` - Fixed

&#x20;  - `auto-deploy-runpod.yml` - Fixed



2\. \*\*AdminAnalyticsPage\*\* - Import path verified, file exists at `./pages/admin/AdminAnalyticsPage`



\### GitHub Secrets Required



| Secret | Description |

|--------|-------------|

| `INFISICAL\_TOKEN` | Infisical service token |

| `INFISICAL\_CLIENT\_ID` | Infisical client ID |

| `INFISICAL\_CLIENT\_SECRET` | Infisical client secret |

| `INFISICAL\_PROJECT\_ID` | Infisical project ID |

| `DOCKER\_LOGIN` | Docker Hub username |

| `DOCKER\_PW\_TOKEN` | Docker Hub password/token |

| `RUNPOD\_API\_KEY` | RunPod API key |

| `RUNPOD\_ID` | RunPod pod ID |



\---



\## v2.5.13: Full "No-Env" Transition (April 2026)



\### Changes Applied

\- Dynamic CORS (Regex) for Vercel branch support

\- Automated POD\_ID capture

\- Autoscaler fail-fast



\---



\## v2.5.12: Secret Handshake Skill (April 2026)



\### Changes Applied

\- Vercel sync automation

\- INFISICAL\_TOKEN injection



\---



\## v2.5.11: Reliability Features (April 2026)



\### 1. Idempotency Keys (prevent duplicate runs)



\*\*Frontend sends header:\*\*

```http

POST /api/v1/simulations

Idempotency-Key: <uuid>

```



\*\*Supabase table:\*\*

```sql

create table idempotency\_keys (

&#x20; key text primary key,

&#x20; user\_id uuid not null,

&#x20; request\_hash text not null,

&#x20; response jsonb,

&#x20; status text default 'processing',

&#x20; created\_at timestamp default now()

);

```



\*\*API logic:\*\*

```python

def hash\_request(body: dict) -> str:

&#x20;   return hashlib.sha256(json.dumps(body, sort\_keys=True).encode()).hexdigest()



\# Check existing

existing = supabase.table("idempotency\_keys").select("\*").eq("key", key).execute()

if existing.data:

&#x20;   if existing.data\[0]\["request\_hash"] == request\_hash:

&#x20;       return existing.data\[0]\["response"]  # Return cached

&#x20;   raise HTTPException(409, "Idempotency key reuse with different payload")

```



\---



\### 2. Job Status Persistence (Supabase = Source of Truth)



\*\*Redis = transport, Supabase = truth\*\*



\*\*Table:\*\*

```sql

create table simulations (

&#x20; id uuid primary key,

&#x20; user\_id uuid,

&#x20; status text check (status in ('queued','running','completed','failed')),

&#x20; input jsonb,

&#x20; result jsonb,

&#x20; error text,

&#x20; created\_at timestamp default now(),

&#x20; updated\_at timestamp default now()

);

```



\*\*API writes on enqueue:\*\*

```python

supabase.table("simulations").insert({

&#x20;   "id": job\_id,

&#x20;   "user\_id": user\["user\_id"],

&#x20;   "status": "queued",

&#x20;   "input": data

}).execute()

```



\*\*Worker state transitions:\*\*

```python

\# On start

supabase.table("simulations").update({"status": "running"}).eq("id", job\_id).execute()



\# On success

supabase.table("simulations").update({"status": "completed", "result": result}).eq("id", job\_id).execute()



\# On failure

supabase.table("simulations").update({"status": "failed", "error": str(e)}).eq("id", job\_id).execute()

```



\---



\### Final Architecture



```

Frontend

&#x20;  ↓ (Idempotency-Key)

API (FastAPI)

&#x20;  ├── verifies user

&#x20;  ├── enforces idempotency

&#x20;  ├── writes "queued" → Supabase

&#x20;  └── pushes job → Redis



Worker

&#x20;  ├── pops job

&#x20;  ├── updates "running"

&#x20;  ├── executes simulation

&#x20;  ├── updates "completed"/"failed"

&#x20;  └── publishes event (WebSocket)



Supabase = SOURCE OF TRUTH

Redis = TRANSPORT LAYER

```



\### Problems Solved



| Problem | Fixed by |

|---------|----------|

| Duplicate runs | Idempotency keys |

| Lost job state | Supabase persistence |

| Worker crash mid-job | Status recoverable |

| Retry duplication | Same job\_id reused |

| UI inconsistency | DB = truth |



\---



\## v2.5.10: Advanced Features (April 2026)



\### 1. Auth Passthrough (Supabase → API → Worker)



\*\*API verifies JWT and injects user context into job:\*\*



```python

\# services/api/auth.py

def verify\_user(authorization: str = Header(None)):

&#x20;   token = authorization.replace("Bearer ", "")

&#x20;   payload = jwt.decode(token, SB\_JWT\_SECRET, algorithms=\["HS256"])

&#x20;   return {

&#x20;       "user\_id": payload.get("sub"),

&#x20;       "email": payload.get("email"),

&#x20;       "role": payload.get("role"),

&#x20;   }



\# Enqueue with user context

job = {

&#x20;   "id": str(uuid.uuid4()),

&#x20;   "payload": data,

&#x20;   "user": user,  # ✅ user\_id, email, role

&#x20;   "created\_at": time.time(),

}

```



\*\*Worker accesses user context:\*\*



```python

job = json.loads(job\_raw)

user = job.get("user", {})

user\_id = user.get("user\_id")

tier = user.get("role")

```



\---



\### 2. Retry + Dead Letter Queue (DLQ)



\*\*Queue Strategy:\*\*



| Queue | Purpose |

|-------|---------|

| `simhpc\_jobs` | Main queue |

| `simhpc\_jobs\_retry` | Retry queue |

| `simhpc\_jobs\_dlq` | Dead letter |



\*\*Worker logic:\*\*



```python

MAX\_RETRIES = 3



def process\_job(job):

&#x20;   try:

&#x20;       run\_simulation(job)

&#x20;   except Exception as e:

&#x20;       job\["retries"] = job.get("retries", 0) + 1

&#x20;       job\["error"] = str(e)



&#x20;       if job\["retries"] < MAX\_RETRIES:

&#x20;           redis.rpush("simhpc\_jobs\_retry", json.dumps(job))

&#x20;       else:

&#x20;           redis.rpush("simhpc\_jobs\_dlq", json.dumps(job))

```



\---



\### 3. WebSocket Real-Time Updates



\*\*API WebSocket endpoint:\*\*



```python

\# services/api/ws.py

connections = defaultdict(list)



async def websocket\_endpoint(ws: WebSocket, user\_id: str):

&#x20;   await ws.accept()

&#x20;   connections\[user\_id].append(ws)

&#x20;   try:

&#x20;       while True: await ws.receive\_text()

&#x20;   except: connections\[user\_id].remove(ws)

```



\*\*Worker publishes events via Redis:\*\*



```python

redis.publish("simhpc\_events", json.dumps({

&#x20;   "user\_id": user\_id,

&#x20;   "event": {"job\_id": job\_id, "status": status}

}))

```



\*\*Frontend connects:\*\*



```ts

const ws = new WebSocket(`wss://api.com/ws?user\_id=${user.id}`)

ws.onmessage = (msg) => updateStatus(JSON.parse(msg.data))

```



\---



\### Architecture Summary



```

Frontend → Vercel /api/\* → API (JWT verify) → Redis queue → Worker

&#x20;                      ↓                    ↓                    ↓

&#x20;                  WebSocket          Job + user           publish events

&#x20;                  (real-time)        context              → Redis pubsub

```



\### GitHub Secrets Required



| Secret | Description |

|--------|-------------|

| `INFISICAL\_CLIENT\_ID` | Infisical client ID |

| `INFISICAL\_CLIENT\_SECRET` | Infisical client secret |

| `INFISICAL\_PROJECT\_ID` | Infisical project ID |

| `DOCKER\_LOGIN` | Docker Hub username |

| `DOCKER\_PW\_TOKEN` | Docker Hub password/token |

| `RUNPOD\_API\_KEY` | RunPod API key |

| `RUNPOD\_ID` | RunPod pod ID |



\---



\## v2.5.9: Architecture Fixed (April 2026)



\### ⚠️ VERIFIED WORKING (Production Checklist)



\- \[ ] Frontend ONLY calls `/api/\*` (not direct runpod.net)

\- \[ ] No CORS issues (proxy handles routing)

\- \[ ] Vercel proxy returning 200 for /api/v1/\*

\- \[ ] Worker pulling jobs from Redis successfully



\### Changes Applied



1\. \*\*Worker = Pure Compute\*\* - Removed FastAPI, CORS, HTTP endpoints from worker

&#x20;  - Worker now ONLY consumes Redis queue

&#x20;  - Single shared Redis client (not per-loop)

&#x20;  - Single job format: JSON with `id`, `status`, `progress`



2\. \*\*Clean Architecture\*\*:

&#x20;  ```

&#x20;  Frontend → Vercel /api/\* → Proxy → RunPod API → Redis → Worker

&#x20;  ```



\### Key Design Rules



| Rule | Description |

|------|-------------|

| One HTTP surface | API handles all HTTP, Worker has none |

| One job format | JSON only: `{"id": "...", "status": "queued"}` |

| Frontend → /api/\* | Never call RunPod directly from browser |



\### GitHub Secrets Required



| Secret | Description |

|--------|-------------|

| `INFISICAL\_CLIENT\_ID` | Infisical client ID |

| `INFISICAL\_CLIENT\_SECRET` | Infisical client secret |

| `INFISICAL\_PROJECT\_ID` | Infisical project ID |

| `DOCKER\_LOGIN` | Docker Hub username |

| `DOCKER\_PW\_TOKEN` | Docker Hub password/token |

| `RUNPOD\_API\_KEY` | RunPod API key |

| `RUNPOD\_ID` | RunPod pod ID |



\---



\## v2.5.8: Blockers Fixed (April 2026)



\### Changes Applied



1\. \*\*vercel.json updated\*\* - Added API rewrite rule:

&#x20;  ```json

&#x20;  { "source": "/api(/.\*)?", "destination": "/api/\[...path]" }

&#x20;  ```

&#x20;  This routes all `/api/\*` requests through the proxy.



2\. \*\*Proxy exists\*\* - `apps/frontend/api/\[...path].ts` already handles proxying requests to RunPod.



\### How It Works



\- Frontend calls `/api/v1/simulations` (same-origin)

\- Vercel rewrites to `/api/\[...path].ts`

\- Proxy forwards to `https://{pod}.proxy.runpod.net/api/v1/simulations`

\- No CORS needed - server-to-server call



\### Environment Variables (Vercel)



| Key | Value |

|-----|-------|

| `RUNPOD\_API\_KEY` | Your RunPod API key |

| `RUNPOD\_POD\_NAME` | Pod name to filter (optional) |



\---



\## v2.5.6: Comprehensive Audit Applied (April 2026)



\### Key Fixes Applied



1\. \*\*APIReference Import Fix\*\* - Removed broken import from `apps/frontend/src/pages/index.ts`

2\. \*\*CORS Configuration\*\* - Updated `ALLOWED\_ORIGINS` with explicit origins (no wildcards)

3\. \*\*GitHub CI\*\* - Updated Node version to 22, added Infisical token support

4\. \*\*Vercel Build\*\* - Fixed by removing non-existent component import



\### Test Commands



```bash

\# Test health endpoint

curl https://your-pod.proxy.runpod.net/api/v1/health



\# Test profile fetch

curl -H "Authorization: Bearer YOUR\_TOKEN" \\

&#x20; https://your-pod.proxy.runpod.net/api/v1/user/profile

```



\### Environment Variables Required



| Key | Value |

|-----|-------|

| `ALLOWED\_ORIGINS` | `http://localhost:3000,http://localhost:5173,http://localhost:59824,http://127.0.0.1:59824,https://simhpc-nexusbayareas-projects.vercel.app,https://simhpc.nexusbayarea.com,https://simhpc.com` |

| `SB\_URL` | Supabase project URL |

| `SB\_SERVICE\_KEY` | Supabase service role key |

| `SB\_JWT\_SECRET` | Supabase JWT secret |

| `REDIS\_URL` | Redis connection string |



\---



\## v2.5.5 Architecture: Vercel Proxy Layer



\### Problem

CORS errors persist between frontend (Vercel) and backend (RunPod) due to origin mismatches.



\### Solution: Vercel API Route Proxy (`api/\[...path].ts`)

```ts

export default async function handler(req, res) {

&#x20; const BASE\_URL = process.env.RUNPOD\_API\_URL;

&#x20; const path = req.query.path?.join("/") || "";

&#x20; const url = `${BASE\_URL}/${path}`;



&#x20; const response = await fetch(url, {

&#x20;   method: req.method,

&#x20;   headers: {

&#x20;     "Content-Type": "application/json",

&#x20;     Authorization: req.headers.authorization || "",

&#x20;   },

&#x20;   body: req.method !== "GET" \&\& req.method !== "HEAD" ? JSON.stringify(req.body) : undefined,

&#x20; });



&#x20; res.status(response.status).send(await response.text());

}

```



\### Benefits

\- Eliminates CORS permanently (server-to-server)

\- Centralized auth passthrough

\- Unified `/api/\*` layer for all backend calls

\- Easy to add logging/rate limiting



\### Frontend Changes

```ts

// Before (CORS issues)

fetch("https://runpod-pod.proxy.runpod.net/api/v1/...")



// After (proxy)

fetch("/api/api/v1/...")

```



\### Environment Variables (Vercel)

\- `RUNPOD\_API\_URL` = `https://{POD\_ID}-8000.proxy.runpod.net`



\---



\## v2.5.5: SB\_ Env Prefix for Infisical



\### Problem

Infisical flags secrets containing "SUPABASE" as sensitive.



\### Changes

| Old | New |

|-----|-----|

| `SUPABASE\_URL` | `SB\_URL` |

| `SUPABASE\_SERVICE\_ROLE\_KEY` | `SB\_SERVICE\_KEY` |

| `SUPABASE\_JWT\_SECRET` | `SB\_JWT\_SECRET` |

| `SUPABASE\_AUDIENCE` | `SB\_AUDIENCE` |



\### Required RunPod Pod Environment Variables

| Key | Value |

|-----|-------|

| `SB\_URL` | Supabase project URL |

| `SB\_SERVICE\_KEY` | Supabase service role key |

| `SB\_JWT\_SECRET` | Supabase JWT secret |

| `SB\_AUDIENCE` | `authenticated` |

| `ALLOWED\_ORIGINS` | CORS allowed origins |

| `REDIS\_URL` | Redis connection string |



\---



\## Pending Fixes (Not Yet Applied)



\### 1. APIReference Import Fix

File: `apps/frontend/src/pages/index.ts`

\- Remove or fix `./APIReference` import that doesn't exist



\### 2. Ruff Lint Fixes

File: `services/worker/worker.py`

\- Remove unused imports: `hashlib`, `requests`, `ConnectionError`

\- Fix one-line if statements (E701)



\### 3. GitHub Actions Node Version

Update to Node 22:

```yaml

uses: actions/setup-node@v4

with:

&#x20; node-version: 22

```



\### 4. Manifest 401 Fix

Ensure `/site.webmanifest` exists in `/public` or remove from HTML



\## v2.5.5: Dynamic Pod Synchronization + Infisical Integration



\### Phase 4: Pod Metadata Sync

When a new Pod is provisioned, values propagate to secrets vault and trigger frontend rebuild.



\*\*sync-pod.sh\*\* (`scripts/sync-pod.sh`):

```bash

./scripts/sync-pod.sh <POD\_ID>

\# Updates: RUNPOD\_POD\_ID, VITE\_API\_URL in Infisical

\# Triggers: Vercel redeploy with new URL

```



\### In-Memory Cache Fallback

API now gracefully falls back to in-memory cache when Redis is unavailable.



\*\*New Helpers:\*\*

\- `get\_cache()` - Returns Redis or InMemoryCache

\- `is\_redis\_available()` - Returns bool for cache mode detection

\- Health check now shows `cache\_mode: "redis" | "in\_memory\_fallback"`



\### Updated Master Deploy Flow

```bash

\# 1. Build \& Push Docker

docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .

docker push simhpcworker/simhpc-unified:latest



\# 2. Provision New Pod

NEW\_POD\_ID=$(python3 scripts/deploy\_unified.py | grep -oP '(?<=pod\_id: )\[a-z0-9]+')



\# 3. Sync Metadata

./scripts/sync-pod.sh $NEW\_POD\_ID



\# 4. Update GitHub

git add . \&\& git commit -m "deploy: update pod to $NEW\_POD\_ID" \&\& git push



\# 5. Fleet Synced

```



\---



\- \*\*v2.5.4\*\*: SimHPC Skills System + Git Auto-Deploy + Env-Based CORS + \*\*Unified Deployment (API+Worker+Autoscaler in Single Pod)\*\* + \*\*Dynamic Sync Script\*\* + Docker Lean Images + Infisical Integration + Multi-Stage Builds + Non-Root Execution + CVE Remediations + PYTHONPATH Fix for Module Imports + \*\*Vercel Build Fix (APIReference import)\*\* + \*\*Deployment Skills (Vercel, GitHub Safe Push, deploy\_all.sh)\*\* + \*\*Supabase SB\_ Secret Sync (sb-sync.sh)\*\* + \*\*Zod Downgrade to 3.24.4\*\* + \*\*Vite Chunk Size Optimization\*\* + \*\*Supabase Real Credentials\*\* + \*\*CORS Fix (Allow All Origins + Vercel Regex)\*\*



\## Deployment Skills System (v2.5.4)



\### Skills Structure

```

skills/

├── antigravity/     # AI agent skills

├── deployment/       # Deployment pipeline skills

│   ├── SKILL.md

│   ├── vercel-deploy.md

│   └── github-safe-push.md

├── docker/         # Docker optimization

├── runpod/         # RunPod deployment

└── ...

```



\### Master Deploy Script (deploy\_all.sh)

```bash

\#!/bin/bash

echo "\[1/5] Running Local Build Test..."

infisical run -- npm run build



if \[ $? -ne 0 ]; then

&#x20;   echo "Local build failed. Fix pathing/imports before pushing."

&#x20;   exit 1

fi



echo "\[2/5] Build passed. Syncing Infisical..."

infisical secrets push



echo "\[3/5] Deploying to Vercel..."

infisical run --env=production -- vercel --prod --yes



echo "\[4/5] Fixing Git Casing..."

git rm -r --cached .

git add .

git commit -m "fix: resolve APIReference pathing and sync v2.5.4"



echo "\[5/5] Pushing to GitHub..."

git push origin main

```



\- \*\*v2.6.3\*\*: \*\*Vercel Build Stability\*\* (File Migration \& Path Fixes) + \*\*Infisical Project Integration\*\* (Explicit ProjectID in CI) + \*\*Refreshed Installation Scripts\*\*

\- \*\*v2.6.2\*\*: \*\*CI/CD Hardening\*\* (Infisical Token Standard, Docker Secret Alignment) + \*\*File Path Normalization\*\* (AlphaControlRoom)

\- \*\*v2.6.1\*\*: Bare Except Guard (Specific Exceptions) + Python Worker Hardening (JSON/Type Error Handling) + Hardened Deployment Script

\- \*\*v2.6.0\*\*: Cost-Optimized Autoscaler (120s Idle Timeout) + Dormant Termination (48h) + Direct-Action Admin API (`runpod\_service.py`) + Admin Dashboard Auto-Term Visibility + Accurate Cost Tracking

\- \*\*v2.5.6\*\*: Advanced Dynamic API Proxy (Vercel) + Cold Start Resilience (Retry/Backoff) + Caching + `@app.get("/health")` Endpoint + Resolved CORS permanently

\- \*\*v2.5.5\*\*: Unified API Proxy (Vercel) Implementation + Vercel Build Fix (APIReference) + Python Worker Lint Fix (`ruff --fix`) + Frontend API Proxy Alignment + Deployment SOP v2.5.5

\- \*\*v2.5.4\*\*: Detailed Error Surface in `api.ts` + Empty Token Guard + Infisical Machine Identity v2.5.4

\- \*\*v2.5.3\*\*: Full Fleet Build (Worker, API, Autoscaler) + Security Hardening (Non-Root Execution) + CVE Remediations + Infisical Integration + CORS Policy Update (Exposed Headers + Explicit OPTIONS Preflight) + Integrated SimHPC Skill Tool (`fix-all`) + `run\_api.py` Entry Point Audit + Vercel Deployment Preparation

\- \*\*v2.5.2\*\*: Fixed Supabase key authentication (JWT) + Worker heartbeat fix + API deployed to RunPod

\- \*\*v2.5.1\*\*: FastAPI Dependency Injection Fix + RunPod URL Fix + Route Ordering Fix + Worker Queue Fix + Queue Key Alignment + Lazy Redis + Docker .env Removal + Admin Import Fix + Route Import Fix + Control Data Fix

\- \*\*v2.5.0\*\*: Structural Consolidation (Single Source of Truth), Unified Worker Plane, Schema Normalization, \*\*Simulation Usage Quota \& Anti-Spam Enforcement\*\*, \*\*Health Check Endpoint\*\*, \*\*Worker Heartbeat Always-On\*\*, \*\*Ruff Lint Clean (0 errors)\*\*, \*\*Pre-Commit Framework + GitHub Actions CI\*\*, \*\*Unified Deployment Pipeline\*\*, \*\*RunPod Auto-Updater\*\*, \*\*Admin RBAC (ProtectedRoute)\*\*, \*\*Admin Dashboard (Sidebar + KPIs)\*\*, \*\*Supabase Edge Function (Fleet Metrics)\*\*, \*\*Platform Alerts + Billing Threshold\*\*, \*\*Panic Button (Terminate All Fleet)\*\*, \*\*Real-Time Telemetry Hook\*\*, \*\*Guidance Engine (Mercury AI)\*\*, \*\*Docker Path Alignment\*\*, \*\*Race Condition Fix\*\*, \*\*Credential Sanitization\*\*, \*\*Infisical Universal Auth (RogWin)\*\*, \*\*Docker Worker Image v2.5.0 Built\*\*, \*\*Supabase CLI Linked \& Deployed (ldzztrnghaaonparyggz)\*\*.



\## Full Fleet Build \& Security Hardening (v2.5.3)



\### Problem: Image Bloat \& Root Vulnerabilities



Previous images were over 2GB (API) and used default root users, increasing the attack surface. Autoscaler lacked Infisical integration for secret management.



\### Fix: Hardened Fleet v2.5.3



1\. \*\*Worker (`simhpc-worker:v2.5.3`)\*\*:

&#x20;  - Switched to `nvidia/cuda:12.8.1-runtime-ubuntu22.04` base.

&#x20;  - Enforced \*\*non-root execution\*\* with `simuser`.

&#x20;  - Applied critical security patches for `setuptools`, `wheel`, and `pip`.

2\. \*\*API (`simhpc-api:v2.5.3`)\*\*:

&#x20;  - Implemented \*\*Multi-Stage Build\*\* (Builder → Runtime) reducing image size.

&#x20;  - Hardened with non-root `simuser` and gunicorn/uvicorn stack.

&#x20;  - Added automated Healthcheck for `v1/health`.

3\. \*\*Autoscaler (`simhpc-autoscaler:v2.5.3`)\*\*:

&#x20;  - Integrated \*\*Infisical CLI\*\* for just-in-time secret injection.

&#x20;  - Multi-stage build with non-root user for process isolation.

&#x20;  - Uses `infisical run --` to wrap the Python entry point.



\---



\## FastAPI Dependency Injection Fix (v2.5.1)



\### Problem: Startup Crash - `ValueError: no signature found for builtin type <class 'dict'>`



FastAPI was crashing at API startup when inspecting the `Depends(verify\_auth)` pattern. The module-level `verify\_auth: Any = None` caused FastAPI to try to introspect `None` (or Python's built-in `dict` type) which has no callable signature.



\### Fix: Stub Function Pattern



Replaced all module-level `None` defaults with proper stub functions that FastAPI can introspect at import/include time:



```python

\# Before (broken)

verify\_auth: Any = None



\# After (working)

def verify\_auth(authorization: str = Header(None)) -> dict:

&#x20;   """Stub replaced by init\_routes(). If called, app wasn't initialized."""

&#x20;   raise RuntimeError("verify\_auth not initialized — call init\_routes() first")

```



Applied to: `verify\_auth` in `simulations.py`, `control.py`, `certificates.py`, `verify\_admin` in `admin.py`.



\### Additional Fixes in v2.5.1



1\. \*\*RunPod Status URL Fix\*\*: `get\_job\_status` was missing `pod\_id` in the URL path (was `/status/{job\_id}`, now `/{pod\_id}/status/{job\_id}`)



2\. \*\*enqueue\_job Signature Fix\*\*: Changed `enqueue\_job(sim\_id, job\_data)` to `enqueue\_job(job\_data)` to match `job\_queue.py` signature



3\. \*\*Route Ordering Fix\*\*: Moved `/simulations/usage` route above `/{sim\_id}` to prevent `/usage` from being caught as a sim\_id parameter



4\. \*\*Worker Queue Busy Loop Fix\*\*: Changed `lpush` to `rpush` when pushing back jobs at capacity to prevent tight busy loop



5\. \*\*Queue Key Alignment\*\*: Changed `job\_queue.py` from `"jobs:pending"` to use `os.getenv("QUEUE\_NAME", "simhpc\_jobs")` — aligns with worker's `QUEUE\_NAME` default



6\. \*\*Lazy Redis Connection\*\*: Wrapped Redis connection in `get\_redis()` lazy init function instead of connecting at import time — prevents crash during docker-compose startup or Vercel cold start



7\. \*\*Docker .env Removal\*\*: Removed `COPY services/api/.env ./` from `Dockerfile.api` — secrets should be passed as runtime environment variables, not baked into image



8\. \*\*Admin Import Fix\*\*: Removed broken `sys.path.append` import of `autoscaler.py` from admin.py — replaced with fallback that indicates Redis pub/sub IPC not implemented



9\. \*\*Route Import Fix\*\*: Fixed `onboarding.py` relative imports (`...schemas.onboarding`) that would fail in Docker — now uses try/except with absolute imports



10\. \*\*Control Data Fix\*\*: Removed hardcoded fake alerts from `control.py` — now fetches real alerts from Redis keys `alert:\*` and timeline from `timeline:\*`

\- \*\*v2.4.1-DEV\*\*: Mission Control Cockpit Synchronization + Persistent Onboarding (Autosave \& Cross-Device Resume).

\- \*\*v2.4.0-DEV\*\*: Interactive Onboarding (Guided Walkthrough) + Event-Driven Trigger Engine.

\- \*\*v2.3.0\*\*: Option C Autoscaler (Stop/Resume) + Network Volume Persistence + "Wake GPU" Admin Panel.

\- \*\*v2.2.1\*\*: RunPod API Integration + Queue-Aware Autoscaler + Docker Hub Images.

\- \*\*v1.6.0-ALPHA\*\*: Mission Control Cockpit (Modular Design Intelligence Platform).

\- \*\*v1.5.1-ALPHA\*\*: Alpha Control Room (4-Panel UI).

\- \*\*v1.4.0-BETA\*\*: Direct Vercel Deployment \& RunPod Orchestration.



\---



\## Structural Consolidation: Single Source of Truth (v2.5.0)



\### Problem: Fragmented Worker \& Scaling Logic



The `v2.4` codebase had logic spread across `services/runpod-worker/`, `services/worker/`, and `robustness-orchestrator/`. Key issues:

\- Multiple `worker.py` and `autoscaler.py` versions causing "truth drift."

\- Scaling logic (`idle\_timeout.py`) buried in an `/app/` subdirectory.

\- Standalone services (PDF, AI Report) not integrated into the primary worker loop.

\- Deployment manifests (`Dockerfile.worker`) referencing outdated paths.



\### Fix: Unified Compute Plane



1\.  \*\*Unified `services/worker/`\*\*: Consolidated all compute-related logic into a single, clean directory.

2\.  \*\*Truth Promotion\*\*:

&#x20;   - Promoted `worker.py` (v2.5.0) as the canonical physics execution engine.

&#x20;   - Promoted `idle\_timeout.py` (v2.3.0) and renamed it to `autoscaler.py` as the official scaling strategy.

&#x20;   - Integrated `ai\_report\_service.py` and `pdf\_service.py` into the worker runtime.

3\.  \*\*API Integration\*\*: Updated `services/api/api.py` to point to the unified `services/worker/` for fleet management and "Warm" commands.

4\.  \*\*Legacy Purge\*\*: Created `legacy\_archive/` to house all deprecated v1.6.0-ALPHA and v2.2.1 artifacts.

5\.  \*\*Security Hardening\*\*: Enforced April 1st standard for `.env` protection and Git hygiene.



\---



\## Beta Hardening: Alignment \& Tightening (Complete)



\### Backend Accuracy



\- \*\*Standardized API Namespaces\*\*: Ensured all frontend routing goes through `api/v1/`.

\- \*\*Runtime Validation\*\*: Added `schemas.ts` bringing strict `zod` validation protecting against worker inconsistencies.

\- \*\*Idempotency\*\*: Added UUID-based API idempotency (`Idempotency-Key` headers) to `Certificate` generation so multiple quick requests don't duplicate generation.

\- \*\*Background Queues Mocked\*\*: Certificates endpoints updated to avoid blocking API threads, correctly returning `processing` statuses under async operations.



\### Frontend UI Alignment



\- \*\*Single Source of Truth\*\*: Replaced multiple data models mapping UI directly from `simulations` database responses.

\- \*\*States Visualized\*\*: Surfaced real status keys ("running", "auditing", "completed") directly mapping them to components (e.g. `SimulationDetailModal`).

\- \*\*Cockpit Tightened\*\*: Explicitly disabled high-risk "Clone" and "Intercept" actions to reduce vulnerability ahead of beta scale operations while enabling "boost" and "certify".



\---



\## Schema Normalization: Single Source of Truth (v2.5.0)



\### Problem: Schema Drift + Inconsistent Contracts



The `simulation\_history` table had drifted from the API response shapes and frontend types. Key issues:



\- Frontend expected `ai\_insight` and `metrics` in `result\_summary`, but worker wrote `data` and `pdf\_url`

\- Control Room API returned `id`/`model\_name` but frontend expected `run\_id`/`model`

\- Alert shapes mismatched between API (`id`, `type`) and frontend (`alert\_id`, `level`, `source`)

\- Timeline events used `content` but frontend expected `label` and `severity`

\- Lineage edges used `from`/`to` but frontend expected `source`/`target`

\- No certificates table, no audit trail, no org-level isolation



\### Fix: Beta-Ready Production Schema



1\. \*\*Core Table Renamed\*\*: `simulation\_history` → `simulations` with backward-compatible view

2\. \*\*New Columns\*\*: `org\_id`, `prompt`, `input\_params`, `gpu\_result`, `audit\_result`, `hallucination\_score`, `certificate\_id`, `error`, `pdf\_url`, `updated\_at`

3\. \*\*Status Constraint\*\*: CHECK constraint enforcing `queued`, `running`, `auditing`, `completed`, `failed`

4\. \*\*Supporting Tables\*\*: `certificates`, `documents`, `document\_chunks`, `simulation\_events`

5\. \*\*RLS Policies\*\*: User-level and org-level isolation with service-role bypass

6\. \*\*Auto `updated\_at`\*\*: Trigger-based timestamp updates

7\. \*\*Performance Indexes\*\*: 7 new indexes on high-query columns

8\. \*\*TypeScript Contracts\*\*: 5 new type files (`db.ts`, `audit.ts`, `api.ts`, `realtime.ts`, `view.ts`)

9\. \*\*Backend Alignment\*\*: `api.py` and `worker.py` updated to write to `simulations` table

10\. \*\*Frontend Alignment\*\*: `useSimulationUpdates`, `controlRoomStore`, `Dashboard`, `SimulationDetailModal` updated to use new types



\### API Routes Split



`api.py` (1281 lines) split into modular route files:

\- \*\*`routes/simulations.py`\*\*: `POST /simulations`, `GET /simulations`, `GET /simulations/{id}`, `POST /simulations/{id}/export-pdf`, `GET /simulations/{id}/status`

\- \*\*`routes/certificates.py`\*\*: `POST /simulations/{id}/certificate`, `GET /certificates/{id}/verify`

\- \*\*`routes/control.py`\*\*: `GET /controlroom/state`, `POST /control/command`, `GET /control/timeline`, `GET /control/lineage`

\- \*\*`routes/admin.py`\*\*: Fleet management endpoints (warm, readiness, status, stop, terminate)

\- \*\*`routes/onboarding.py`\*\*: Already existed



All routes use `init\_routes()` pattern to receive shared dependencies from `api.py`.



\---



\## Mission Control Cockpit: Backend Synchronization (v2.4.1-DEV)



\### Problem: Disconnected Cockpit Components



While the frontend "Cockpit" UI (O-D-I-A-V loop) was designed in `v1.6.0`, many of its command and telemetry components were placeholders or lacked robust backend implementation, leading to "stale" telemetry and non-functional control buttons.



\### Fix: Unified Control Subsystem



1\. \*\*Unified State Aggregator\*\*:

&#x20;   - Implemented `GET /api/v1/controlroom/state` to provide a single, consistent snapshot of active runs, audit alerts, and temporal events.

&#x20;   - Synchronized with `controlRoomStore.ts` to hydrate the entire Cockpit on mount.

2\. \*\*Explicit Command Execution\*\*:

&#x20;   - Implemented `POST /api/v1/control/command` with support for `intercept`, `clone`, `boost`, and `certify`.

&#x20;   - Integrated the \*\*Operator Console\*\* with real-world job state transitions in Redis.

3\. \*\*Temporal \& Structural Lineage\*\*:

&#x20;   - Added `GET /api/v1/control/timeline` and `GET /api/v1/control/lineage` to support the horizontal marquee and parent-child design ancestry graph.

&#x20;   - Renamed and synchronized `lineageData` in `controlRoomStore.ts` for consistent state hydration.

4\. \*\*Admin Fleet Control \& Navigation\*\*:

&#x20;   - Extracted the standalone `WakeGPU.tsx` component and linked it to the `v2.4.1` primary Dashboard Sidebar.

&#x20;   - Verified the existence and routing of `/admin/analytics` for centralized fleet management.

5\. \*\*Tier-Gated Artifact Access\*\*:

&#x20;   - Integrated signed-URL logic for PDF Report downloads in `SimulationDetailModal.tsx`.

&#x20;   - Implemented Professional-tier checks (`profile.plan`) to prevent unauthorized artifact access on the Free tier.

6\. \*\*Technical UI Stability\*\*:

&#x20;   - Resolved `getToken` Promise handling across all cockpit components.

&#x20;   - Fixed `tsconfig.json` path alias resolution (`@/\*`) for the monorepo frontend.

&#x20;   - Standardized `Button.tsx` with a professional `class-variance-authority` (CVA) implementation to resolve project-wide typing errors.



\## Persistent Onboarding: Autosave \& Cross-Device Resume (v2.4.1-DEV)



\### Problem: Fragmented User Journey



Users often start onboarding on one device (e.g., mobile) and want to continue on another (e.g., desktop). Without persistence, users are forced to restart or skip the walkthrough, leading to lower conversion and higher drop-off.



\### Fix: Versioned Autosave System



1\. \*\*Backend (FastAPI + Supabase)\*\*:

&#x20;   - Added `GET /api/onboarding` and `POST /api/onboarding` endpoints.

&#x20;   - Implemented \*\*Versioned Conflict Resolution\*\*: Rejects stale writes with `409 Conflict`.

&#x20;   - Added event tracking via `POST /api/onboarding/event`.

2\. \*\*Frontend (Zustand + React)\*\*:

&#x20;   - \*\*Debounced Autosave\*\*: State is synced to the backend 1s after any change.

&#x20;   - \*\*Instant Resume\*\*: Uses `localStorage` for immediate UI response while backend syncs.

&#x20;   - \*\*Conflict Recovery\*\*: Automatically hydrates state from the server upon detecting a version mismatch.

&#x20;   - \*\*Multi-Device Polling\*\*: Syncs every 30s to detect progress made on other devices.



\---



\## Interactive Onboarding: Guided Product Walkthrough (v2.4.0-DEV)



\### Structural Alignment \& Store Refactoring (April 01, 2026)



\### Problem: Documentation/Implementation Mismatch



The `ARCHITECTURE.md` referenced a standalone `WakeGPU.tsx` component that didn't exist (it was inlined in `AdminAnalytics.tsx`). Additionally, the user-facing term `lineageData` was inconsistently mapped to a `lineage` property in the `controlRoomStore.ts`.



\### Fix: Component Extraction \& Store Synchronization



1\. \*\*Extracted `WakeGPU.tsx`\*\*:

&#x20;   - Created a reusable component at `apps/frontend/src/components/admin/WakeGPU.tsx`.

&#x20;   - Refactored `AdminAnalytics.tsx` to use the new component, ensuring architectural consistency.

2\. \*\*Synchronized Lineage State\*\*:

&#x20;   - Renamed the store property from `lineage` to `lineageData` and the setter to `setLineageData`.

&#x20;   - Updated all consumer components (`AlphaControlRoom.tsx`, `SimulationMemory.tsx`, `SimulationLineage.tsx`) to reflect the new naming convention.

3\. \*\*Documentation Audit\*\*: Verified the existence and routing of `/admin/analytics`.



\---



\## Guided Product Walkthrough: The Onboarding Flow (v2.4.0)



SimHPC's advanced physics capabilities can be overwhelming for new users. First-time users often hesitate to run their first simulation or miss the value of the MLE (Machine Learning Enhancement) module.



\### Fix: Progressive Event-Driven Onboarding



1\. \*\*Guided 8-Step Journey\*\*:

&#x20;   - \*\*Step 1\*\*: Welcome Modal (First Login Trigger).

&#x20;   - \*\*Step 2\*\*: Template Selection (Highlight \& Dim UI).

&#x20;   - \*\*Step 3\*\*: Configuration (Progressive Tooltips).

&#x20;   - \*\*Step 4\*\*: Queue Awareness (Soft Sell for GPU).

&#x20;   - \*\*Step 5\*\*: Results Visualization (The "Value" Moment).

&#x20;   - \*\*Step 6\*\*: MLE Optimization (The "Differentiation" Moment).

&#x20;   - \*\*Step 7\*\*: Comparison View (Proof of Value).

&#x20;   - \*\*Step 8\*\*: Conversion Trigger (Soft Paywall/Upgrade Card).

2\. \*\*Conversion Intelligence\*\*:

&#x20;   - Triggered by high queue wait times or MLE GPU recommendations.

&#x20;   - Inline upgrade cards for "Unlock Full Power."

3\. \*\*Technical Foundation\*\*:

&#x20;   - \*\*Frontend\*\*: Zustand state with persistent `onboarding\_state` sync.

&#x20;   - \*\*Animation\*\*: Smooth transitions via Framer Motion.

&#x20;   - \*\*Backend\*\*: Event stream tracking in FastAPI to trigger context-aware hints.



\---



\## Option C: On-Demand GPU + Network Volumes (March 28, 2026)



\### Problem: Cold Start \& Cost Overhead



Previous autoscaling destroyed pods completely, leading to \~3 minute cold starts and loss of solver caches. Scaling up from zero was inefficient for live demos.



\### Fix: Hibernation Strategy (v2.3.0)



1\. \*\*Option C Autoscaler (`idle\_timeout.py`)\*\*:

&#x20;  - Replaced `terminate\_pod` with `stop\_pod` to keep the pod disk.

&#x20;  - Preserves \*\*Network Volume\*\* at `/workspace` for global persistence.

&#x20;  - Resumes stopped pods in \~90 seconds (2x faster than fresh creation).

&#x20;  - Idle cost reduced to disk-only (\~$0.10/day total dormant cost).

2\. \*\*Proactive "Wake GPU" Control\*\*:

&#x20;  - Added `POST /api/v1/admin/fleet/warm` to resume pods on demand.

&#x20;  - Created `WakeGPU.tsx` component for the admin cockpit to trigger warm-up 90s before demos.

&#x20;  - Live readiness polling via `/api/v1/admin/fleet/readiness`.

3\. \*\*Rich Fleet API\*\*:

&#x20;  - Consolidated status including stopped pod IDs and cost tracking.



\## RunPod API + Cost-Aware Autoscaler (March 25, 2026)



\### Security Audit: Git Hardening (March 28, 2026)



\- \*\*Fix: .gitignore Negation Syntax\*\*: Standardized `!filename` patterns to prevent unintentional ignoring of schema/example files.

\- \*\*Fix: .env Untracked\*\*: Physically removed tracked `.env` file from Git cache to stop secrets exposure.

\- \*\*Policy Enforcement\*\*: Updated `GEMINI.md`, `README.md`, and `ARCHITECTURE.md` with strict rules against `\_gitignore` naming and `.env` commits.



\### Problem: Idle GPU Burn



Manual pod management via RunPod UI led to $10–$25/day idle burn with no automated cost controls.



\### Fix: Production-Grade Orchestration



1\. \*\*RunPod API Client (`runpod\_api.py`)\*\*: Full pod lifecycle management via GraphQL API.

2\. \*\*Queue-Aware Autoscaler v2.2.1\*\*: Advanced scaling based on `queue\_length` + `inflight\_jobs`.

&#x20;  - \*\*Metrics\*\*: Real-time tracking of pending vs. processing jobs via Redis.

&#x20;  - \*\*Cost Control\*\*: `MAX\_PODS` cap and automatic idle termination after 300s.

&#x20;  - \*\*GPU Policy\*\*: Prefers cost-effective A40 GPUs with RTX 3090 fallback.



3\. \*\*Vercel \& Security Policy v2.2.1\*\*: Standardized environment and deployment policy.

&#x20;  - \*\*Double-Key Strategy\*\*: Implemented split Supabase keys (Anon for Frontend, Service Role for Worker).

&#x20;  - \*\*Stable Handshake\*\*: Transitioned to RunPod HTTP Proxy URLs to eliminate "Offline" blips from IP changes.

&#x20;  - \*\*Google One Tap Fix\*\*: Updated Google Cloud Console origins and redirect URIs for Vercel production.

4\. \*\*RunPod Fleet Migration (v2.2.1)\*\*: Successfully migrated to a high-performance pod cluster.

&#x20;  - \*\*New Pod ID\*\*: See private `INFRASTRUCTURE.md` (excluded from git).

&#x20;  - \*\*Connection Details\*\*: See private `INFRASTRUCTURE.md` — pod IPs and SSH keys are rotated on each deployment.

&#x20;  - \*\*Global Sync\*\*: Updated 12+ files across frontend, backend, and documentation to reflect the new pod infrastructure.

5\. \*\*Worker v2.2.1\*\*: Integrated with autoscaler metrics.

&#x20;  - \*\*Inflight Tracking\*\*: Increments `simhpc\_inflight` on job pop, decrements on completion.

&#x20;  - \*\*Activity Timestamping\*\*: Updates `pods:last\_used:{pod\_id}` in Redis for precise idle detection.

&#x20;  - \*\*GPU Acceleration\*\*: NVIDIA CUDA 12.1 + high-performance physics stack.

6\. \*\*Local Alpha Stack\*\*: Implemented `docker-compose.yml` for solo-founder rapid development.

7\. \*\*Admin \& Health API\*\*: 7 new protected endpoints in `api.py` for fleet and system health monitoring.

&#x20;  - `GET /api/v1/system/status` — Aggregated health check (Mercury, RunPod, Supabase, Worker).

&#x20;  - `GET /api/v1/admin/fleet` — Fleet status dashboard data.

&#x20;  - `GET /api/v1/admin/fleet/cost` — Cost tracking summary.

&#x20;  - `POST /api/v1/admin/fleet/pod/{id}/stop` — Stop pod.

8\. \*\*Security \& Connectivity\*\*:

&#x20;  - \*\*CORS Hardening\*\*: Added `simhpc.nexusbayarea.com` and `simhpc.com` to allowed origins.

&#x20;  - \*\*Production Redis Guard\*\*: Added validation to block `localhost` Redis usage in Vercel environments.

&#x20;  - \*\*Supabase Service Role\*\*: Standardized on `SUPABASE\_SERVICE\_ROLE\_KEY` for background writes.

9\. \*\*Infrastructure Updates\*\*:

&#x20;  - `Dockerfile.autoscaler` updated to include `runpod\_api.py`.

&#x20;  - `docker-compose.yml` autoscaler service updated with 10 additional env vars.



\---



\## Physics Worker: PDF Report Storage (March 23, 2026)



\### Problem: Raw Data Exposure



Simulation results were only available as raw JSON in the database, lacking professional engineering artifacts for export.



\### Fix: Automated Engineering Artifacts



1\. \*\*PDF Generation\*\*: Implemented a professional PDF report generator in `services/worker/pdf\_service.py` with Unicode support and numerical anchoring.

2\. \*\*Supabase Storage Integration\*\*:

&#x20;  - Added `upload\_pdf\_to\_supabase` to handle artifact persistence.

&#x20;  - Workers now upload generated PDFs to the `reports` bucket.

3\. \*\*Tiered Access Control\*\*:

&#x20;  - Implemented Public URLs for Free/Demo users.

&#x20;  - Implemented \*\*Signed URLs\*\* (1-hour expiration) for Professional/Enterprise users.

4\. \*\*Worker Workflow Update\*\*:

&#x20;  - `services/runpod-worker/worker.py` now triggers PDF generation and upload upon simulation completion.

&#x20;  - The `pdf\_url` is returned in the job result and synced to the `simulation\_history` table for instant frontend access.



\---



\## Toast Notification System Fix (March 18, 2026)



\### Problem: Silent Errors



The `<Toaster />` component from sonner was \*\*never mounted\*\* in the React tree. All 12 `toast()` calls were silently doing nothing.



\### Fix: Reactive Toast Notifications



1\. Created `src/App.tsx` with `<Toaster />` (6s default, 8s success, 10s error, cyan theme, rounded corners).

2\. Created `src/index.css` (toast CSS overrides) and `src/hooks/useSimulationUpdates.ts` (Supabase Realtime hook).

3\. Updated `Dashboard.tsx` to use `toast.promise()` pattern for simulation submissions.

4\. Created `src/components/SimulationDetailModal.tsx` — AI insights, physics metrics, PDF download.

5\. Created `src/pages/AdminAnalytics.tsx` — Admin Control at `/admin/analytics` with lead qualification.



\### Custom Domain \& First-Party Auth (March 18, 2026)



\- DNS: A `@ → 76.76.21.21`, CNAME `auth → \[project-ref].supabase.co`

\- Eliminates "Cookie Rejected" errors by making Supabase Auth first-party.

\- CORS hardened in `api.py` from `\["\*"]` to explicit allow-list.



\---



\## Frontend Deployment Diagnosis (March 18, 2026)



\### GitHub Pages vs Vercel Analysis



Console logs revealed that the GitHub Pages deployment fails while Vercel works due to:



1\. \*\*Environment Variable Injection\*\*: Vite requires `VITE\_SUPABASE\_URL` at build time.

2\. \*\*CSP Restrictions\*\*: `github.io` enforces strict CSP which blocks Stripe.js.

3\. \*\*Third-Party Cookie Blocks\*\*: Enhanced Tracking Protection on `github.io` blocks Supabase Auth.



\### Decision: Vercel Production Standard



\*\*Vercel retained as Production Primary.\*\* GitHub Pages remains as backup/staging with env var injection fix applied if needed.



\---



\### March 18, 2026 (SaaS Deployment \& Production Launch)



\- \*\*Frontend Deployment\*\*: Successfully pushed the finalized `v1.6.0-ALPHA` cockpit to `lostbobo.git`.

\- \*\*Production Status\*\*: SimHPC SaaS is LIVE at <https://simhpc.com>.

\- \*\*Conflict Resolution\*\*: Synchronized the frontend repository with the latest component updates.



\### March 16, 2026 (Mission Control Cockpit Redesign - v1.6.0)



\- \*\*Modular Component Architecture\*\*: Decoupled the Alpha Control Room into production-grade components: `TelemetryPanel`, `ActiveSimulations`, `SimulationLineage`, `OperatorConsole`, and `GuidanceEngine`.

\- \*\*Mercury AI Integration\*\*: Fully transitioned to Mercury AI for simulation assistance and notebook generation.

\- \*\*System Health LEDs\*\*: Real-time status indicators for Mercury AI, Supabase, and RunPod.





