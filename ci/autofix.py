def generate_patch(failure, diagnosis):
    """Maps a diagnosis to a concrete auto-fix patch proposal."""
    if diagnosis == "fix_import":
        # Strategy: attempt to restore missing imports or fix order
        return {
            "type": "code_patch",
            "action": "add_missing_import_or_dependency",
            "node": failure["node"]
        }

    if diagnosis == "fix_dependency":
        # Strategy: sync lockfile with pyproject.toml
        return {
            "type": "dependency_patch",
            "action": "update_pyproject_or_lockfile",
            "node": failure["node"]
        }

    if diagnosis == "fix_style":
        # Strategy: run formatter
        return {
            "type": "format_patch",
            "action": "ruff --fix",
            "node": failure["node"]
        }

    return None
