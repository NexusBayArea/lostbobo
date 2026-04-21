CREATE TABLE IF NOT EXISTS risk_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES walk_forward_runs(id),
    current_equity FLOAT,
    peak_equity FLOAT,
    drawdown FLOAT,
    rolling_vol FLOAT,
    var_95 FLOAT,
    cvar_95 FLOAT,
    status TEXT CHECK (status IN ('active', 'restricted', 'halted')),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES walk_forward_runs(id),
    event_type TEXT,
    severity TEXT,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
