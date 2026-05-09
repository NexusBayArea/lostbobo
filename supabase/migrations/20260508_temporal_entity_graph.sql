-- Temporal + Entity Graph enhancements
-- Adds regime column, evidence_event_ids, and graph indexes

ALTER TABLE world_states ADD COLUMN IF NOT EXISTS regime TEXT NOT NULL DEFAULT 'normal';

ALTER TABLE knowledge_graph_edges ADD COLUMN IF NOT EXISTS evidence_event_ids JSONB DEFAULT '[]';

CREATE INDEX IF NOT EXISTS idx_kge_relation_weight ON knowledge_graph_edges (relation, weight DESC);

CREATE TABLE IF NOT EXISTS plugin_registrations (
    plugin_name TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    registered_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE plugin_registrations ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS "plugin_reg_read" ON plugin_registrations FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "plugin_reg_insert" ON plugin_registrations FOR INSERT WITH CHECK (true);

GRANT SELECT, INSERT ON plugin_registrations TO anon, authenticated, service_role;
