import os
import subprocess
from ci.diagnose import diagnose
from ci.autofix import generate_patch

def apply_patch(patch):
    """Executes a controlled mutation on the codebase to fix a CI failure."""
    if not patch:
        return False

    print(f"Applying patch: {patch['type']} -> {patch['action']}")

    try:
        if patch["type"] == "format_patch":
            subprocess.run(["uv", "run", "ruff", "check", ".", "--fix"], check=False)
            subprocess.run(["uv", "run", "ruff", "format", "."], check=False)
            return True

        if patch["type"] == "dependency_patch":
            # Re-generate lockfile
            subprocess.run(["uv", "pip", "compile", "pyproject.toml", "-o", "requirements.lock"], check=True)
            return True
            
        if patch["type"] == "code_patch":
            # For now, we might trigger a specific repair script if it exists
            # or just log that we need manual intervention for complex code fixes
            return False
            
    except Exception as e:
        print(f"Failed to apply patch: {e}")
        return False

    return False

def self_heal(failures):
    """The core healing loop: diagnose -> patch -> apply."""
    fix_count = 0
    for f in failures:
        diagnosis = diagnose(f)
        patch = generate_patch(f, diagnosis)
        if patch:
            if apply_patch(patch):
                fix_count += 1
    
    return fix_count
