-- 1. Create walk_forward_runs table
CREATE TABLE IF NOT EXISTS walk_forward_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID,
  strategy_id TEXT,
  dataset_id TEXT,
  status TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create walk_forward_windows table
CREATE TABLE IF NOT EXISTS walk_forward_windows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES walk_forward_runs(id),
  train_start DATE,
  train_end DATE,
  test_start DATE,
  test_end DATE,
  contract_hash TEXT,
  simulation_id UUID,
  status TEXT,
  metrics JSONB
);

-- 3. Create strategy_snapshots table
CREATE TABLE IF NOT EXISTS strategy_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id TEXT,
  version INT,
  parameters JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
