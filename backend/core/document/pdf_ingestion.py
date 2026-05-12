from __future__ import annotations

import uuid
from typing import Any

import fitz

from backend.core.memory.retrieval.ingestion import IngestionPipeline


class PDFIngestionService:
    def __init__(self, ingestion_pipeline: IngestionPipeline):
        self.ingestion = ingestion_pipeline

    async def ingest(
        self,
        file_bytes: bytes,
        tenant_id: str,
        plugin_name: str = "kernel",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        documents = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if not text.strip():
                continue

            tables = page.find_tables()
            table_text = ""
            for table in tables:
                for row in table.extract():
                    table_text += " | ".join(str(cell) for cell in row) + "\n"
                table_text += "\n"

            content = text + "\n" + table_text if table_text else text

            chunk_id = str(uuid.uuid4())
            documents.append(
                {
                    "content": content,
                    "metadata": {
                        **(metadata or {}),
                        "source": "pdf",
                        "page": page_num + 1,
                        "total_pages": doc.page_count,
                        "chunk_id": chunk_id,
                    },
                }
            )

        doc.close()
        count = await self.ingestion.ingest(documents, plugin_name=plugin_name, tenant_id=tenant_id)
        return count
