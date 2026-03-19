-- SimHPC Supabase Migration: Heartbeat & Simulation History
-- Run this in Supabase SQL Editor to enable real-time dashboard updates

-- 1. Heartbeat table for Dashboard Status LEDs
CREATE TABLE IF NOT EXISTS worker_heartbeat (
    worker_id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'online',
    jobs_processed INTEGER DEFAULT 0,
    last_ping TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    gpu_type TEXT
);

-- 2. Simulation History for the User Dashboard
CREATE TABLE IF NOT EXISTS simulation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    job_id TEXT UNIQUE,
    scenario_name TEXT,
    status TEXT DEFAULT 'queued',
    result_summary JSONB,
    report_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Enable Realtime so the Dashboard updates automatically
ALTER PUBLICATION supabase_realtime ADD TABLE worker_heartbeat;
ALTER PUBLICATION supabase_realtime ADD TABLE simulation_history;

-- 4. Index for fast dashboard queries
CREATE INDEX IF NOT EXISTS idx_simulation_history_user_id ON simulation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_simulation_history_status ON simulation_history(status);
CREATE INDEX IF NOT EXISTS idx_worker_heartbeat_last_ping ON worker_heartbeat(last_ping);

-- 5. Alpha Lead Qualification Table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    runs_completed INTEGER DEFAULT 0,
    qualification TEXT DEFAULT 'new' CHECK (qualification IN ('new', 'warm', 'hot')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_qualification ON leads(qualification);
