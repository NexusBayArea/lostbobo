#!/usr/bin/env python3
"""DAG Execution Engine with caching."""

import json
import os
import subprocess
import sys
from hash import compute_node_key


CACHE_PATH = ".cache/dag_cache.json"


def load_cache():
    """Load cache from disk."""
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Persist cache to disk."""
    os.makedirs(".cache", exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def run_node(image, node):
    """Execute a single DAG node."""
    entry = node.get("entry", f"ci/jobs/{node['name']}.py")
    
    # Check if entry exists, fallback to module.py if needed (common in some repos)
    if not os.path.exists(entry) and not os.path.exists(entry.replace(".py", "")):
         # If it's a compute node but no specific script, maybe it's a generic run
         pass

    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.getcwd()}:/app",
            "-w",
            "/app",
            image,
            "python",
            entry,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    return {
        "node": node["name"],
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
        "inputs": node.get("inputs", [])
    }


def main(manifest_path):
    """Main DAG execution loop."""
    manifest = json.load(open(manifest_path))
    image = manifest["image"]["ref"]
    image_digest = manifest["image"]["digest"]
    dag_jobs = manifest.get("dag", {}).get("jobs", [])

    print(f"Image: {image}")
    print(f"Digest: {image_digest}")
    print(f"Jobs: {len(dag_jobs)}")

    cache = load_cache()
    new_cache = {}
    failures = []
    blocked_nodes = set()

    # Get compute nodes (renamed from jobs in previous step)
    dag_nodes = manifest.get("dag", {}).get("compute_nodes", [])
    if not dag_nodes:
        # Fallback to 'jobs' if compiler hasn't updated yet in production
        dag_nodes = manifest.get("dag", {}).get("jobs", [])

    for node in dag_nodes:
        node_name = node["name"]
        
        # Check if any dependency failed
        if any(dep in blocked_nodes for dep in node.get("deps", [])):
            print(f"BLOCKED {node_name} (upstream failure)")
            blocked_nodes.add(node_name)
            continue

        key = compute_node_key(node, cache, image_digest)

        if cache.get(node_name) == key:
            print(f"SKIP {node_name} (cache hit)")
            new_cache[node_name] = key
            continue

        print(f"RUN {node_name}...")
        res = run_node(image, node)
        
        if res["ok"]:
            print(f"PASS {node_name}")
            new_cache[node_name] = key
        else:
            print(f"FAIL {node_name}")
            failures.append(res)
            blocked_nodes.add(node_name)

    save_cache(new_cache)
    
    if failures:
        with open("failures.json", "w") as f:
            json.dump(failures, f, indent=2)
        print(f"Failure capture complete. {len(failures)} nodes failed.")
        sys.exit(1) # Final exit 1 to trigger CI failure step
    
    print(f"DAG Execution Successful. {len(new_cache)} nodes converged.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ci/kernel.py <manifest.json>")
        sys.exit(1)

    main(sys.argv[1])
