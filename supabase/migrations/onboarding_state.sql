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
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER update_onboarding_state_updated_at
    BEFORE UPDATE ON onboarding_state
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();


-- 1. Function to create the onboarding row
CREATE OR REPLACE FUNCTION public.handle_new_user_onboarding()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.onboarding_state (user_id, current_step)
  VALUES (new.id, 'welcome');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Trigger that runs whenever a new user is added to auth.users
CREATE OR REPLACE TRIGGER on_auth_user_created_onboarding
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user_onboarding();
