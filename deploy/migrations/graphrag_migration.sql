-- GraphRAG Migration
-- Adds pgvector embeddings, IVFFlat index, and match_chunks() RPC
-- Safe to re-run: uses IF NOT EXISTS / CREATE OR REPLACE

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS embedding vector(1536);

ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS category text;

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_category
    ON document_chunks (category);

CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_count int DEFAULT 20,
    min_similarity float DEFAULT 0.30,
    filter_category text DEFAULT NULL
)
RETURNS TABLE (
    chunk_id text,
    text text,
    source_name text,
    title text,
    url text,
    published_at double precision,
    similarity float
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id AS chunk_id,
        dc.text,
        dc.source_name,
        dc.title,
        dc.url,
        dc.published_at,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE dc.embedding IS NOT NULL
      AND 1 - (dc.embedding <=> query_embedding) >= min_similarity
      AND (filter_category IS NULL OR dc.category = filter_category)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION match_chunks TO anon, authenticated, service_role;
