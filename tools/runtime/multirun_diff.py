def diff_runs(run_a, run_b):
    map_a = {n["node_id"]: n for n in run_a}
    map_b = {n["node_id"]: n for n in run_b}

    diff = {}
    all_nodes = set(map_a) | set(map_b)

    for nid in all_nodes:
        a = map_a.get(nid)
        b = map_b.get(nid)

        if not a:
            diff[nid] = "added"
            continue
        if not b:
            diff[nid] = "removed"
            continue

        if a["contract"] != b["contract"]:
            diff[nid] = "changed"
        else:
            diff[nid] = "unchanged"

    return diff
