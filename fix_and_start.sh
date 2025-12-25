#!/bin/bash

# AutoDeployX Port Conflict Resolver - Updated for v3.9
# Fixes port 6333 conflict and starts all services

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

clear
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    AutoDeployX Complete Setup Tool    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in AutoDeployX directory
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found!"
    echo "Run this from: cd ~/AutoDeployX && sudo ./fix_and_start.sh"
    exit 1
fi

# Step 1: Stop all existing containers
info "Step 1/7: Stopping all AutoDeployX containers..."
docker-compose down -v 2>/dev/null || true
sleep 2

# Step 2: Find and stop conflicting processes
info "Step 2/7: Checking for port conflicts..."

check_and_free_port() {
    local port=$1
    local service=$2
    
    # Check using multiple methods
    if command -v lsof &> /dev/null; then
        PIDS=$(sudo lsof -ti :$port 2>/dev/null || true)
    elif command -v ss &> /dev/null; then
        PIDS=$(sudo ss -lptn "sport = :$port" 2>/dev/null | awk '/pid=/{match($0,/pid=([0-9]+)/,a); print a[1]}' | sort -u || true)
    else
        PIDS=""
    fi
    
    if [ ! -z "$PIDS" ]; then
        warning "Port $port ($service) occupied by PID(s): $PIDS"
        
        # Check if it's a Docker container
        for pid in $PIDS; do
            CONTAINER=$(docker ps -q --filter "pid=$pid" 2>/dev/null || true)
            if [ ! -z "$CONTAINER" ]; then
                warning "Found Docker container using port $port, stopping..."
                docker stop $CONTAINER 2>/dev/null || true
            else
                warning "Non-Docker process on port $port, attempting to kill PID $pid..."
                sudo kill -9 $pid 2>/dev/null || true
            fi
        done
        sleep 1
        log "Freed port $port"
    else
        log "Port $port ($service) is free"
    fi
}

# Check all required ports
check_and_free_port 6333 "Qdrant"
check_and_free_port 6334 "Qdrant gRPC"
check_and_free_port 8000 "Backend API"
check_and_free_port 3000 "Frontend"
check_and_free_port 9090 "Prometheus"
check_and_free_port 3001 "Grafana"

# Step 3: Clean Docker resources
info "Step 3/7: Cleaning old Docker resources..."
docker system prune -f 2>/dev/null || true

# Step 4: Verify .env exists
info "Step 4/7: Checking .env configuration..."
if [ ! -f ".env" ]; then
    warning ".env not found!"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log "Created .env from .env.example"
        echo ""
        warning "⚠️  IMPORTANT: You need to edit .env file!"
        echo "   Add at least ONE of these:"
        echo "   - OPENAI_API_KEY=sk-..."
        echo "   - HUGGINGFACE_API_KEY=hf_..."
        echo "   - LOCAL_LLM_PATH=/path/to/model.gguf"
        echo ""
        read -p "Press Enter to edit .env now, or Ctrl+C to exit: "
        ${EDITOR:-nano} .env
    else
        error ".env.example not found! Cannot proceed."
        exit 1
    fi
else
    log ".env file exists"
    
    # Check if any LLM is configured
    if ! grep -q "OPENAI_API_KEY=sk-" .env && \
       ! grep -q "HUGGINGFACE_API_KEY=hf_" .env && \
       ! grep -q "LOCAL_LLM_PATH=/" .env; then
        warning "No LLM configured in .env!"
        echo "   The app will start but repo analysis won't work."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Edit .env first: nano .env"
            exit 1
        fi
    fi
fi

# Step 5: Build images
info "Step 5/7: Building Docker images (this may take 5-15 minutes)..."
echo ""
docker-compose build --no-cache 2>&1 | tee build.log

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    error "Build failed! Check build.log for details."
    echo ""
    echo "Common fixes:"
    echo "  1. Frontend build error: cd frontend && npm install"
    echo "  2. Check Dockerfiles exist: ls -la docker/"
    echo "  3. Verify disk space: df -h"
    exit 1
fi

log "Build successful!"

# Step 6: Start services
info "Step 6/7: Starting services..."
docker-compose up -d

echo ""
info "Waiting for services to become healthy (max 2 minutes)..."

# Wait function
wait_for_health() {
    local service=$1
    local max_wait=120
    local elapsed=0
    
    echo -n "   $service: "
    
    while [ $elapsed -lt $max_wait ]; do
        STATUS=$(docker-compose ps -q $service | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "starting")
        
        if [ "$STATUS" = "healthy" ]; then
            echo -e "${GREEN}healthy ✓${NC}"
            return 0
        elif [ "$STATUS" = "unhealthy" ]; then
            echo -e "${RED}unhealthy ✗${NC}"
            return 1
        fi
        
        echo -n "."
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    echo -e "${YELLOW}timeout ⚠${NC}"
    return 1
}

# Wait for critical services
wait_for_health "qdrant" || warning "Qdrant not healthy"
wait_for_health "backend" || warning "Backend not healthy"
wait_for_health "frontend" || warning "Frontend not healthy"

# Step 7: Display status
echo ""
info "Step 7/7: Final status check..."
echo ""
docker-compose ps

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 AutoDeployX is running!                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📱 Access Your Services:${NC}"
echo ""
echo -e "  🌐 Frontend:          ${GREEN}http://localhost:3000${NC}"
echo -e "  🔧 Backend API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  🔍 Backend Health:    ${GREEN}http://localhost:8000/health${NC}"
echo -e "  💾 Qdrant Dashboard:  ${GREEN}http://localhost:6333/dashboard${NC}"
echo -e "  📊 Prometheus:        ${GREEN}http://localhost:9090${NC}"
echo -e "  📈 Grafana:           ${GREEN}http://localhost:3001${NC} (admin/admin)"
echo ""
echo -e "${BLUE}🧪 Quick Tests:${NC}"
echo ""
echo "  # Test backend health"
echo "  curl http://localhost:8000/health"
echo ""
echo "  # Test repo analysis (needs LLM configured)"
echo "  curl -X POST http://localhost:8000/api/repo/analyze \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"repo_url\":\"https://github.com/octocat/Hello-World\",\"branch\":\"master\"}'"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo ""
echo "  View all logs:        docker-compose logs -f"
echo "  View backend logs:    docker-compose logs -f backend"
echo "  Stop all services:    docker-compose down"
echo "  Restart service:      docker-compose restart backend"
echo "  Check status:         docker-compose ps"
echo ""
echo -e "${YELLOW}⚠️  Troubleshooting:${NC}"
echo ""
echo "  If backend fails:"
echo "    docker-compose logs backend | tail -50"
echo ""
echo "  If frontend fails:"
echo "    docker-compose logs frontend | tail -50"
echo ""
echo "  Rebuild everything:"
echo "    docker-compose down -v"
echo "    docker-compose up --build -d"
echo ""

# Optional: Test connections
echo -e "${BLUE}🔍 Running connectivity tests...${NC}"
echo ""

test_endpoint() {
    local name=$1
    local url=$2
    echo -n "  Testing $name... "
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

test_endpoint "Backend Health" "http://localhost:8000/health"
test_endpoint "Backend Docs" "http://localhost:8000/docs"
test_endpoint "Frontend" "http://localhost:3000"
test_endpoint "Qdrant" "http://localhost:6333/healthz"
test_endpoint "Prometheus" "http://localhost:9090/-/healthy"
test_endpoint "Grafana" "http://localhost:3001/api/health"

echo ""
log "Setup complete! 🚀"
echo ""

# Optional: Open in browser
read -p "📱 Open services in browser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:3000" 2>/dev/null &
        sleep 1
        xdg-open "http://localhost:8000/docs" 2>/dev/null &
        sleep 1
        xdg-open "http://localhost:9090" 2>/dev/null &
        sleep 1
        xdg-open "http://localhost:3001" 2>/dev/null &
        log "Opened in browser!"
    else
        warning "Could not detect browser"
    fi
fi

echo ""
echo -e "${GREEN}All done! Take screenshots of all the dashboards! 📸${NC}"
