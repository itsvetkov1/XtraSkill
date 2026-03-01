#!/bin/bash
# =============================================================================
# XtraSkill Deployment Script
# =============================================================================
# Usage:
#   ./deploy.sh           # Start dev environment
#   ./deploy.sh start    # Start services
#   ./deploy.sh stop     # Stop services
#   ./deploy.sh restart  # Restart services
#   ./deploy.sh logs     # View logs
#   ./deploy.sh status   # Show container status
#   ./deploy.sh build    # Rebuild images
#   ./deploy.sh clean    # Remove containers and volumes
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD_FILE="docker-compose.prod.yml"

# Parse arguments
COMMAND="${1:-start}"
ENV="${2:-dev}"

# Determine compose file
if [ "$ENV" = "prod" ]; then
    COMPOSE_FILES="-f $COMPOSE_PROD_FILE"
    echo -e "${BLUE}Using production configuration${NC}"
else
    COMPOSE_FILES=""
    echo -e "${BLUE}Using development configuration${NC}"
fi

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed."
        exit 1
    fi
}

check_env() {
    if [ ! -f .env ]; then
        log_warn ".env file not found. Creating from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            log_info "Created .env file. Please edit it with your API keys."
        else
            log_error ".env.example not found!"
            exit 1
        fi
    fi
}

start() {
    log_info "Starting XtraSkill services..."
    docker compose $COMPOSE_FILES up -d
    log_info "Services started!"
    show_status
}

stop() {
    log_info "Stopping XtraSkill services..."
    docker compose $COMPOSE_FILES down
    log_info "Services stopped."
}

restart() {
    stop
    sleep 2
    start
}

build() {
    log_info "Building Docker images..."
    docker compose $COMPOSE_FILES build --no-cache
    log_info "Build complete!"
}

logs() {
    docker compose $COMPOSE_FILES logs -f --tail=50
}

status() {
    show_status
}

show_status() {
    echo ""
    echo "=============================================="
    echo "           XtraSkill Status"
    echo "=============================================="
    echo ""
    
    # Check if docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running!"
        exit 1
    fi
    
    # Show container status
    docker compose $COMPOSE_FILES ps
    
    echo ""
    echo "=============================================="
    echo "           Service URLs"
    echo "=============================================="
    echo ""
    echo "  Backend API:    http://localhost:8000"
    echo "  Health Check:  http://localhost:8000/health"
    echo "  OpenClaw:      http://localhost:8080"
    echo ""
    echo "  PostgreSQL:     localhost:5432 (prod only)"
    echo ""
}

clean() {
    log_warn "This will remove all containers and volumes!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        log_info "Cleaning up..."
        docker compose $COMPOSE_FILES down -v --remove-orphans
        log_info "Cleanup complete!"
    else
        log_info "Cancelled."
    fi
}

help() {
    echo "XtraSkill Deployment Script"
    echo ""
    echo "Usage: $0 [command] [environment]"
    echo ""
    echo "Commands:"
    echo "  start    - Start services (default)"
    echo "  stop     - Stop services"
    echo "  restart  - Restart services"
    echo "  build    - Rebuild Docker images"
    echo "  logs     - View logs (follow mode)"
    echo "  status   - Show container status"
    echo "  clean    - Remove containers and volumes"
    echo "  help     - Show this help"
    echo ""
    echo "Environment:"
    echo "  dev      - Development (SQLite, default)"
    echo "  prod     - Production (PostgreSQL)"
    echo ""
    echo "Examples:"
    echo "  $0 start           # Start dev environment"
    echo "  $0 start prod      # Start production"
    echo "  $0 logs            # View logs"
    echo "  $0 build           # Rebuild images"
    echo ""
}

# Main
check_docker
check_env

case "$COMMAND" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    build)
        build
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        help
        exit 1
        ;;
esac
