from tools.runtime.contract import compute_contract
from tools.runtime.trace import load


def build_index(nodes):
    by_id = {n["id"]: n for n in nodes}
    children = {n["id"]: [] for n in nodes}

    for n in nodes:
        for d in n.get("deps", []):
            if d in children:
                children[d].append(n["id"])

    return by_id, children


def compute_all_contracts(nodes):
    return {n["id"]: compute_contract(n) for n in nodes}


def load_previous_contracts(nodes, workspace):
    prev = {}
    for n in nodes:
        t = load(n["id"], workspace)
        prev[n["id"]] = t["contract"] if t else None
    return prev


def compute_dirty(nodes, contracts, prev_contracts):
    dirty = set()
    for nid, contract in contracts.items():
        if prev_contracts.get(nid) != contract:
            dirty.add(nid)
    return dirty


def propagate_dirty(dirty, children):
    queue = list(dirty)
    while queue:
        nid = queue.pop(0)
        for child in children.get(nid, []):
            if child not in dirty:
                dirty.add(child)
                queue.append(child)
    return dirty


def topological_sort(nodes):
    visited = set()
    order = []
    by_id = {n["id"]: n for n in nodes}

    def visit(nid):
        if nid in visited:
            return
        for d in by_id[nid].get("deps", []):
            visit(d)
        visited.add(nid)
        order.append(nid)

    for n in nodes:
        visit(n["id"])
    return order


def plan_execution(nodes, workspace):
    by_id, children = build_index(nodes)
    contracts = compute_all_contracts(nodes)
    prev_contracts = load_previous_contracts(nodes, workspace)

    dirty = compute_dirty(nodes, contracts, prev_contracts)
    dirty = propagate_dirty(dirty, children)

    return {"contracts": contracts, "dirty": dirty, "ordered": topological_sort(nodes)}
