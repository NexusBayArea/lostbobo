import ast
from pathlib import Path

def remove_duplicate_functions(source: str) -> str:
    tree = ast.parse(source)
    seen = set()
    output = []
    
    # Keep track of function names to remove duplicates
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in seen:
                continue
            seen.add(node.name)
        output.append(node)
        
    return ast.unparse(ast.Module(body=output, type_ignores=[]))

def normalize_file(path: Path):
    try:
        source = path.read_text()
        normalized = remove_duplicate_functions(source)
        path.write_text(normalized)
    except Exception as e:
        print(f"Error normalizing {path}: {e}")
