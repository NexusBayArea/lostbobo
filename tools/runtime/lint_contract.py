from dataclasses import dataclass


@dataclass
class LintRule:
    code: str
    description: str
    severity: str  # "error" | "warning"


class LintContract:
    def __init__(self):
        self.rules: dict[str, LintRule] = {
            "E402": LintRule(
                code="E402",
                description="imports must be top-level or explicitly declared as lazy imports",
                severity="error",
            ),
            "F401": LintRule(
                code="F401",
                description="unused imports must be explicitly declared as side-effect imports",
                severity="error",
            ),
        }

    def validate_import_policy(self, bootstrap_imports: list[str]) -> list[str]:
        violations = []

        for imp in bootstrap_imports:
            if imp.startswith("lazy:"):
                continue
            if imp.startswith("side_effect:"):
                continue
            violations.append(imp)

        return violations


LINT_CONTRACT = LintContract()
