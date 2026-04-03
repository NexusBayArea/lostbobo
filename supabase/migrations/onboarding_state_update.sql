-- Update SimHPC Onboarding State for Versioned Conflict Resolution
ALTER TABLE onboarding_state 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS events TEXT[] DEFAULT '{}';

-- If the table already exists, ensure it has these columns.
-- The previous migration might have already created it without them.
