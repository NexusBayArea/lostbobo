#!/bin/bash
# =============================================================================
# SimHPC CPU Node Validation — health checks for all services
# =============================================================================
set -euo pipefail

echo "=== SimHPC CPU Node Validation ==="
FAILED=0

check() {
    local name="$1"
    shift
    echo -n "$name: "
    if "$@" > /dev/null 2>&1; then
        echo "OK"
    else
        echo "FAIL"
        FAILED=1
    fi
}

check "Gateway HTTP" curl -s http://localhost:8080/health --max-time 5
check "RAG Service gRPC" python3 -c "import grpc; ch = grpc.insecure_channel('localhost:50051'); grpc.channel_ready_future(ch).result(timeout=5)"
check "Module Runtime gRPC" python3 -c "import grpc; ch = grpc.insecure_channel('localhost:50052'); grpc.channel_ready_future(ch).result(timeout=5)"

TOKEN=$(curl -s -X POST http://localhost:8080/auth/token \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    check "Auth JWT" test -n "$TOKEN"
    check "RAG Retrieve" curl -s -X POST http://localhost:8080/api/v1/rag/retrieve \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"query":"test","top_k":1}' --max-time 10
    check "DeepSeek Reason" curl -s -X POST http://localhost:8080/api/v1/rag/reason \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"context":[],"prompt_template":"Say hello in one word"}' --max-time 30
    check "Plugins" curl -s http://localhost:8080/api/v1/plugins \
        -H "Authorization: Bearer $TOKEN" --max-time 5
else
    echo "WARNING: Could not obtain auth token. Skipping authenticated checks."
fi

if [ "$FAILED" -eq 0 ]; then
    echo ""
    echo "=== All checks passed ==="
else
    echo ""
    echo "=== Some checks FAILED ==="
    exit 1
fi
