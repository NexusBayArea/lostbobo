CREATE TABLE IF NOT EXISTS plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    publisher TEXT NOT NULL,
    version TEXT NOT NULL,
    manifest JSONB NOT NULL,
    trust_score FLOAT DEFAULT 0.5,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plugins_plugin_id ON plugins (plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugins_revoked ON plugins (revoked);
