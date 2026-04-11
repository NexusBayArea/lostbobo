#!/bin/bash

# ═══════════════════════════════════════════════════════════
# SimHPC Docker Quick Start Guide
# ═══════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  SimHPC Docker Quick Start                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ───────────────────────────────────────────────────────────
# Step 1: Check prerequisites
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Check Prerequisites"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✓ Check Docker is installed:"
if command -v docker &> /dev/null; then
    echo "  $(docker --version)"
else
    echo "  ✗ Docker not installed. Install from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo ""

echo "✓ Check Docker daemon is running:"
if docker ps &> /dev/null; then
    echo "  Docker daemon OK"
else
    echo "  ✗ Docker daemon not running"
    exit 1
fi
echo ""

echo "✓ Check docker-compose:"
if command -v docker-compose &> /dev/null; then
    echo "  $(docker-compose --version)"
else
    echo "  ✗ docker-compose not found"
    echo "  Install: pip install docker-compose"
    exit 1
fi
echo ""

# ───────────────────────────────────────────────────────────
# Step 2: Setup environment
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Create .env file (if not exists)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# SimHPC Environment Variables

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Redis
REDIS_PASSWORD=changeme

# Supabase
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_AUDIENCE=authenticated

# API
SIMHPC_API_KEY=your-api-key
ENVIRONMENT=development
LOG_LEVEL=info

# Monitoring
GRAFANA_PASSWORD=admin
EOF
    echo "✓ .env created (customize the values!)"
else
    echo "✓ .env already exists"
fi
echo ""

# ───────────────────────────────────────────────────────────
# Step 3: Build image
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Build Docker Image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Option A: Using the build script (recommended)"
echo "  chmod +x docker-build.sh"
echo "  ./docker-build.sh"
echo ""

echo "Option B: Using docker-compose"
echo "  docker-compose build"
echo ""

echo "Option C: Using docker build directly"
echo "  DOCKER_BUILDKIT=1 docker build -t simhpc:latest -f Dockerfile.optimized ."
echo ""

# ───────────────────────────────────────────────────────────
# Step 4: Start services
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Start Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Start all services with docker-compose:"
echo "  docker-compose up -d"
echo ""

echo "Or start individual services:"
echo "  docker-compose up -d redis      # Start Redis only"
echo "  docker-compose up -d api        # Start API only"
echo "  docker-compose up -d prometheus # Start Prometheus"
echo "  docker-compose up -d grafana    # Start Grafana"
echo ""

# ───────────────────────────────────────────────────────────
# Step 5: Monitor services
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Monitor Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Check status:"
echo "  docker-compose ps"
echo ""
echo "  Should show all services as 'Up' with health status:"
echo "  - redis: healthy"
echo "  - api: healthy"
echo ""

echo "View logs:"
echo "  docker-compose logs -f api       # Follow API logs"
echo "  docker-compose logs -f redis     # Follow Redis logs"
echo "  docker-compose logs -f           # Follow all logs"
echo ""

echo "Check health individually:"
echo "  docker exec simhpc-api curl http://localhost:8080/health"
echo "  docker exec simhpc-redis redis-cli ping"
echo ""

# ───────────────────────────────────────────────────────────
# Step 6: Access services
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 6: Access Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "API:"
echo "  Health: http://localhost:8080/health"
echo "  Docs: http://localhost:8080/docs"
echo ""

echo "Redis:"
echo "  Host: localhost:6379"
echo "  Password: (set in .env)"
echo "  CLI: docker exec simhpc-redis redis-cli"
echo ""

echo "Monitoring (optional):"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3000"
echo ""

# ───────────────────────────────────────────────────────────
# Step 7: Common commands
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 7: Common Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Start/Stop:"
echo "  docker-compose up -d             # Start all services"
echo "  docker-compose down              # Stop all services"
echo "  docker-compose restart api       # Restart API service"
echo ""

echo "Logs:"
echo "  docker-compose logs -f api --tail 100"
echo "  docker-compose logs --follow --timestamps"
echo ""

echo "Debugging:"
echo "  docker-compose exec api bash     # Shell into API container"
echo "  docker-compose exec redis bash   # Shell into Redis container"
echo "  docker-compose exec api python3  # Python shell in API"
echo ""

echo "Cleanup:"
echo "  docker-compose down              # Stop and remove containers"
echo "  docker-compose down -v           # Also remove volumes (data loss!)"
echo "  docker image prune               # Remove unused images"
echo "  docker system prune              # Clean up everything unused"
echo ""

# ───────────────────────────────────────────────────────────
# Step 8: Testing
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 8: Test the Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Test API is healthy:"
echo "  curl http://localhost:8080/health"
echo ""

echo "Test CORS is working:"
echo "  curl -i -X GET http://localhost:8080/api/v1/user/profile \\"
echo "    -H 'Origin: http://localhost:3000' \\"
echo "    -H 'Authorization: Bearer <token>'"
echo ""

echo "Look for: Access-Control-Allow-Origin header in response"
echo ""

echo "Test Redis connection:"
echo "  docker exec simhpc-redis redis-cli ping"
echo "  # Should return: PONG"
echo ""

# ───────────────────────────────────────────────────────────
# Troubleshooting
# ───────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TROUBLESHOOTING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Q: Services won't start?"
echo "A: Check logs: docker-compose logs"
echo "   Common issues:"
echo "   - Port already in use: lsof -i :8080 (kill process if needed)"
echo "   - Image not built: docker-compose build"
echo "   - .env missing secrets: edit .env with your values"
echo ""

echo "Q: Health check failing?"
echo "A: Check logs: docker-compose logs -f api"
echo "   Verify endpoint: curl http://localhost:8080/health"
echo "   Check port is exposed: docker-compose ps"
echo ""

echo "Q: Can't connect to Redis?"
echo "A: Check Redis is running: docker-compose ps redis"
echo "   Check password matches .env: docker exec simhpc-redis redis-cli info"
echo "   Verify API has correct REDIS_URL"
echo ""

echo "Q: Out of disk space?"
echo "A: Check: docker system df"
echo "   Clean up: docker system prune -a --volumes"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Ready to deploy!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""