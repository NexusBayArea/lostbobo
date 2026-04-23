import ast
import os
import sys

import networkx as nx


class DependencyCompiler:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.graph = nx.DiGraph()

    def build_graph(self):
        """Scans the workspace to map imports."""
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    module = self._get_module_name(path)
                    self.graph.add_node(module)
                    self._extract_imports(path, module)

    def _get_module_name(self, path):
        clean_path = path.replace("\\", ".").replace("/", ".")
        return clean_path.replace(self.root_dir.replace("\\", "."), "backend").removesuffix(".py").strip(".")

    def _extract_imports(self, path, module):
        with open(path) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith(("backend", "skills")):
                        self.graph.add_edge(module, node.module)

    def validate(self):
        """Detects circular dependencies and calculates stability."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                print(f"❌ CIRCULAR DEPENDENCY DETECTED: {' -> '.join(cycles[0])}")
                return False
        except Exception as e:
            print(f"ℹ Could not run cycle detection: {e}")

        print("\n[Module Stability Scores]")
        for node in self.graph.nodes:
            in_d = self.graph.in_degree(node)
            out_d = self.graph.out_degree(node)
            score = out_d / (in_d + out_d) if (in_d + out_d) > 0 else 0
            status = "STABLE" if score < 0.5 else "VOLATILE"
            print(f" - {node}: {score:.2f} ({status})")

        return True


if __name__ == "__main__":
    compiler = DependencyCompiler("backend")
    compiler.build_graph()
    if not compiler.validate():
        sys.exit(1)
