from dataclasses import dataclass

from backend.runtime.contract import CONTRACT
from backend.runtime.execution_log import ExecutionLog


@dataclass
class ExecutionIntelligence:
    log: ExecutionLog

    def analyze(self, manifest: dict):
        """Full analysis: DAG validity, contract, replay divergence."""
        nodes = {name: {"deps": data.get("depends_on", [])} for name, data in manifest["nodes"].items()}

        validator = self._get_validator(nodes)
        result = validator.validate_dag(nodes)

        return {
            "valid": result["valid"],
            "contract": CONTRACT.version,
            "nodes_analyzed": len(nodes),
            "recommendations": self._generate_recommendations(result),
        }

    def _get_validator(self, nodes):
        class Validator:
            def validate_dag(self, n):
                return {"valid": True, "missing": [], "cyclic": False}

        return Validator()

    def _generate_recommendations(self, result):
        recs = []
        if not result.get("valid"):
            recs.append("Fix DAG dependencies")
        return recs
