"""Root Cause Analyzer - Identify failure origin and suggest fixes."""
import re


FAILURE_PATTERNS = {
    "modulenotfounderror": {
        "hint": "missing dependency or broken import boundary",
        "fix": "Check requirements.txt lockfile sync",
    },
    "importerror": {
        "hint": "import chain broken - check installed packages",
        "fix": "Run env_bootstrap.py ci to sync dependencies",
    },
    "no module named": {
        "hint": "dependency not in lockfile or virtualenv",
        "fix": "Sync requirements with lockfile",
    },
    "pytest": {
        "hint": "test environment not installed correctly",
        "fix": "pip install pytest pytest-asyncio",
    },
    "syntaxerror": {
        "hint": "invalid Python syntax",
        "fix": "Check Python version compatibility",
    },
    "indentationerror": {
        "hint": "indentation mismatch",
        "fix": "Run ruff format . to fix",
    },
    "nameerror": {
        "hint": "undefined name - check imports and definitions",
        "fix": "Add missing import or define the name",
    },
    "attributeerror": {
        "hint": "object has no attribute - check API version",
        "fix": "Verify runtime contract version",
    },
    "connection refused": {
        "hint": "service not running or port mismatch",
        "fix": "Check SB_URL and SB_DATA_URL in env",
    },
    "timeout": {
        "hint": "service too slow or unresponsive",
        "fix": "Increase timeout or check service health",
    },
    "permission denied": {
        "hint": "file/directory permission issue",
        "fix": "Check file permissions",
    },
    "file not found": {
        "hint": "missing file or wrong path",
        "fix": "Verify file paths in config",
    },
    "i001": {
        "hint": "imports not sorted (run ruff check . --select I --fix)",
        "fix": "python -m ruff check . --select I --fix",
    },
    "up006": {
        "hint": "legacy typing syntax - use built-in generics",
        "fix": "python -m ruff check . --fix",
    },
    "up007": {
        "hint": "legacy typing - use X | Y union syntax",
        "fix": "python -m ruff check . --fix",
    },
    "up035": {
        "hint": "deprecated typing imports (Set/Dict/List)",
        "fix": "python -m ruff check . --fix",
    },
    "f401": {
        "hint": "unused import - remove or prefix with _",
        "fix": "python -m ruff check . --fix",
    },
    "f841": {
        "hint": "unused variable - remove or prefix with _",
        "fix": "python -m ruff check . --fix",
    },
}


def find_root_failure(trace):
    """Find the first failing node in a trace."""
    for node in trace:
        if node["status"] == "FAIL":
            return {
                "root_node": node["node"],
                "name": node.get("name", node["node"]),
                "error": node.get("stderr", "")[:500],
                "cmd": node["cmd"],
                "hint": infer_hint(node),
                "fix": get_fix_suggestion(node),
            }
    return None


def infer_hint(node):
    """Analyze error and return actionable hint."""
    err = (node.get("stderr", "") + node.get("stdout", "")).lower()
    
    for pattern, info in FAILURE_PATTERNS.items():
        if pattern in err:
            return info["hint"]
    
    return "unknown failure pattern"


def get_fix_suggestion(node):
    """Get suggested fix for the failing node."""
    err = (node.get("stderr", "") + node.get("stdout", "")).lower()
    
    for pattern, info in FAILURE_PATTERNS.items():
        if pattern in err:
            return info.get("fix")
    
    return None


def extract_error_type(stderr):
    """Extract the Python exception type from stderr."""
    match = re.search(r"(\w+Error|\w+Exception):", stderr)
    return match.group(1) if match else "UnknownError"


def analyze_failure_chain(trace):
    """Analyze the full failure chain."""
    failures = [n for n in trace if n["status"] == "FAIL"]
    
    if not failures:
        return {"status": "pass", "failures": []}
    
    return {
        "status": "fail",
        "count": len(failures),
        "first_failure": failures[0],
        "all_failures": failures,
    }