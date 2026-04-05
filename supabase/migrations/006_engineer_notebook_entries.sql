-- 006_engineer_notebook_entries.sql
-- Structured experiment notebook with linked simulations

CREATE TABLE IF NOT EXISTS notebook_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  simulation_id UUID REFERENCES simulations(id) ON DELETE SET NULL,
  title TEXT NOT NULL DEFAULT '',
  research_question TEXT DEFAULT '',
  parameters TEXT DEFAULT '',
  observations TEXT DEFAULT '',
  conclusions TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  linked_experiment_ids UUID[] DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notebook_entries_user_id ON notebook_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_notebook_entries_simulation_id ON notebook_entries(simulation_id);
CREATE INDEX IF NOT EXISTS idx_notebook_entries_created ON notebook_entries(user_id, created_at DESC);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_notebook_entry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_notebook_entry_updated_at ON notebook_entries;
CREATE TRIGGER set_notebook_entry_updated_at
  BEFORE UPDATE ON notebook_entries
  FOR EACH ROW
  EXECUTE FUNCTION update_notebook_entry_updated_at();

ALTER TABLE notebook_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage their own notebook entries"
  ON notebook_entries
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
