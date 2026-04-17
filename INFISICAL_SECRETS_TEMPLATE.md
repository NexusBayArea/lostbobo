# SimHPC Infisical Secrets Template
# Copy these to your Infisical dashboard
# Environment: production (or your environment name)

# ═══════════════════════════════════════════════════════════
# CORS Configuration
# ═══════════════════════════════════════════════════════════
ALLOWED_ORIGINS: https://simhpc-nexusbayareas-projects.vercel.app,http://localhost:3000,http://localhost:5173

# ═══════════════════════════════════════════════════════════
# Redis Configuration
# ═══════════════════════════════════════════════════════════

# Option A: Local Redis (for development/RunPod)
REDIS_URL: redis://localhost:6379

# Option B: Redis Cloud (for production)
# Create free account at https://redis.com/cloud/
# Get connection string and replace below
# REDIS_URL: redis://:your-password@your-redis-cloud-host.cloud.redislabs.com:12345

# ═══════════════════════════════════════════════════════════
# Supabase (Authentication)
# ═══════════════════════════════════════════════════════════
SUPABASE_JWT_SECRET: your-supabase-jwt-secret-from-dashboard
SUPABASE_AUDIENCE: authenticated

# ═══════════════════════════════════════════════════════════
# SimHPC API Configuration
# ═══════════════════════════════════════════════════════════
SIMHPC_API_KEY: your-api-key-here
JWT_ALGORITHM: HS256
ENVIRONMENT: production

# ═══════════════════════════════════════════════════════════
# Optional: RunPod Configuration
# ═══════════════════════════════════════════════════════════
RUNPOD_API_KEY: your-runpod-api-key
RUNPOD_GPU_TYPE: A40
RUNPOD_GPU_COUNT: 1

# ═══════════════════════════════════════════════════════════
# Optional: Stripe (if using billing)
# ═══════════════════════════════════════════════════════════
STRIPE_API_KEY: sk_test_your-stripe-key
STRIPE_WEBHOOK_SECRET: whsec_your-webhook-secret

# ═══════════════════════════════════════════════════════════
# Logging & Debugging
# ═══════════════════════════════════════════════════════════
LOG_LEVEL: INFO
DEBUG: false

