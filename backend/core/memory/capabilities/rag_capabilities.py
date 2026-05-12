from __future__ import annotations


async def register_rag_capabilities(kernel):
    from backend.core.memory.fabric.memory_fabric import MemoryFabric
    from backend.core.memory.rag.graph_rag import GraphRAG
    from backend.core.memory.retrieval.compressor import ContextCompressor
    from backend.core.memory.retrieval.embeddings import EmbeddingService
    from backend.core.memory.retrieval.ingestion import IngestionPipeline
    from backend.core.memory.retrieval.reranker import Reranker
    from backend.core.memory.retrieval.retriever import Retriever
    from backend.core.memory.retrieval.streaming import StreamingRAGOrchestrator

    memory_fabric = MemoryFabric()
    embedder = EmbeddingService()
    retriever = Retriever(memory_fabric, embedder)
    reranker = Reranker()
    compressor = ContextCompressor()
    ingestion = IngestionPipeline(memory_fabric, embedder)
    graph_rag = GraphRAG(memory_fabric, retriever, memory_fabric.graph_store)
    streaming = StreamingRAGOrchestrator(memory_fabric, retriever, reranker, compressor, kernel.trust_telemetry)

    kernel.memory_fabric = memory_fabric
    kernel.embedding_service = embedder

    kernel.capabilities.register("memory.ingest", ingestion.ingest)
    kernel.capabilities.register("memory.retrieve", retriever.retrieve)
    kernel.capabilities.register("memory.rerank", reranker.rerank)
    kernel.capabilities.register("memory.compress", compressor.compress)
    kernel.capabilities.register("memory.graphrag", graph_rag.query)
    kernel.capabilities.register("memory.streaming_rag", streaming.query_stream)
