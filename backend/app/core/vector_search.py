from supabase import create_client
from typing import List, Dict
import os


class VectorSearch:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SB_URL"),
            os.getenv("SB_SERVICE_ROLE_KEY")
        )

    async def search_simulations(self, query: str, limit: int = 5, similarity_threshold: float = 0.78) -> List[Dict]:
        embedding = await self._get_embedding(query)

        response = await self.supabase.rpc(
            "match_simulations",
            {
                "query_embedding": embedding,
                "match_threshold": similarity_threshold,
                "match_count": limit
            }
        ).execute()

        return response.data

    async def _get_embedding(self, text: str) -> List[float]:
        return [0.0] * 1536


vector_search = VectorSearch()