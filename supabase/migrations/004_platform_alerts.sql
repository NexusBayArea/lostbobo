-- ============================================
-- 004_platform_alerts.sql
-- v2.5.0: Platform Alerts + Panic Button
-- ============================================

-- Create the platform_alerts table
CREATE TABLE IF NOT EXISTS public.platform_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL, -- 'billing', 'thermal', 'system'
    severity TEXT NOT NULL, -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable Realtime for the alerts table
ALTER PUBLICATION supabase_realtime ADD TABLE platform_alerts;

-- RLS: Only admins can read alerts (service role bypasses)
ALTER TABLE public.platform_alerts ENABLE ROW LEVEL SECURITY;

-- Admins can read all alerts
CREATE POLICY "Admins can read all alerts"
    ON public.platform_alerts
    FOR SELECT
    USING (auth.jwt() ->> 'email' = 'arche@simhpc.com' OR auth.jwt() -> 'app_metadata' ->> 'role' = 'admin');

-- Service role can insert alerts (used by Edge Functions)
-- No explicit policy needed — service_role bypasses RLS

-- Index for fast queries on recent alerts
CREATE INDEX IF NOT EXISTS idx_platform_alerts_created_at
    ON public.platform_alerts (created_at DESC);

-- Index for deduplication queries
CREATE INDEX IF NOT EXISTS idx_platform_alerts_type_created
    ON public.platform_alerts (type, created_at DESC);
