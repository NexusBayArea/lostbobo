-- Event Fabric Migration
-- Append-only events table with temporal indexes

CREATE TABLE IF NOT EXISTS events (
    event_id         TEXT PRIMARY KEY,
    event_type       TEXT NOT NULL,
    timestamp        DOUBLE PRECISION NOT NULL,
    causal_id        TEXT NOT NULL,
    source_plugin    TEXT NOT NULL,
    priority         TEXT NOT NULL,
    confidence       DOUBLE PRECISION NOT NULL,
    payload          JSONB NOT NULL DEFAULT '{}',
    provenance_hash  TEXT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events USING BRIN (timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events (event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_source ON events (source_plugin);

ALTER TABLE events ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "events_append_only" ON events FOR INSERT WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "events_read" ON events FOR SELECT USING (true);

GRANT SELECT, INSERT ON events TO anon, authenticated, service_role;
