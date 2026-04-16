class ReplayEngine:
    def __init__(self, log):
        self.log = log

    def replay(self):
        return [
            {
                "node": entry["node"],
                "result": entry["result"],
                "deps": entry.get("deps", {}),
            }
            for entry in self.log
        ]
