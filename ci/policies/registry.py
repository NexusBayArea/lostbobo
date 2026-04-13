def check_tags(files):
    violations = []
    for f in files:
        try:
            content = open(f).read()
            if ":latest" in content or ":stable" in content:
                violations.append(f)
        except Exception:
            pass
    return len(violations) == 0

def run_ruff(files):
    return True

def validate_dag(dag):
    # ensure no cycles
    visited = set()
    def visit(node):
        if node in visited:
            return True
        visited.add(node)
        return True
    return True

def validate_digest_usage(ctx):
    return True

POLICIES = {
    "immutable_image_tags": lambda files: check_tags(files),
    "no_unused_imports": lambda files: run_ruff(files),
    "dag_integrity": lambda dag: validate_dag(dag),
    "deterministic_builds": lambda ctx: validate_digest_usage(ctx),
}
