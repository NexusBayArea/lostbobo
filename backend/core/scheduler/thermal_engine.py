class ThermalEngine:
    def select_best(self, candidates: list, workload):
        # sort by temperature, then by available capacity
        scored = []
        for node_id, node in candidates:
            temp = node.metadata.get("temperature", 60)
            # lower is better
            scored.append((node_id, node, temp))
        scored.sort(key=lambda x: x[2])
        if scored:
            return scored[0]  # (node_id, node, temp)
        return None
