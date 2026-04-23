"""Sandbox Fix Validator - Apply and validate fixes in isolated workspace."""
import tempfile
import shutil
import subprocess
import sys
import os
import json
from pathlib import Path
from backend.tools.ci.fix_engine import propose_fix, validate_fix, generate_fix_script


def copy_repo_to_sandbox(repo_path: str, sandbox_path: str):
    """Copy repo to sandbox directory."""
    if os.path.exists(sandbox_path):
        shutil.rmtree(sandbox_path)
    shutil.copytree(repo_path, sandbox_path)
    print(f"[SANDBOX] Copied repo to {sandbox_path}")


def apply_fix_in_sandbox(fix: dict, sandbox_path: str) -> bool:
    """Apply fix in sandbox workspace."""
    if not fix.get("command"):
        print(f"[SANDBOX] No command for action: {fix['action']}")
        return False
    
    print(f"[SANDBOX] Applying: {fix['command']}")
    
    result = subprocess.run(
        fix["command"],
        shell=True,
        cwd=sandbox_path,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"[SANDBOX] Fix failed: {result.stderr[:500]}")
        return False
    
    print(f"[SANDBOX] Fix applied successfully")
    return True


def run_ci_in_sandbox(sandbox_path: str) -> bool:
    """Run CI in sandbox workspace."""
    print(f"[SANDBOX] Running CI replay...")
    
    result = subprocess.run(
        "python tools/run_ci.py",
        shell=True,
        cwd=sandbox_path,
        capture_output=True,
        text=True,
        timeout=300,
    )
    
    if result.returncode == 0:
        print(f"[SANDBOX] CI passed in sandbox")
        return True
    
    print(f"[SANDBOX] CI failed in sandbox: {result.stderr[:500]}")
    return False


def apply_and_validate(root_cause: dict, repo_path: str = None) -> dict:
    """Apply fix in sandbox and validate with CI replay."""
    repo_path = repo_path or "."
    
    fix = propose_fix(root_cause)
    print(f"\n[FIX PROPOSED]")
    print(f"  Action: {fix.get('action')}")
    print(f"  Description: {fix.get('description')}")
    print(f"  Command: {fix.get('command')}")
    
    if not validate_fix(fix):
        print(f"[SANDBOX] Fix requires manual review")
        return {
            "status": "NO_FIX",
            "fix": fix,
            "reason": "requires manual review",
        }
    
    with tempfile.TemporaryDirectory() as tmp:
        sandbox_path = os.path.join(tmp, "repo")
        
        copy_repo_to_sandbox(repo_path, sandbox_path)
        
        if not apply_fix_in_sandbox(fix, sandbox_path):
            return {
                "status": "FIX_APPLY_FAILED",
                "fix": fix,
            }
        
        if not run_ci_in_sandbox(sandbox_path):
            return {
                "status": "FIX_VALIDATION_FAILED",
                "fix": fix,
            }
        
        return {
            "status": "FIX_VERIFIED",
            "fix": fix,
            "sandbox": sandbox_path,
        }


def apply_batch(root_causes: list, repo_path: str = None) -> dict:
    """Apply fixes sequentially and validate."""
    repo_path = repo_path or "."
    
    results = []
    for root_cause in root_causes:
        result = apply_and_validate(root_cause, repo_path)
        results.append(result)
        
        if result["status"] != "FIX_VERIFIED":
            print(f"[BATCH] Fix failed at {root_cause.get('root_node')}")
            break
    
    all_passed = all(r["status"] == "FIX_VERIFIED" for r in results)
    
    return {
        "status": "ALL_FIXED" if all_passed else "PARTIAL_FIX",
        "results": results,
    }


def create_fix_script(fix: dict, path: str, workspace: str = "."):
    """Generate fix script file."""
    script = generate_fix_script(fix, workspace)
    
    with open(path, "w") as f:
        f.write(script)
    
    os.chmod(path, 0o755)
    print(f"[FIX SCRIPT] Created {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_fix.py <ci_trace.json>")
        sys.exit(1)
    
    trace_path = sys.argv[1]
    
    with open(trace_path) as f:
        trace = json.load(f)
    
    from backend.tools.ci.root_cause import find_root_failure
    
    root = find_root_failure(trace)
    if root:
        result = apply_and_validate(root)
        print(f"\n[RESULT] {result['status']}")
    else:
        print("[ERROR] No root cause found")