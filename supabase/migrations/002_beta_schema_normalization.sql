-- =========================================
-- SimHPC Beta Schema Migration (v2.5.0)
-- =========================================
-- Idempotent. Safe for incremental rollout.

-- 0. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. SIMULATIONS (CORE)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'simulation_history') THEN
        ALTER TABLE simulation_history RENAME TO simulations;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    org_id TEXT,
    job_id TEXT UNIQUE,
    scenario_name TEXT,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'auditing', 'completed', 'failed')),
    prompt TEXT,
    input_params JSONB,
    result_summary JSONB,
    gpu_result JSONB,
    audit_result JSONB,
    hallucination_score FLOAT,
    report_url TEXT,
    pdf_url TEXT,
    certificate_id TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE simulations ADD COLUMN IF NOT EXISTS org_id TEXT;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS gpu_result JSONB;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS audit_result JSONB;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS hallucination_score FLOAT;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS certificate_id TEXT;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS pdf_url TEXT;
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'simulations_status_check') THEN
        ALTER TABLE simulations ADD CONSTRAINT simulations_status_check CHECK (status IN ('queued', 'running', 'auditing', 'completed', 'failed'));
    END IF;
END $$;

-- 2. CERTIFICATES
CREATE TABLE IF NOT EXISTS certificates (
    id TEXT PRIMARY KEY,
    simulation_id UUID REFERENCES simulations(id) ON DELETE CASCADE,
    verification_hash TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. RAG TABLES
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    title TEXT,
    type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    doc_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id TEXT,
    content TEXT,
    embedding VECTOR(768),
    embedding_dim INT DEFAULT 768,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. EVENT LOG
CREATE TABLE IF NOT EXISTS simulation_events (
    id BIGSERIAL PRIMARY KEY,
    simulation_id UUID,
    type TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. BACKFILL
UPDATE simulations SET status = 'completed' WHERE (report_url IS NOT NULL OR pdf_url IS NOT NULL) AND (status IS NULL OR status = 'queued');
UPDATE simulations SET hallucination_score = (audit_result->>'hallucination_score')::float WHERE audit_result IS NOT NULL AND hallucination_score IS NULL;
UPDATE simulations SET org_id = user_id::text WHERE org_id IS NULL AND user_id IS NOT NULL;

-- 6. INDEXES
CREATE INDEX IF NOT EXISTS idx_simulations_user_id ON simulations(user_id);
CREATE INDEX IF NOT EXISTS idx_simulations_org_id ON simulations(org_id);
CREATE INDEX IF NOT EXISTS idx_simulations_status ON simulations(status);
CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_simulations_updated_at ON simulations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_simulations_job_id ON simulations(job_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_events_simulation_id ON simulation_events(simulation_id);

-- 7. FOREIGN KEY BACKREF
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'simulations_certificate_fk') THEN
        ALTER TABLE simulations ADD CONSTRAINT simulations_certificate_fk FOREIGN KEY (certificate_id) REFERENCES certificates(id);
    END IF;
END $$;

-- 8. RLS
ALTER TABLE simulations ENABLE ROW LEVEL SECURITY;
ALTER TABLE certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "simulations_user_access" ON simulations;
CREATE POLICY "simulations_user_access" ON simulations FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "simulations_service_role" ON simulations;
CREATE POLICY "simulations_service_role" ON simulations FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "certificates_service_role" ON certificates;
CREATE POLICY "certificates_service_role" ON certificates FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "simulation_events_service_role" ON simulation_events;
CREATE POLICY "simulation_events_service_role" ON simulation_events FOR ALL USING (true) WITH CHECK (true);

-- 9. UPDATED_AT TRIGGER
CREATE OR REPLACE FUNCTION update_updated_at_column() 
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$ 
BEGIN 
  NEW.updated_at = NOW(); 
  RETURN NEW; 
END; 
$$;

DROP TRIGGER IF EXISTS update_simulations_updated_at ON simulations;
CREATE TRIGGER update_simulations_updated_at BEFORE UPDATE ON simulations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10. REALTIME
ALTER PUBLICATION supabase_realtime ADD TABLE simulations;

-- 11. VERIFICATION VIEW
CREATE OR REPLACE VIEW certificate_verification_view 
WITH (security_invoker = true) AS
SELECT c.id AS certificate_id, c.simulation_id, c.verification_hash, c.storage_url, c.created_at,
       s.hallucination_score, s.audit_result, s.status AS simulation_status
FROM certificates c JOIN simulations s ON s.id = c.simulation_id;

-- 12. BACKWARD COMPAT VIEW
CREATE OR REPLACE VIEW simulation_history 
WITH (security_invoker = true) AS
SELECT id, user_id, job_id, scenario_name, status, result_summary, report_url, created_at FROM simulations;
