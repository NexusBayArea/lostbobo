"""Targeted Fix Engine - Node-scoped fix proposals based on root cause."""
import re
import subprocess
import json
from pathlib import Path


FIX_STRATEGIES = {
    "modulenotfounderror": {
        "action": "add_dependency",
        "extract": "module",
        "command": "uv pip compile pyproject.toml -o requirements.api.lock",
        "description": "Add missing dependency to lockfile",
    },
    "no module named": {
        "action": "add_dependency",
        "extract": "module",
        "command": "uv pip compile pyproject.toml -o requirements.api.lock",
        "description": "Add missing dependency to lockfile",
    },
    "i001": {
        "action": "fix_imports",
        "extract": None,
        "command": "python -m ruff check . --select I --fix",
        "description": "Fix import ordering",
    },
    "importerror": {
        "action": "fix_import",
        "extract": None,
        "command": "python tools/ci_gates/import_guard.py",
        "description": "Fix import boundary issue",
    },
    "pytest not found": {
        "action": "install_dev_deps",
        "extract": None,
        "command": "pip install pytest pytest-asyncio ruff",
        "description": "Install dev dependencies",
    },
    "syntaxerror": {
        "action": "format_code",
        "extract": None,
        "command": "ruff format .",
        "description": "Format code with ruff",
    },
    "indentationerror": {
        "action": "format_code",
        "extract": None,
        "command": "ruff format .",
        "description": "Fix indentation with ruff",
    },
    "nameerror": {
        "action": "check_definitions",
        "extract": "name",
        "command": None,
        "description": "Check for undefined name",
    },
    "attributeerror": {
        "action": "check_api_version",
        "extract": "attribute",
        "command": None,
        "description": "Check API version compatibility",
    },
    "connection refused": {
        "action": "check_service",
        "extract": None,
        "command": None,
        "description": "Check service configuration",
    },
}


def extract_module(error: str):
    """Extract module name from error message."""
    patterns = [
        r"named '(.+?)'",
        r"No module named '(.+?)'",
        r"module '(.+?)'",
    ]
    for pattern in patterns:
        m = re.search(pattern, error)
        if m:
            return m.group(1)
    return None


def extract_name(error: str):
    """Extract undefined name from error."""
    m = re.search(r"NameError: name '(\w+)'", error)
    return m.group(1) if m else None


def extract_attribute(error: str):
    """Extract missing attribute from error."""
    m = re.search(r"'(\w+)' object has no attribute", error)
    return m.group(1) if m else None


def get_fix_strategy(error: str):
    """Match error to fix strategy."""
    error_lower = error.lower()
    
    for pattern, strategy in FIX_STRATEGIES.items():
        if pattern in error_lower:
            return strategy
    
    return None


def propose_fix(root_cause: dict) -> dict:
    """Propose targeted fix based on root cause analysis."""
    error = (root_cause.get("error") or "").lower()
    node = root_cause.get("root_node")
    
    strategy = get_fix_strategy(error)
    
    if not strategy:
        return {
            "action": "manual_review",
            "reason": "unclassified failure",
            "node": node,
            "error": error,
        }
    
    extracted = None
    if strategy.get("extract") == "module":
        extracted = extract_module(root_cause.get("error", ""))
    elif strategy.get("extract") == "name":
        extracted = extract_name(root_cause.get("error", ""))
    elif strategy.get("extract") == "attribute":
        extracted = extract_attribute(root_cause.get("error", ""))
    
    return {
        "action": strategy["action"],
        "command": strategy.get("command"),
        "description": strategy["description"],
        "extracted": extracted,
        "node": node,
        "error": error,
    }


def generate_fix_script(fix: dict, workspace: str = ".") -> str:
    """Generate shell script for applying fix."""
    if not fix.get("command"):
        return f"# No command for action: {fix['action']}"
    
    return f"""#!/bin/bash
# Auto-generated fix script
set -e
cd {workspace}
{fix['command']}
echo "Fix applied: {fix.get('description')}"
"""


def validate_fix(fix: dict) -> bool:
    """Check if fix is valid and applicable."""
    if fix["action"] == "manual_review":
        return False
    if not fix.get("command"):
        return False
    return True


def get_fix_confidence(fix: dict) -> float:
    """Estimate fix confidence (0.0 - 1.0)."""
    high_confidence_actions = {
        "add_dependency": 0.8,
        "install_dev_deps": 0.9,
        "format_code": 0.95,
        "fix_imports": 0.9,
        "fix_import": 0.7,
    }
    
    return high_confidence_actions.get(fix.get("action"), 0.3)