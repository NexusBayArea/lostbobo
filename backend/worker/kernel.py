def run_mfem(node: dict):
    # This will be replaced by actual solver execution logic
    print(f"Executing MFEM solver: {node.get('solver')} on mesh: {node.get('mesh')}")
    # Placeholder: Simulate solver process
    return {"status": "ok", "solver": node.get("solver"), "mesh": node.get("mesh")}


def execute_node(node: dict):
    if node.get("type") == "mfem.solve":
        return run_mfem(node)
    raise ValueError(f"Unknown node type: {node.get('type')}")
