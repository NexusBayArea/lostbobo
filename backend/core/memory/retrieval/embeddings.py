from __future__ import annotations

import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str = "nomic-embed-text-v2-moe"):
        self.model_name = model_name

    async def embed(self, texts: list[str]) -> list[list[float]]:
        dim = 768
        return [np.random.randn(dim).tolist() for _ in texts]
