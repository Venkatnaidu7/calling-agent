#!/usr/bin/env bash
# ==============================================================================
# AI Voice Agent Platform - Linux Podman Quickstart Script
# ==============================================================================
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}   AI Voice Agent SaaS Platform - Podman Quickstart ${NC}"
echo -e "${CYAN}====================================================${NC}\n"

# 1. Check Podman installation
if ! command -v podman &>/dev/null; then
    echo -e "${RED}[ERROR] Podman is not installed. Please install podman first:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y podman"
    echo "  Fedora/RHEL:   sudo dnf install -y podman"
    echo "  Arch:          sudo pacman -S podman"
    exit 1
fi

# 2. Detect compose CLI (podman compose vs podman-compose)
COMPOSE_CMD=""
if podman compose version &>/dev/null; then
    COMPOSE_CMD="podman compose"
elif command -v podman-compose &>/dev/null; then
    COMPOSE_CMD="podman-compose"
else
    echo -e "${YELLOW}[INFO] Neither 'podman compose' nor 'podman-compose' was found.${NC}"
    echo "Installing podman-compose via pip or package manager is recommended:"
    echo "  pip install --user podman-compose"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Using compose command: ${CYAN}${COMPOSE_CMD}${NC}"

# 3. Verify .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!] .env file not found. Copying from .env.example...${NC}"
    cp .env.example .env
    
    # Generate cryptographic keys if openssl is available
    if command -v openssl &>/dev/null; then
        NEW_APP_KEY=$(openssl rand -hex 32)
        NEW_JWT_KEY=$(openssl rand -hex 32)
        sed -i "s/APP_SECRET_KEY=.*/APP_SECRET_KEY=${NEW_APP_KEY}/" .env
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${NEW_JWT_KEY}/" .env
        echo -e "${GREEN}[OK]${NC} Generated random APP_SECRET_KEY and JWT_SECRET_KEY in .env"
    fi
else
    echo -e "${GREEN}[OK]${NC} .env configuration detected."
fi

# 4. Build and start containers
echo -e "\n${CYAN}Building and starting container stack with Podman...${NC}"
$COMPOSE_CMD up -d --build

# 5. Wait for services to initialize
echo -e "\n${YELLOW}Waiting for PostgreSQL & Redis to report healthy status...${NC}"
for i in {1..30}; do
    if $COMPOSE_CMD ps | grep -q "postgres.*healthy" || podman inspect --format='{{.State.Health.Status}}' aicalling_postgres_1 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}[OK] Database is healthy!${NC}"
        break
    fi
    sleep 2
    if [ "$i" -eq 30 ]; then
        echo -e "${YELLOW}[NOTE] DB health status still pending, proceeding to migration attempt...${NC}"
    fi
done

# 6. Run database migrations
echo -e "\n${CYAN}Applying Alembic database migrations...${NC}"
$COMPOSE_CMD exec -T api python -m alembic upgrade head
echo -e "${GREEN}[OK] Migrations applied successfully!${NC}"

# 7. Stack Summary & Next Steps
echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}   AI Calling Platform is Running Successfully!     ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "  - Frontend Dashboard: ${CYAN}http://localhost:3000${NC}"
echo -e "  - Backend REST API:   ${CYAN}http://localhost:8000${NC}"
echo -e "  - API Swagger Docs:   ${CYAN}http://localhost:8000/api/docs${NC}"
echo -e "  - Health Check:       ${CYAN}http://localhost:8000/health${NC}"
echo -e "  - Celery Worker:      Active (Redis background queue)"
echo -e "  - Database:           PostgreSQL + pgvector (port 5432)"
echo -e "  - Cache/Broker:       Redis 7 (port 6379)"
echo -e "----------------------------------------------------"
echo -e "To create your initial Super Admin account, run:"
echo -e "  ${CYAN}$COMPOSE_CMD exec api python scripts/create_platform_admin.py --email admin@example.com --password 'YourPassword'${NC}\n"
echo -e "To follow API logs:"
echo -e "  ${CYAN}$COMPOSE_CMD logs -f api${NC}\n"
echo -e "To stop the stack:"
echo -e "  ${CYAN}$COMPOSE_CMD down${NC}\n"
