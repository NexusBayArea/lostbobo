import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

SAFE_FIXES = {
    "missing_dependency",
    "lockfile_drift",
    "missing_dev_dependency",
    "pytest_missing",
}


def apply_fix(failure: Dict[str, Any], repo_path: Path, dry_run: bool = True) -> Dict[str, Any]:
    fix_type = failure.get("type")

    if fix_type not in SAFE_FIXES:
        return {
            "applied": False,
            "reason": f"Unsafe fix type: {fix_type}",
            "requires_manual": True,
        }

    result = {
        "applied": False,
        "fix_type": fix_type,
        "command": "",
    }

    if fix_type == "missing_dependency":
        result = _fix_missing_dependency(failure, repo_path, dry_run)
    elif fix_type == "lockfile_drift":
        result = _fix_lockfile_drift(repo_path, dry_run)
    elif fix_type in ("missing_dev_dependency", "pytest_missing"):
        result = _fix_dev_dependency(failure, repo_path, dry_run)

    return result


def _fix_missing_dependency(failure: Dict[str, Any], repo_path: Path, dry_run: bool) -> Dict[str, Any]:
    module = failure.get("module", "unknown")
    pyproject = repo_path / "backend" / "pyproject.toml"

    if not pyproject.exists():
        return {"applied": False, "reason": "pyproject.toml not found"}

    result = {
        "applied": False,
        "module": module,
        "fix_type": "missing_dependency",
    }

    if not dry_run:
        with open(pyproject, "r") as f:
            content = f.read()

        if module not in content:
            with open(pyproject, "a") as f:
                f.write(f'\n{module} = "*"\n')

            subprocess.run(
                "cd backend && uv pip compile pyproject.toml -o requirements.api.lock",
                shell=True,
                cwd=repo_path,
                capture_output=True,
            )

            result["applied"] = True
            result["command"] = f"Added {module} to pyproject.toml and rebuilt lockfile"
        else:
            result["applied"] = True
            result["command"] = f"Module {module} already in pyproject.toml, just rebuild lockfile"
            subprocess.run(
                "cd backend && uv pip compile pyproject.toml -o requirements.api.lock",
                shell=True,
                cwd=repo_path,
                capture_output=True,
            )

    return result


def _fix_lockfile_drift(repo_path: Path, dry_run: bool) -> Dict[str, Any]:
    result = {
        "applied": False,
        "fix_type": "lockfile_drift",
    }

    if not dry_run:
        subprocess.run(
            "cd backend && uv pip compile pyproject.toml -o requirements.api.lock",
            shell=True,
            cwd=repo_path,
            capture_output=True,
        )
        result["applied"] = True
        result["command"] = "Rebuilt requirements.api.lock"

    return result


def _fix_dev_dependency(failure: Dict[str, Any], repo_path: Path, dry_run: bool) -> Dict[str, Any]:
    dep = "pytest"
    pyproject = repo_path / "backend" / "pyproject.toml"

    result = {
        "applied": False,
        "dependency": dep,
        "fix_type": "missing_dev_dependency",
    }

    if not dry_run:
        with open(pyproject, "r") as f:
            content = f.read()

        if dep not in content:
            with open(pyproject, "a") as f:
                f.write(f'\n{dep} = "*"\n')

            subprocess.run(
                "cd backend && uv pip compile pyproject.toml -o requirements.dev.lock",
                shell=True,
                cwd=repo_path,
                capture_output=True,
            )

            result["applied"] = True
            result["command"] = f"Added {dep} to pyproject.toml and rebuilt dev lockfile"

    return result


def sandbox_fix(failure: Dict[str, Any], repo_root: str) -> Dict[str, Any]:
    repo_path = Path(repo_root)

    if failure.get("type") not in SAFE_FIXES:
        return {
            "applied": False,
            "reason": f"Fix type {failure.get('type')} not in safe list",
        }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_copy = tmp_path / "repo"

        shutil.copytree(repo_path, repo_copy, dirs_exist_ok=True)

        fix_result = apply_fix(failure, repo_copy, dry_run=False)

        if not fix_result.get("applied"):
            return fix_result

        changed = list(repo_copy.rglob("*.lock")) + list(repo_copy.rglob("pyproject.toml"))
        changes = []
        for f in changed:
            orig = repo_path / f.relative_to(repo_copy)
            if orig.exists():
                with open(f) as new_f, open(orig) as orig_f:
                    if new_f.read() != orig_f.read():
                        changes.append(str(f.relative_to(repo_copy)))

        return {
            "applied": True,
            "changes": changes,
            "sandbox_path": str(repo_copy),
            "fix_command": fix_result.get("command", ""),
        }


def generate_patch(original: Path, modified: Path) -> Optional[str]:
    result = subprocess.run(
        ["git", "diff", "--no-color"],
        capture_output=True,
        text=True,
        cwd=modified,
    )
    return result.stdout if result.stdout else None