import asyncio
from backend.core.embedding.service import embedding_service

async def main():
    print("Starting full backfill of document_chunks embeddings...")
    count = await embedding_service.process_unembedded_chunks(batch_size=100)
    print(f"Backfill complete — {count} chunks embedded.")

if __name__ == "__main__":
    asyncio.run(main())
