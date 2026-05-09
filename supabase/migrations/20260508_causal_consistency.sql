-- Causal Consistency Migration
-- Adds vector_clock and causal_id columns to events table

ALTER TABLE events
    ADD COLUMN IF NOT EXISTS vector_clock JSONB NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS causal_id TEXT NOT NULL;

CREATE INDEX IF NOT EXISTS idx_events_causal ON events (causal_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_vector ON events USING GIN (vector_clock);

-- world_states table for state registry snapshots
CREATE TABLE IF NOT EXISTS world_states (
    state_id         TEXT PRIMARY KEY,
    timestamp        DOUBLE PRECISION NOT NULL,
    causal_id        TEXT NOT NULL,
    regime           TEXT NOT NULL DEFAULT 'normal',
    entities         JSONB NOT NULL DEFAULT '{}',
    uncertainty      JSONB NOT NULL DEFAULT '{}',
    provenance       JSONB NOT NULL DEFAULT '{}',
    pending_events   JSONB NOT NULL DEFAULT '[]',
    snapshot_at      DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_world_states_ts ON world_states (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_world_states_causal ON world_states (causal_id);

ALTER TABLE world_states ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS "world_states_append" ON world_states FOR INSERT WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "world_states_read" ON world_states FOR SELECT USING (true);

GRANT SELECT, INSERT ON world_states TO anon, authenticated, service_role;
