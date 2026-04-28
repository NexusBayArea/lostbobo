#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git_changed_files():
    # Works for PR + push
    base = "origin/main"

    result = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def classify(files: list[str]) -> dict:
    flags = {
        "deps": False,
        "api": False,
        "runtime": False,
        "worker": False,
        "tools": False,
        "global": False,
    }

    for f in files:
        if f.endswith(".toml") or "requirements" in f:
            flags["deps"] = True

        elif f.startswith("backend/app/"):
            flags["api"] = True

        elif f.startswith("backend/runtime/"):
            flags["runtime"] = True

        elif f.startswith("backend/worker/"):
            flags["worker"] = True

        elif f.startswith("backend/tools/"):
            flags["tools"] = True

        else:
            flags["global"] = True  # unknown → safe fallback

    return flags


if __name__ == "__main__":
    files = git_changed_files()
    flags = classify(files)

    print("[CI] Changed files:")
    for f in files:
        print("  ", f)

    print("\n[CI] Flags:", flags)
