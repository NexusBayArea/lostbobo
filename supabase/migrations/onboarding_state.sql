-- SimHPC Onboarding State Migration
CREATE TABLE IF NOT EXISTS onboarding_state (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    current_step TEXT DEFAULT 'welcome',
    completed_steps TEXT[] DEFAULT '{}',
    skipped BOOLEAN DEFAULT false,
    last_event TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE onboarding_state ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can see their own onboarding state"
    ON onboarding_state FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own onboarding state"
    ON onboarding_state FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own onboarding state"
    ON onboarding_state FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_onboarding_state_updated_at
    BEFORE UPDATE ON onboarding_state
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
