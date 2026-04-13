TEMPLATES = {
    "ImportError": {
        "action": "install_package",
        "cmd": ["uv", "pip", "install", "-e", "."],
        "desc": "Local package import resolution"
    },
    "ModuleNotFoundError": {
        "action": "dependency_fix",
        "cmd": ["uv", "pip", "compile", "pyproject.toml", "-o", "requirements.lock"],
        "desc": "Lockfile dependency sync"
    },
    "ruff": {
        "action": "lint_fix",
        "cmd": ["uv", "run", "ruff", "check", ".", "--fix"],
        "desc": "Automated style compliance"
    },
    "syntax": {
        "action": "syntax_gate",
        "cmd": None, # Requires human or LLM intervention
        "desc": "Syntax error detection"
    }
}

def get_template_for_signature(signature):
    """Matches a signature against known fix templates."""
    for key, template in TEMPLATES.items():
        if key in signature:
            return template
    return None
