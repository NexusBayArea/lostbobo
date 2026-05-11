-- deploy/supabase/migrations/20260510_plugin_security.sql
-- Plugin Security Audit Log

CREATE TABLE IF NOT EXISTS kernel_security_audit (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT,
    plugin_id TEXT NOT NULL,
    command TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    duration_ms DOUBLE PRECISION,
    output_bytes INTEGER,
    permission_denied BOOLEAN DEFAULT FALSE,
    timed_out BOOLEAN DEFAULT FALSE,
    anomaly_flag BOOLEAN DEFAULT FALSE,
    timestamp DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE INDEX IF NOT EXISTS idx_security_plugin_ts
    ON kernel_security_audit (plugin_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_security_request_id
    ON kernel_security_audit (request_id);

-- RLS
ALTER TABLE kernel_security_audit ENABLE ROW LEVEL SECURITY;

-- service_role full access
DROP POLICY IF EXISTS "service_role_full_access_audit" ON kernel_security_audit;
CREATE POLICY "service_role_full_access_audit" ON kernel_security_audit
    TO service_role USING (true) WITH CHECK (true);

-- Read-only for authenticated users
DROP POLICY IF EXISTS "auth_read_audit" ON kernel_security_audit;
CREATE POLICY "auth_read_audit" ON kernel_security_audit
    TO authenticated USING (true);