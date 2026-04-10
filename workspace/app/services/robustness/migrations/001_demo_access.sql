-- SimHPC Magic Link Demo Access Table
-- Run this in the Supabase SQL Editor

-- Enable UUID generation if not already done
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create demo_access table
CREATE TABLE IF NOT EXISTS demo_access (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT,
  token_hash TEXT UNIQUE NOT NULL,
  usage_limit INT DEFAULT 5,
  usage_count INT DEFAULT 0,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  ip_address TEXT,
  notes TEXT
);

-- Index for fast token lookups
CREATE INDEX IF NOT EXISTS idx_demo_access_token_hash ON demo_access(token_hash);

-- Index for admin queries by email
CREATE INDEX IF NOT EXISTS idx_demo_access_email ON demo_access(email);

-- Row Level Security (RLS)
ALTER TABLE demo_access ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (backend uses service role key)
CREATE POLICY "Service role full access" ON demo_access
  FOR ALL
  USING (auth.role() = 'service_role');

-- Comment on table for documentation
COMMENT ON TABLE demo_access IS 'Magic link demo tokens with usage limits for alpha pilot onboarding';
COMMENT ON COLUMN demo_access.token_hash IS 'SHA-256 hash of the plaintext token (never store raw tokens)';
COMMENT ON COLUMN demo_access.usage_limit IS 'Maximum number of simulation runs allowed';
COMMENT ON COLUMN demo_access.usage_count IS 'Current number of simulation runs used';
COMMENT ON COLUMN demo_access.expires_at IS 'Token expiration timestamp (UTC)';
