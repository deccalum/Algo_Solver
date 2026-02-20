#!/bin/bash

# Algo Solver - Full Stack Application Runner
# Combines Python optimization engine with Java Spring Boot + React frontend

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_DIR="$SCRIPT_DIR/python"
DATA_DIR="$SCRIPT_DIR/data/output"
JAVA_DIR="$SCRIPT_DIR/java"
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
        print_success "Frontend built to java/src/main/resources/static"
        
        print_info "Starting Spring Boot server..."
        cd "$JAVA_DIR"
        mvn spring-boot:run
        # Browser auto-opens at http://localhost:8080
        ;;
    
    dev)
        print_header "Starting Development Servers"
        print_info "This will start:"
        print_info "  • Frontend dev server: http://localhost:3000"
        print_info "  • Backend API server:  http://localhost:8080"
        print_info ""
        print_info "Starting backend first..."
        
        cd "$JAVA_DIR"
        mvn spring-boot:run &
        BACKEND_PID=$!
        
        sleep 5
        print_success "Backend running (PID: $BACKEND_PID)"
        
        print_info "Starting frontend..."
        cd "$FRONTEND_DIR"
        npm run dev
        
        # Cleanup on exit
        kill $BACKEND_PID 2>/dev/null || true
        ;;
    
    frontend)
        print_header "Starting Frontend Dev Server Only"
        print_info "Dev server: http://localhost:3000"
        print_info "API proxy:  http://localhost:8080"
        cd "$FRONTEND_DIR"
        npm run dev
        ;;
    
    backend)
        print_header "Starting Backend API Server Only"
        print_info "Spring Boot: http://localhost:8080"
        print_info "Browser will auto-open"
        cd "$JAVA_DIR"
        mvn spring-boot:run
        ;;
    
    build)
        print_header "Building Full Application"
        
        print_info "Installing frontend dependencies..."
        cd "$FRONTEND_DIR"
        npm install
        
        print_info "Building frontend for production..."
        npm run build
        print_success "Frontend built → java/src/main/resources/static/"
        
        print_info "Building Spring Boot application..."
        cd "$JAVA_DIR"
        mvn clean package -DskipTests
        print_success "Backend packaged → java/target/Algo_Solver-1.0.jar"
        
        print_header "Build Complete"
        print_info "Run with: ./run.sh start"
        print_info "Or JAR:   java -jar java/target/Algo_Solver-1.0.jar"
        ;;
    
    # ============ PYTHON OPTIMIZATION ENGINE ============
    
    generate)
        print_header "Generating Product Catalog (~100k products)"
        cd "$PYTHON_DIR"
        python3 main.py
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
        
        print_info "Verifying Maven..."
        cd "$JAVA_DIR"
        mvn --version
        print_success "Maven ready"
        
        print_info "Verifying Python..."
        cd "$PYTHON_DIR"
        python3 --version
        print_success "Python ready"
        
        print_header "All Dependencies Ready"
        ;;
    
    clean)
        print_header "Cleaning Build Artifacts"
        
        print_info "Cleaning frontend..."
        cd "$FRONTEND_DIR"
        rm -rf dist node_modules
        
        print_info "Cleaning backend..."
        cd "$JAVA_DIR"
        mvn clean
        rm -rf src/main/resources/static/*
        
        print_info "Cleaning Python cache..."
        cd "$PYTHON_DIR"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        
        print_success "All build artifacts cleaned"
        ;;
    
    *)
        cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                    ALGO SOLVER - RUNNER                        ║
║          Python Optimization + Spring Boot + React             ║
╚════════════════════════════════════════════════════════════════╝

Usage: ./run.sh [command]

📦 FULL-STACK COMMANDS:
  start          Start production app (builds frontend + runs backend)
                 → Opens http://localhost:8080 automatically
  
  dev            Start dev servers (frontend + backend)
                 → Frontend: http://localhost:3000 (with hot reload)
                 → Backend:  http://localhost:8080
  
  frontend       Start only frontend dev server (port 3000)
  backend        Start only backend server (port 8080)
  build          Build complete application for production
  
🐍 PYTHON OPTIMIZATION ENGINE:
  generate       Generate product catalog (~100k products)
  results        Show generated data files

🛠️  UTILITIES:
  install        Install all dependencies (npm + verify Maven/Python)
  clean          Remove all build artifacts

💡 QUICK START:
  ./run.sh install       # First time only
  ./run.sh dev           # Development mode
  ./run.sh generate      # Generate product data
  
  Or production:
  ./run.sh build         # Build everything
  ./run.sh start         # Run production app (auto-opens browser)

📚 CONFIGURATION:
  - Python engine:  config/app.yaml
  - Spring Boot:    java/src/main/resources/application.properties
  - Frontend:       frontend/vite.config.js
  
🌐 URLs:
  Production:  http://localhost:8080  (Spring Boot serves React)
  Development: http://localhost:3000  (Vite dev server with HMR)
               http://localhost:8080  (Spring Boot API)

⚙️  DISABLE AUTO-BROWSER:
  Edit java/src/main/resources/application.properties:
    app.open-browser=false
EOF
        ;;
esac
