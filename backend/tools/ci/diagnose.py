import json
import re
from typing import Dict, Any, Optional


FIX_COMMANDS = {
    "missing_dependency": "cd backend && uv pip compile pyproject.toml -o requirements.api.lock",
    "missing_dev_dependency": "cd backend && uv pip compile pyproject.toml -o requirements.dev.lock",
    "lockfile_drift": "cd backend && uv pip compile pyproject.toml -o requirements.api.lock",
    "import_boundary_violation": "Check backend imports: use app.X for local package, runtime.X for backend/runtime",
    "pytest_missing": "cd backend && uv pip install -r requirements.dev.lock",
}


def classify(log: str) -> Dict[str, Any]:
    log_lower = log.lower()
    full_log = log

    if "modulenotfounderror" in log_lower or "no module named" in log_lower:
        match = re.search(r"No module named '([^']+)'", log)
        module = match.group(1) if match else "unknown"

        return {
            "type": "missing_dependency",
            "module": module,
            "fix": FIX_COMMANDS["missing_dependency"],
            "confidence": 0.95,
        }

    if "pytest: command not found" in log_lower or "pytest: not found" in log_lower:
        return {
            "type": "missing_dev_dependency",
            "fix": FIX_COMMANDS["pytest_missing"],
            "confidence": 0.98,
        }

    if "differ" in log_lower and "lock" in log_lower:
        return {
            "type": "lockfile_drift",
            "fix": FIX_COMMANDS["lockfile_drift"],
            "confidence": 0.95,
        }

    if "import boundary violations" in log_lower:
        return {
            "type": "import_boundary_violation",
            "fix": FIX_COMMANDS["import_boundary_violation"],
            "confidence": 0.9,
        }

    if "modulenotfounderror" in log_lower and "backend" in log_lower:
        return {
            "type": "module_not_in_path",
            "fix": "Ensure PYTHONPATH includes backend directory",
            "confidence": 0.85,
        }

    if "ruff" in log_lower and ("not found" in log_lower or "command not found" in log_lower):
        return {
            "type": "missing_linter",
            "fix": "pip install ruff",
            "confidence": 0.98,
        }

    if "error" in log_lower and "import" in log_lower:
        import_match = re.search(r"ImportError: (.+?)(?:\n|$)", log)
        error_detail = import_match.group(1) if import_match else "unknown"
        return {
            "type": "import_error",
            "detail": error_detail,
            "fix": "Check module availability in installed packages",
            "confidence": 0.7,
        }

    return {
        "type": "unknown",
        "fix": "Inspect logs manually",
        "confidence": 0.3,
    }


def diagnose(log: str) -> Dict[str, Any]:
    result = classify(log)
    result["suggested_command"] = result.get("fix", "")
    return result


def save_failure(diagnosis: Dict[str, Any], path: str = "ci_failure.json"):
    with open(path, "w") as f:
        json.dump(diagnosis, f, indent=2)


def load_failure(path: str = "ci_failure.json") -> Optional[Dict[str, Any]]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def format_diagnosis(diagnosis: Dict[str, Any]) -> str:
    if not diagnosis:
        return "No diagnosis available"

    lines = ["", "--- AUTO DIAGNOSIS ---"]
    for key, value in diagnosis.items():
        lines.append(f"{key}: {value}")

    return "\n".join(lines)