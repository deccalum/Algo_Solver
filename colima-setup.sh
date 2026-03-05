#!/bin/bash

# Algo Solver - Colima Setup Helper
# Use this to start Colima, then run docker-compose for the database

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_colima() {
    if ! command -v colima &> /dev/null; then
        print_error "Colima not found. Install with: brew install colima"
        exit 1
    fi
}

start_colima() {
    print_header "Starting Colima"
    
    # Check if already running
    if colima status &> /dev/null; then
        print_success "Colima is already running"
        return 0
    fi
    
    print_info "Starting Colima (this may take a minute)..."
    colima start
    
    # Give Docker time to be ready
    sleep 5
    print_success "Colima started"
}

start_postgres() {
    print_header "Starting PostgreSQL with Docker Compose"
    
    cd "$SCRIPT_DIR"
    
    print_info "Starting postgres container..."
    docker-compose up -d postgres
    
    print_info "Waiting for PostgreSQL to be ready..."
    sleep 3
    
    # Test connection with limited retries
    max_attempts=10
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U postgres -d algosolver &> /dev/null; then
            print_success "PostgreSQL is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        if [ $attempt -lt $max_attempts ]; then
            echo -n "."
            sleep 1
        fi
    done
    
    print_error "PostgreSQL failed to start after ${max_attempts} seconds"
    echo "Check logs with: docker-compose logs postgres"
    exit 1
}

stop_colima() {
    print_header "Stopping Services"
    
    if [ "$SKIP_COMPOSE" != "true" ]; then
        print_info "Stopping PostgreSQL..."
        docker-compose down || true
        print_success "PostgreSQL stopped"
    fi
    
    print_info "Stopping Colima..."
    colima stop || true
    print_success "Colima stopped"
}

case "$1" in
    up|start)
        check_colima
        start_colima
        start_postgres
        
        print_header "Setup Complete"
        echo -e "${GREEN}Database is ready at: postgresql://localhost:5432/algosolver${NC}"
        echo -e "${GREEN}User: postgres (no password required)${NC}"
        echo ""
        echo "You can now start the backend:"
        echo -e "  ${YELLOW}cd java && mvn spring-boot:run${NC}"
        echo ""
        echo "Or start everything with:"
        echo -e "  ${YELLOW}./run.sh dev${NC}"
        ;;
    
    down|stop)
        stop_colima
        ;;
    
    logs)
        print_info "Showing PostgreSQL logs:"
        docker-compose logs -f postgres
        ;;
    
    status)
        print_info "Colima status:"
        colima status || print_error "Colima not running"
        echo ""
        print_info "PostgreSQL container status:"
        docker-compose ps postgres || print_error "PostgreSQL container not running"
        ;;
    
    *)
        echo "Algo Solver - Colima Setup Helper"
        echo ""
        echo "Usage: $0 {up|down|logs|status}"
        echo ""
        echo "Commands:"
        echo "  up      - Start Colima and PostgreSQL"
        echo "  down    - Stop Colima and PostgreSQL"
        echo "  logs    - Show PostgreSQL logs"
        echo "  status  - Show status of services"
        echo ""
        echo "Quick start:"
        echo "  ./colima-setup.sh up"
        echo "  ./run.sh dev"
        exit 1
        ;;
esac
