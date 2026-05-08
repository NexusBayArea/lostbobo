from backend.runtime.rag.manifest_parser import ManifestRegistry


class SAHRAGRouter:
    """Simulation-Augmented Hierarchical RAG — Manifest-first retrieval."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.manifests = ManifestRegistry(kernel)
        self.vector_rag = kernel.services["rag"]

    async def query(self, user_query: str, domain: str = None, top_k: int = 10):
        job_id = await self.kernel.supabase_job_store.create_job("sah_rag_query", {"query": user_query})

        # 1. Manifest-guided deterministic navigation
        manifests = await self.manifests.traverse(user_query, domain)

        context = []
        for manifest in manifests[:3]:
            context.append(
                {
                    "type": "manifest",
                    "path": manifest.path,
                    "scope": manifest.scope,
                    "critical_paths": manifest.critical_paths,
                    "always_load": manifest.always_load,
                }
            )

        # 2. Simulation Memory Retrieval
        sim_memory = await self.kernel.services["simulation_memory"].retrieve(user_query, domain)

        # 3. Traditional vector fallback
        vector_results = await self.vector_rag.query(user_query, top_k=top_k - len(context))

        final_context = context + sim_memory + vector_results

        await self.kernel.supabase_job_store.update_job(job_id, result={"context_size": len(final_context)})

        return final_context
