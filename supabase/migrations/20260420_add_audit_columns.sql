-- 1. Create audit columns
ALTER TABLE walk_forward_runs
ADD COLUMN IF NOT EXISTS audit_result JSONB,
ADD COLUMN IF NOT EXISTS audit_score FLOAT;
