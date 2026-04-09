-- Authority Alignment: Supabase as single source of truth for usage tracking
-- Prevents race conditions with atomic increments and enables batch flush pattern

-- 1. Add credits column to profiles (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'credits'
    ) THEN
        ALTER TABLE public.profiles ADD COLUMN credits INT DEFAULT 10;
    END IF;
END $$;

-- 2. Create unified usage log table
CREATE TABLE IF NOT EXISTS public.usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    feature_type TEXT NOT NULL, -- e.g., 'simulation', 'alpha_insight'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Index for fast dashboard queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_date 
    ON public.usage_logs(user_id, created_at DESC);

-- 4. The Atomic Increment Function (Prevents Race Conditions)
CREATE OR REPLACE FUNCTION public.decrement_usage_atomic(
    target_user_id UUID, 
    spend_amount INT, 
    feature TEXT
)
RETURNS void AS $$
BEGIN
    -- Only update if the user has enough credits (atomic check)
    UPDATE public.profiles
    SET credits = credits - spend_amount
    WHERE id = target_user_id AND credits >= spend_amount;

    IF FOUND THEN
        -- Log the transaction for audit trails
        INSERT INTO public.usage_logs (user_id, amount, feature_type)
        VALUES (target_user_id, spend_amount, feature);
    ELSE
        RAISE EXCEPTION 'Insufficient credits';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 5. RLS for usage_logs
ALTER TABLE public.usage_logs ENABLE ROW SECURITY;

DROP POLICY IF EXISTS "usage_logs_user_read" ON public.usage_logs;
CREATE POLICY "usage_logs_user_read" ON public.usage_logs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "usage_logs_service_role" ON public.usage_logs;
CREATE POLICY "usage_logs_service_role" ON public.usage_logs
    FOR ALL USING (auth.role() = 'service_role');

-- 6. Grant execute permission to service role
GRANT EXECUTE ON FUNCTION public.decrement_usage_atomic TO service_role;