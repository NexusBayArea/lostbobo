def validate_manifest(manifest: dict):
    nodes = manifest["nodes"]
    for src, data in nodes.items():
        for imp in data["imports"]:
            if imp not in nodes:
                raise ImportError(f"Broken import detected: {src} -> {imp}")
