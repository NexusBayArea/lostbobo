-- deploy/supabase/migrations/20260510_provenance_storage.sql

-- 1. Core Lineage Table (already exists, add missing columns safely)
ALTER TABLE execution_lineage 
ADD COLUMN IF NOT EXISTS trace_id TEXT,
ADD COLUMN IF NOT EXISTS correlation_id TEXT,
ADD COLUMN IF NOT EXISTS causation_id TEXT;

-- 2. Dedicated Provenance Graph Tables (for fast traversal)
CREATE TABLE IF NOT EXISTS provenance_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    node_type TEXT NOT NULL,
    node_name TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(execution_id, node_type, node_name)
);

CREATE TABLE IF NOT EXISTS provenance_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    weight FLOAT DEFAULT 1.0,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for fast queries and graph traversal
CREATE INDEX IF NOT EXISTS idx_provenance_nodes_execution 
    ON provenance_nodes(execution_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_provenance_edges_execution 
    ON provenance_edges(execution_id, source_id, target_id);

CREATE INDEX IF NOT EXISTS idx_provenance_edges_relation 
    ON provenance_edges(relation);

-- 3. Signed Snapshots (for audit & replay)
CREATE TABLE IF NOT EXISTS provenance_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    integrity_hash TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_snapshots_execution 
    ON provenance_snapshots(execution_id, captured_at DESC);

-- 4. RLS (service_role full access)
ALTER TABLE provenance_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE provenance_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE provenance_snapshots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_full_access" ON provenance_nodes;
CREATE POLICY "service_role_full_access" ON provenance_nodes TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_full_access" ON provenance_edges;
CREATE POLICY "service_role_full_access" ON provenance_edges TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_full_access" ON provenance_snapshots;
CREATE POLICY "service_role_full_access" ON provenance_snapshots TO service_role USING (true) WITH CHECK (true);