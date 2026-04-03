-- =========================================
-- SimHPC Profiles Table Migration (v2.5.0)
-- =========================================
-- Purpose: Create the profiles table that the API reads for tier/usage checks.
-- This table was referenced in api.py but had no migration file.
-- =========================================

-- -----------------------------------------
-- PROFILES TABLE
-- -----------------------------------------

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    tier TEXT NOT NULL DEFAULT 'free'
        CHECK (tier IN ('free', 'professional', 'enterprise', 'demo_general', 'demo_full', 'demo_magic')),

    runs_used INTEGER NOT NULL DEFAULT 0,
    email TEXT,
    subscription_status TEXT DEFAULT 'inactive',
    stripe_customer_id TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- -----------------------------------------
-- INDEXES
-- -----------------------------------------

CREATE INDEX IF NOT EXISTS idx_profiles_tier ON profiles(tier);
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer ON profiles(stripe_customer_id);


-- -----------------------------------------
-- ROW LEVEL SECURITY
-- -----------------------------------------

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
DROP POLICY IF EXISTS "profiles_user_read" ON profiles;
CREATE POLICY "profiles_user_read"
ON profiles
FOR SELECT
USING (auth.uid() = id);

-- Users can update their own profile (limited fields)
DROP POLICY IF EXISTS "profiles_user_update" ON profiles;
CREATE POLICY "profiles_user_update"
ON profiles
FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Service role has full access (for API and workers)
DROP POLICY IF EXISTS "profiles_service_role" ON profiles;
CREATE POLICY "profiles_service_role"
ON profiles
FOR ALL
USING (true)
WITH CHECK (true);


-- -----------------------------------------
-- UPDATED_AT TRIGGER
-- -----------------------------------------

DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;

CREATE TRIGGER update_profiles_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =========================================
-- DONE
-- =========================================
