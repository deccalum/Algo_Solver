#!/bin/bash

# Algo Solver - Full Stack Application Runner
# Python optimization engine + React frontend

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_DIR="$SCRIPT_DIR/python"
DATA_DIR="$SCRIPT_DIR/data/output"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

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
        print_info "Building frontend..."
        cd "$FRONTEND_DIR"
        npm run build
        print_success "Frontend built to dist"
        
        print_info "Starting Python API server..."
        cd "$PYTHON_DIR"
        python run_api.py
        ;;
    
    dev)
        print_header "Starting Development Servers"
        print_info "This will start:"
        print_info "  • Frontend dev server: http://localhost:3000"
        print_info "  • Python API server:    http://localhost:18000"
        print_info ""
        print_info "Starting Python backend first..."
        
        cd "$PYTHON_DIR"
        python run_api.py &
        BACKEND_PID=$!
        
        sleep 5
        print_success "Python API running (PID: $BACKEND_PID)"
        
        print_info "Starting frontend..."
        cd "$FRONTEND_DIR"
        npm run dev
        
        # Cleanup on exit
        kill $BACKEND_PID 2>/dev/null || true
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
        cd "$PYTHON_DIR"
        python run_api.py
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
        print_info "  • Frontend (nginx):      localhost:80"
        print_info ""
        docker-compose up --build
        ;;
    
    docker-dev)
        print_header "Starting Docker Services (Development)"
        print_info "Same as docker-up but with rebuild"
        docker-compose up --build --force-recreate
        ;;
    
    docker-down)
        print_header "Stopping Docker Services"
        docker-compose down
        print_success "Docker services stopped"
        ;;
    
    docker-logs)
        print_header "Docker Service Logs"
        docker-compose logs -f
        ;;
    
    # ============ PYTHON OPTIMIZATION ENGINE ============
    
    generate)
        print_header "Generating Product Catalog (~100k products)"
        cd "$PYTHON_DIR"
        python main.py
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
        cd "$PYTHON_DIR"
        python --version
        print_success "Python ready"
        
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
  start          Start production app (builds frontend + runs backend)
                 → Opens http://localhost:18000 automatically
  dev            Start dev servers (frontend + backend)
                 → Frontend: http://localhost:3000 (with hot reload)
                 → Backend:  http://localhost:18000
  frontend       Start only frontend dev server (port 3000)
  backend        Start only backend server (port 18000)
  build          Build complete application for production

🐳 DOCKER COMMANDS:
  docker-up      Start all services with Docker Compose
                 → Frontend: http://localhost:8080
                 → API:      http://localhost:18000
                 → Database: localhost:5432
  docker-dev     Same as docker-up but force rebuild
  docker-down    Stop all Docker services
  docker-logs    Show Docker service logs

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