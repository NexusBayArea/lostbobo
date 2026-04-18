def validate_contract(contract: dict) -> None:
    if not isinstance(contract, dict):
        raise RuntimeError("contract must be dict")

    if "nodes" not in contract:
        raise RuntimeError("missing nodes")

    nodes = contract["nodes"]

    if not isinstance(nodes, dict):
        raise RuntimeError("nodes must be dict")

    for name, node in nodes.items():
        if "path" not in node:
            raise RuntimeError(f"{name}: missing path")
        if "depends_on" not in node:
            raise RuntimeError(f"{name}: missing depends_on")
