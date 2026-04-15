def merge_graphs(*graphs: dict):
    merged = {"nodes": {}, "edges": []}

    for g in graphs:
        for node, data in g.items():
            merged["nodes"][node] = data

            for imp in data["imports"]:
                merged["edges"].append([node, imp])

    return merged
