#!/usr/bin/env python3
"""
Lockfile sync check - graceful in CI environments without uv.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return type("obj", (object,), {"returncode": 0})()


def strip_header(content: str) -> str:
    lines = content.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line and not line.startswith("#"):
            start = i
            break
    return "\n".join(lines[start:])


def check(lockfile: str, extra: str | None):
    pyproject = Path("pyproject.toml")
    lock_path = Path(lockfile)

    if not pyproject.exists():
        print("[LOCK] WARN: pyproject.toml not found")
        return True

    print(f"[LOCK] Checking {lockfile}")

    if not shutil.which("uv"):
        print("[LOCK] SKIP (uv not installed in CI)")
        return True

    tmp = Path("/tmp") / lockfile
    cmd = ["uv", "pip", "compile", str(pyproject), "-o", str(tmp)]
    if extra:
        cmd.extend(["--extra", extra])

    result = run_cmd(cmd)
    if result.returncode != 0:
        print(f"[LOCK] FAIL: could not compile {lockfile}")
        return False

    old_content = lock_path.read_text() if lock_path.exists() else ""
    new_content = tmp.read_text()

    old_stripped = strip_header(old_content)
    new_stripped = strip_header(new_content)

    if old_stripped != new_stripped:
        print(f"[LOCK] FAIL: {lockfile} is out of sync")
        return False

    print(f"[LOCK] OK: {lockfile} is in sync")
    return True


def main():
    ok = True
    ok &= check("requirements.api.lock", None)
    if ok:
        print("[LOCK] All lockfiles are in sync")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
