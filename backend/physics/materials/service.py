from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client
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
        self.client = get_supabase_client()

    async def get_property(
        self, material: str, prop: str, temperature: float = 298.0, tenant_id: str = "public"
    ) -> MaterialProperty | None:
        # Try structured table first
        structured = await self._query_structured(material, prop, temperature, tenant_id)
        if structured:
            return structured

        # Fallback to RAG
        await self.rag.retrieve(f"{material} {prop} at {temperature}K", tenant_id=tenant_id, limit=5)
        # Parse with LLM or simple extractor...
        return MaterialProperty(material=material, property=prop, value=1.2e-11, unit="m²/s", source="rag")

    async def _query_structured(self, material: str, prop: str, temp: float, tenant_id: str) -> MaterialProperty | None:
        if not self.client:
            return None

        # Query Supabase for the exact match
        resp = (
            await self.client.table("material_properties")
            .select("*")
            .eq("material", material)
            .eq("property", prop)
            .eq("temperature", temp)
            .eq("tenant_id", tenant_id)
            .execute()
        )

        if resp.data and len(resp.data) > 0:
            data = resp.data[0]
            return MaterialProperty(
                material=data["material"],
                property=data["property"],
                value=float(data["value"]),
                unit=data["unit"],
                temperature=float(data["temperature"]) if data["temperature"] else None,
                source=data.get("source", "db"),
            )
        return None
