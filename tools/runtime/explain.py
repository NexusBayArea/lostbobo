def explain(node_id, plan, prev_contracts, contracts, lineage):
    reasons = []

    if prev_contracts.get(node_id) != contracts.get(node_id):
        reasons.append("contract_changed")

    for dep in lineage[node_id]["deps"]:
        if prev_contracts.get(dep) != contracts.get(dep):
            reasons.append(f"upstream_changed:{dep}")

    if not reasons:
        reasons.append("no_change (reused)")

    return reasons


def diff_inputs(old, new):
    changes = {}
    keys = set(old.keys()) | set(new.keys())
    for k in keys:
        if old.get(k) != new.get(k):
            changes[k] = {
                "before": old.get(k),
                "after": new.get(k),
            }
    return changes


def build_reverse_graph(nodes):
    children = {}
    for n in nodes:
        for d in n.get("deps", []):
            children.setdefault(d, []).append(n["id"])
    return children


def get_downstream(node_id, children):
    result = set()
    stack = [node_id]
    while stack:
        cur = stack.pop()
        for c in children.get(cur, []):
            if c not in result:
                result.add(c)
                stack.append(c)
    return result


def build_report(nodes, plan, prev_contracts, contracts, lineage):
    report = {}
    for n in nodes:
        nid = n["id"]
        report[nid] = {
            "will_run": nid in plan["dirty"],
            "reason": explain(nid, plan, prev_contracts, contracts, lineage),
        }
    return report
