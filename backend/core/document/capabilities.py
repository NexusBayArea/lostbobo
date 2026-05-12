from __future__ import annotations


async def register_document_capabilities(kernel):
    from backend.core.document.pdf_certificate_service import PDFCertificateService
    from backend.core.document.pdf_ingestion import PDFIngestionService
    from backend.core.document.pdf_service import PDFReportService

    pdf_service = PDFReportService()

    ingestion_pipeline = getattr(kernel, "memory_fabric", None)
    if ingestion_pipeline is not None:
        from backend.core.memory.retrieval.embeddings import EmbeddingService
        from backend.core.memory.retrieval.ingestion import IngestionPipeline

        embedder = getattr(kernel, "embedding_service", None) or EmbeddingService()
        pipeline = IngestionPipeline(ingestion_pipeline, embedder)
        pdf_ingestion = PDFIngestionService(pipeline)

        kernel.capabilities.register("memory.ingest_pdf", pdf_ingestion.ingest)

    pdf_cert = PDFCertificateService(kernel)

    kernel.capabilities.register("document.generate_pdf", pdf_service.generate)
    kernel.capabilities.register("document.generate_certificate", pdf_cert.generate)
