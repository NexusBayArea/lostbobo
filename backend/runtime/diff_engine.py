def diff_runs(a: dict, b: dict):
    result = []

    nodes_a = {n["id"]: n for n in a.get("nodes", [])}
    nodes_b = {n["id"]: n for n in b.get("nodes", [])}

    all_ids = set(nodes_a) | set(nodes_b)

    for nid in all_ids:
        na = nodes_a.get(nid)
        nb = nodes_b.get(nid)

        if not na or not nb:
            result.append({"node": nid, "type": "added_or_removed"})
            continue

        if na["status"] != nb["status"]:
            result.append({"node": nid, "type": "status_change", "from": na["status"], "to": nb["status"]})

        if abs(na["duration"] - nb["duration"]) > 0.01:
            result.append({"node": nid, "type": "duration_change", "delta": nb["duration"] - na["duration"]})

    return result
