-- 1. Create runs table
CREATE TABLE IF NOT EXISTS runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  label TEXT
);

-- 2. Create node_traces table
CREATE TABLE IF NOT EXISTS node_traces (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid REFERENCES runs(id),
  node_id TEXT,
  contract TEXT,
  deps JSONB,
  result JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create indexes
CREATE INDEX IF NOT EXISTS idx_node_traces_run_id ON node_traces(run_id);
CREATE INDEX IF NOT EXISTS idx_node_traces_node_id ON node_traces(node_id);
