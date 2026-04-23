"""Execution Diff Engine - Compare runs to detect changes."""


def diff_runs(prev, current):
    """Compare previous and current run to detect changes."""
    diff = []

    prev_map = {n["node"]: n for n in prev} if prev else {}

    for node in current:
        name = node["node"]
        prev_node = prev_map.get(name)

        diff.append(
            {
                "node": name,
                "name": node.get("name", name),
                "prev": prev_node["status"] if prev_node else "N/A",
                "current": node["status"],
                "changed": prev_node is not None and prev_node["status"] != node["status"],
                "prev_duration": prev_node.get("duration") if prev_node else None,
                "current_duration": node.get("duration"),
                "error": node.get("stderr", "")[:500] if node["status"] == "FAIL" else None,
            }
        )

    return diff


def summarize_diff(diff):
    """Return a human-readable summary of the diff."""
    lines = []
    for d in diff:
        marker = "❌" if d["changed"] else "✓"
        if d["changed"]:
            lines.append(f"  {marker} {d['node']}: {d['prev']} → {d['current']}")
        else:
            lines.append(f"  {marker} {d['node']}: {d['current']}")
    return "\n".join(lines)


def find_changed_nodes(diff):
    """Return nodes where status changed between runs."""
    return [d for d in diff if d["changed"]]


def detect_drift(diff):
    """Detect if there's unexpected drift between runs."""
    if not diff:
        return {"drift": False, "reason": "no data"}

    changed = find_changed_nodes(diff)

    if not changed:
        return {"drift": False, "reason": "no changes detected"}

    return {
        "drift": True,
        "changed_nodes": [d["node"] for d in changed],
        "count": len(changed),
    }
