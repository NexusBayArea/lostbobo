from pathlib import Path

import structlog
import yaml

from backend.core.supabase_job_store import SupabaseJobStore

log = structlog.get_logger(__name__)


class Manifest:
    def __init__(self, data: dict, path: str):
        self.path = path
        self.scope = data.get("scope", "")
        self.purpose = data.get("purpose", "")
        self.always_load = data.get("always_load", [])
        self.load_on_demand = data.get("load_on_demand", [])
        self.dependencies = data.get("dependencies", [])
        self.critical_paths = data.get("critical_paths", [])
        self.forbidden = data.get("forbidden_operations", [])


class ManifestRegistry:
    """Kernel-centered manifest index (stored in Supabase)."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.manifests: dict[str, Manifest] = {}

    async def load_all(self):
        """Scan project and index all MANIFEST.md files"""
        for manifest_path in Path(".").rglob("MANIFEST.md"):
            try:
                content = manifest_path.read_text()
                # Parse YAML frontmatter
                if "---" in content:
                    parts = content.split("---", 2)
                    if len(parts) >= 2:
                        data = yaml.safe_load(parts[1])
                        manifest = Manifest(data, str(manifest_path))
                        self.manifests[str(manifest_path)] = manifest

                        # Persist to Supabase
                        await self.supabase.record_event(
                            "manifest_indexed",
                            {
                                "path": str(manifest_path),
                                "scope": manifest.scope,
                                "critical_paths": manifest.critical_paths,
                            },
                        )
            except Exception as e:
                log.warning("failed to parse manifest", path=manifest_path, error=str(e))

    async def traverse(self, query: str, domain: str = None) -> list[Manifest]:
        """Hierarchical manifest traversal for context routing"""
        relevant = []
        for path, manifest in self.manifests.items():
            if domain and domain in path.lower():
                relevant.append(manifest)
            elif any(kw in query.lower() for kw in manifest.scope.lower().split()):
                relevant.append(manifest)
        return sorted(relevant, key=lambda m: len(m.critical_paths), reverse=True)
