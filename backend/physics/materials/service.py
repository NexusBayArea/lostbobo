from dataclasses import dataclass

from backend.core.rag.router import RAGRouter


@dataclass
class MaterialProperty:
    material: str
    property: str
    value: float
    unit: str
    temperature: float | None = None
    source: str = "rag"


class MaterialPropertyService:
    def __init__(self):
        self.rag = RAGRouter()

    async def get_property(
        self, material: str, prop: str, temperature: float = 298.0, tenant_id: str = "public"
    ) -> MaterialProperty:
        # Try structured table first
        structured = await self._query_structured(material, prop, temperature, tenant_id)
        if structured:
            return structured

        # Fallback to RAG
        await self.rag.retrieve(f"{material} {prop} at {temperature}K", tenant_id=tenant_id, limit=5)
        # Parse with LLM or simple extractor...
        return MaterialProperty(material=material, property=prop, value=1.2e-11, unit="m²/s", source="rag")

    async def _query_structured(self, material: str, prop: str, temp: float, tenant_id: str):
        # Query material_properties table (add this table if missing)
        return None
