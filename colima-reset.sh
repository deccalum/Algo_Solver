#!/bin/bash

# Algo Solver - Colima Emergency Fix
# Clears all running instances and resets Colima

set -e

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

print_header "Colima Emergency Reset"

print_info "Step 1: Kill any dangling Docker processes..."
killall docker-proxy 2>/dev/null || true
killall docker 2>/dev/null || true
print_success "Killed docker processes"

print_info "Step 2: Stop Colima..."
colima stop 2>/dev/null || print_error "Colima not running (that's ok)"

print_info "Step 3: Wait 3 seconds..."
sleep 3
print_success "Done waiting"

print_info "Step 4: Remove stale socket if present..."
rm -f ~/.colima/default/docker.sock 2>/dev/null || true
print_success "Cleaned up socket"

print_info "Step 5: Starting fresh Colima..."
colima start

print_success "Waiting for Docker daemon..."
sleep 5

print_info "Step 6: Verify Docker is working..."
if docker ps &> /dev/null; then
    print_success "Docker daemon is responding!"
else
    print_error "Docker still not responding"
    echo "Try running: colima status"
    exit 1
fi

print_header "Reset Complete!"
echo -e "${GREEN}Ready to start services:${NC}"
echo ""
echo -e "  ${YELLOW}./colima-setup.sh up${NC}"
echo ""
