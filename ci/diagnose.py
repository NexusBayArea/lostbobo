def diagnose(failure):
    """Classifies the root cause of a node failure based on stderr/logs."""
    stderr = failure.get("stderr", "")
    error_type = failure.get("error_type", "")

    if "ImportError" in stderr or "ImportError" in error_type:
        return "fix_import"

    if "ModuleNotFoundError" in stderr:
        return "fix_dependency"

    if "lint" in error_type.lower() or "ruff" in stderr.lower():
        return "fix_style"

    if "Dockerfile" in stderr or "docker" in error_type.lower():
        return "fix_docker"

    return "unknown"
