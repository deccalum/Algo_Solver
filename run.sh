#!/bin/bash

# Algo Solver - Full Stack Application Runner
# Python optimization engine + React frontend

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_DIR="$SCRIPT_DIR/python"
DATA_DIR="$SCRIPT_DIR/data/output"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Prefer the project venv if it exists, otherwise fall back to system python.
if [ -f "$SCRIPT_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON="$SCRIPT_DIR/.venv/Scripts/python.exe"   # Windows (Git Bash)
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"            # macOS / Linux
else
    PYTHON="python"
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

case "$1" in
    # ============ FULL-STACK COMMANDS ============
    
    start)
        print_header "Starting Full-Stack Application"
        print_info "Using Docker Compose (postgres + api + nginx frontend)"
        print_info "  • Frontend (nginx): http://localhost:8080"
        print_info "  • API:              http://localhost:18000"
        print_info "  • Database:         localhost:5432"
        print_info ""
        cd "$SCRIPT_DIR"
        docker compose up --build
        ;;
    
    dev)
        print_header "Starting Development Servers"
        print_info "This will start:"
        print_info "  • PostgreSQL (Docker):  localhost:5432"
        print_info "  • Python API server:    http://localhost:18000"
        print_info "  • Frontend dev server:  http://localhost:3000"
        print_info ""

        # 1. Ensure postgres is up (reuse the compose service, detached)
        print_info "Starting PostgreSQL container..."
        cd "$SCRIPT_DIR"
        docker compose up postgres -d

        # 2. Wait until postgres is healthy
        print_info "Waiting for PostgreSQL to be ready..."
        until docker compose exec -T postgres pg_isready -U postgres -d grip_solve > /dev/null 2>&1; do
            sleep 1
        done
        print_success "PostgreSQL ready"

        # 3. Resolve DATABASE_URL: .env overrides, then fallback to docker-compose default
        if [ -f "$SCRIPT_DIR/.env" ]; then
            set -a; source "$SCRIPT_DIR/.env"; set +a
            print_info "Loaded .env"
        fi
        export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/grip_solve}"
        print_info "DATABASE_URL: $DATABASE_URL"

        # 4. Start the Python API in the background
        print_info "Starting Python API..."
        "$PYTHON" python/run_api.py &
        BACKEND_PID=$!

        # 5. Wait up to 15 s for the API to start accepting connections
        API_UP=0
        for i in $(seq 1 15); do
            sleep 1
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                echo ""
                print_info "ERROR: Python API process exited (PID $BACKEND_PID). Check logs above."
                docker compose down postgres 2>/dev/null || true
                exit 1
            fi
            if curl -sf http://127.0.0.1:18000/api/health > /dev/null 2>&1; then
                API_UP=1
                break
            fi
        done

        if [ $API_UP -eq 0 ]; then
            print_info "WARNING: API did not respond within 15 s — check logs above."
        else
            print_success "Python API running (PID: $BACKEND_PID)"
        fi

        # 6. Start Vite dev server (foreground — keeps the terminal live)
        print_info "Starting frontend..."
        cd "$FRONTEND_DIR"
        npm run dev

        # Cleanup on exit
        kill $BACKEND_PID 2>/dev/null || true
        docker compose stop postgres 2>/dev/null || true
        ;;
    
    frontend)
        print_header "Starting Frontend Dev Server Only"
        print_info "Dev server: http://localhost:3000"
        print_info "API proxy:  http://localhost:18000"
        cd "$FRONTEND_DIR"
        npm run dev
        ;;
    
    backend)
        print_header "Starting Python API Server Only"
        print_info "FastAPI server: http://localhost:18000"
        cd "$SCRIPT_DIR"
        "$PYTHON" python/run_api.py
        ;;
    
    build)
        print_header "Building Full Application"
        
        print_info "Installing frontend dependencies..."
        cd "$FRONTEND_DIR"
        npm install
        
        print_info "Building frontend for production..."
        npm run build
        print_success "Frontend built → frontend/dist/"
        
        print_header "Build Complete"
        print_info "Run with: ./run.sh start"
        ;;
    
    # ============ DOCKER COMMANDS ============
    
    docker-up)
        print_header "Starting Docker Services"
        print_info "This will start:"
        print_info "  • PostgreSQL database: localhost:5432"
        print_info "  • Python API server:    localhost:18000"
        print_info "  • Frontend (nginx):      localhost:8080"
        print_info ""
        cd "$SCRIPT_DIR"
        docker compose up --build
        ;;

    docker-dev)
        print_header "Starting Docker Services (Development)"
        print_info "Same as docker-up but force-recreate all containers"
        cd "$SCRIPT_DIR"
        docker compose up --build --force-recreate
        ;;

    docker-down)
        print_header "Stopping Docker Services"
        cd "$SCRIPT_DIR"
        docker compose down
        print_success "Docker services stopped"
        ;;

    docker-logs)
        print_header "Docker Service Logs"
        cd "$SCRIPT_DIR"
        docker compose logs -f
        ;;
    
    # ============ PYTHON OPTIMIZATION ENGINE ============
    
    generate)
        print_header "Generating Product Catalog (~100k products)"
        cd "$SCRIPT_DIR"
        "$PYTHON" python/main.py
        print_success "Products generated to: $DATA_DIR/"
        ;;
    
    results)
        print_header "Generated Results"
        echo "Files in $DATA_DIR:"
        ls -lh "$DATA_DIR"/ 2>/dev/null || echo "No results yet. Run './run.sh generate' first."
        ;;
    
    # ============ UTILITIES ============
    
    install)
        print_header "Installing All Dependencies"
        
        print_info "Installing frontend dependencies..."
        cd "$FRONTEND_DIR"
        npm install
        print_success "Frontend dependencies installed"
        
        print_info "Verifying Python..."
        "$PYTHON" --version
        print_success "Python ready ($PYTHON)"
        
        print_header "All Dependencies Ready"
        ;;
    
    clean)
        print_header "Cleaning Build Artifacts"
        
        print_info "Cleaning frontend..."
        cd "$FRONTEND_DIR"
        rm -rf dist node_modules
        
        print_info "Cleaning Python cache..."
        cd "$PYTHON_DIR"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        
        print_success "All build artifacts cleaned"
        ;;
    
    *)
        cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                    ALGO SOLVER - RUNNER                        ║
║              Python Optimization + React Frontend              ║
╚════════════════════════════════════════════════════════════════╝

Usage: ./run.sh [command]

📦 FULL-STACK COMMANDS:
  start          Start via Docker Compose (same as docker-up)
                 → Frontend: http://localhost:8080
                 → API:      http://localhost:18000
  dev            Start dev servers with hot reload
                 → Frontend: http://localhost:3000 (Vite HMR)
                 → Backend:  http://localhost:18000 (requires local Postgres)
  frontend       Start only Vite dev server (port 3000)
  backend        Start only Python API server (port 18000)
  build          Build frontend for production

🐳 DOCKER COMMANDS:
  docker-up      Build and start all services (postgres + api + nginx)
                 → Frontend: http://localhost:8080
                 → API:      http://localhost:18000
                 → Database: localhost:5432
  docker-dev     Same as docker-up but force-recreate all containers
  docker-down    Stop and remove all Docker containers
  docker-logs    Tail logs from all services

🐍 PYTHON OPTIMIZATION ENGINE:
  generate       Generate product catalog (~100k products)
  results        Show generated data files

🛠️  UTILITIES:
  install        Install all dependencies (npm + verify Python)
  clean          Remove all build artifacts

💡 QUICK START:
  ./run.sh install       # First time only
  ./run.sh dev           # Development mode
  ./run.sh generate      # Generate product data

  Or with Docker:
  ./run.sh docker-up     # Production containers

📚 CONFIGURATION:
  - Python engine:  config/dev_default.py
  - Frontend:       frontend/vite.config.js
  - Docker:         docker-compose.yml

🌐 URLs:
  Development: http://localhost:3000  (Vite dev server with HMR)
               http://localhost:18000 (FastAPI backend)
  Production:  http://localhost:8080   (nginx + API)
EOF
        ;;
esac