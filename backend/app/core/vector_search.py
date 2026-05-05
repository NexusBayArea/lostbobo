import os
from supabase import create_client


class VectorSearch:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SB_URL", ""),
            os.getenv("SB_SERVICE_ROLE_KEY", "")
        )

    async def search_simulations(
        self, query: str, limit: int = 5, similarity_threshold: float = 0.78
    ) -> list[dict]:
        """Semantic search over simulation history."""
        return [
            {"content": "Sample simulation trace...", "metadata": {"simulation_id": "sim_001"}},
        ]


vector_search = VectorSearch()