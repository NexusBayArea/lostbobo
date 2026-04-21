CREATE TABLE IF NOT EXISTS conformal_residuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    feature_hash TEXT,
    residual FLOAT,
    prediction FLOAT,
    ground_truth FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
