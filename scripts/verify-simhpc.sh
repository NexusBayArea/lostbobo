# SimHPC Core Engine Deployment Verification Script

NAMESPACE="simhpc"
RED="\033[0;31m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
NC="\033[0m"

log() { echo -e "${BLUE}[$(date "+%H:%M:%S")]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

log "Starting SimHPC Core Engine verification..."
kubectl wait --for=condition=Ready pods -l app=simhpc-core -n $NAMESPACE --timeout=120s
success "All core pods are Ready"
