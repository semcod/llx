#!/bin/bash

# Docker Management Script for llx
# Provides easy commands to manage the Docker environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="llx"
COMPOSE_FILE="docker-compose.yml"
DEV_COMPOSE_FILE="docker-compose-dev.yml"
PROD_COMPOSE_FILE="docker-compose-prod.yml"

# Helper functions
print_header() {
    echo -e "${BLUE}🚀 llx Docker Management${NC}"
    echo "=================================="
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if docker-compose is available
check_compose() {
    if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
        print_error "docker-compose is not installed."
        exit 1
    fi
}

# Get docker-compose command
get_compose_cmd() {
    if docker compose version > /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Main commands
case "${1:-help}" in
    "dev"|"development")
        print_header
        echo "Starting development environment..."
        
        check_docker
        check_compose
        
        COMPOSE_CMD=$(get_compose_cmd)
        
        # Create necessary directories
        mkdir -p logs backups
        
        # Start development services
        $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev up -d
        
        print_status "Development environment started!"
        echo ""
        echo "Available services:"
        echo "  🤖 llx API:        http://localhost:4000"
        echo "  💬 WebUI:          http://localhost:3000"
        echo "  📝 VS Code:        http://localhost:8080"
        echo "  🔧 Ollama:         http://localhost:11434"
        echo "  🗄️  Redis:         localhost:6379"
        echo ""
        echo "To view logs: $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev logs -f"
        echo "To stop: $0 stop-dev"
        ;;

    "prod"|"production")
        print_header
        echo "Starting production environment..."
        
        check_docker
        check_compose
        
        COMPOSE_CMD=$(get_compose_cmd)
        
        # Create necessary directories
        mkdir -p logs backups/{postgres,redis,ollama,prometheus,nginx}
        
        # Check if .env.prod exists
        if [ ! -f ".env.prod" ]; then
            print_warning ".env.prod not found. Creating from .env..."
            cp .env .env.prod
            echo "Please edit .env.prod with production values before running again."
            exit 1
        fi
        
        # Start production services
        $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod up -d
        
        print_status "Production environment started!"
        echo ""
        echo "Available services:"
        echo "  🤖 llx API:        http://localhost:4000"
        echo "  💬 WebUI:          http://localhost:3000"
        echo "  📊 Grafana:        http://localhost:3001"
        echo "  📈 Prometheus:     http://localhost:9090"
        echo "  🗄️  PostgreSQL:     localhost:5432"
        echo "  🔧 Ollama:         http://localhost:11434"
        echo "  🗄️  Redis:         localhost:6379"
        echo ""
        echo "To view logs: $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod logs -f"
        echo "To stop: $0 stop-prod"
        ;;

    "stop"|"stop-all")
        print_header
        echo "Stopping all environments..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        
        # Stop all environments
        $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME down 2>/dev/null || true
        $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev down 2>/dev/null || true
        $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod down 2>/dev/null || true
        
        print_status "All environments stopped!"
        ;;

    "stop-dev")
        print_header
        echo "Stopping development environment..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev down
        
        print_status "Development environment stopped!"
        ;;

    "stop-prod")
        print_header
        echo "Stopping production environment..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod down
        
        print_status "Production environment stopped!"
        ;;

    "status"|"ps")
        print_header
        echo "Container status:"
        echo ""
        
        COMPOSE_CMD=$(get_compose_cmd)
        
        # Show status for all environments
        echo "🔵 Development:"
        $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev ps 2>/dev/null || echo "  Not running"
        echo ""
        echo "🟢 Production:"
        $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod ps 2>/dev/null || echo "  Not running"
        echo ""
        echo "🔵 Full:"
        $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME ps 2>/dev/null || echo "  Not running"
        ;;

    "logs")
        print_header
        echo "Showing logs..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        ENVIRONMENT="${2:-dev}"
        
        case $ENVIRONMENT in
            "dev"|"development")
                $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev logs -f "${3:-}"
                ;;
            "prod"|"production")
                $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod logs -f "${3:-}"
                ;;
            "full")
                $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME logs -f "${3:-}"
                ;;
            *)
                print_error "Unknown environment: $ENVIRONMENT"
                echo "Usage: $0 logs [dev|prod|full] [service_name]"
                exit 1
                ;;
        esac
        ;;

    "restart")
        print_header
        echo "Restarting services..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        ENVIRONMENT="${2:-dev}"
        SERVICE="${3:-}"
        
        case $ENVIRONMENT in
            "dev"|"development")
                if [ -n "$SERVICE" ]; then
                    $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev restart $SERVICE
                else
                    $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev restart
                fi
                ;;
            "prod"|"production")
                if [ -n "$SERVICE" ]; then
                    $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod restart $SERVICE
                else
                    $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod restart
                fi
                ;;
            *)
                print_error "Unknown environment: $ENVIRONMENT"
                echo "Usage: $0 restart [dev|prod] [service_name]"
                exit 1
                ;;
        esac
        
        print_status "Services restarted!"
        ;;

    "clean"|"cleanup")
        print_header
        echo "Cleaning up Docker resources..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        
        # Stop all containers
        $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME down 2>/dev/null || true
        $COMPOSE_CMD -f $DEV_COMPOSE_FILE -p ${PROJECT_NAME}-dev down 2>/dev/null || true
        $COMPOSE_CMD -f $PROD_COMPOSE_FILE -p ${PROJECT_NAME}-prod down 2>/dev/null || true
        
        # Remove containers
        docker container prune -f
        
        # Remove unused images
        docker image prune -f
        
        # Remove unused networks
        docker network prune -f
        
        # Ask about volumes
        read -p "Remove all volumes? This will delete all data! [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker volume prune -f
            print_status "Volumes removed!"
        else
            print_warning "Volumes preserved."
        fi
        
        print_status "Cleanup completed!"
        ;;

    "backup")
        print_header
        echo "Creating backups..."
        
        # Create backup directory
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # Backup PostgreSQL
        if docker ps | grep -q "llx-postgres"; then
            echo "📦 Backing up PostgreSQL..."
            docker exec llx-postgres-prod pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/postgres.sql
            print_status "PostgreSQL backed up!"
        fi
        
        # Backup Redis
        if docker ps | grep -q "llx-redis"; then
            echo "📦 Backing up Redis..."
            docker exec llx-redis-prod redis-cli BGSAVE
            sleep 5
            docker cp llx-redis-prod:/data/dump.rdb $BACKUP_DIR/redis.rdb
            print_status "Redis backed up!"
        fi
        
        # Backup Ollama models
        if docker ps | grep -q "llx-ollama"; then
            echo "📦 Backing up Ollama models..."
            docker cp llx-ollama-prod:/root/.ollama $BACKUP_DIR/ollama
            print_status "Ollama models backed up!"
        fi
        
        # Backup configuration files
        cp .env $BACKUP_DIR/ 2>/dev/null || true
        cp llx.yaml $BACKUP_DIR/ 2>/dev/null || true
        cp litellm-config.yaml $BACKUP_DIR/ 2>/dev/null || true
        
        print_status "Backup completed: $BACKUP_DIR"
        ;;

    "update")
        print_header
        echo "Updating services..."
        
        COMPOSE_CMD=$(get_compose_cmd)
        
        # Pull latest images
        echo "📦 Pulling latest images..."
        $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME pull
        
        # Rebuild llx image
        echo "🔨 Rebuilding llx image..."
        docker build -t llx:latest .
        
        # Restart services
        echo "🔄 Restarting services..."
        $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME up -d --force-recreate
        
        print_status "Services updated!"
        ;;

    "install-tools")
        print_header
        echo "Installing local tools..."
        
        # Check if tools are already installed
        if command -v ollama > /dev/null 2>&1; then
            print_warning "Ollama is already installed locally"
        else
            echo "📦 Installing Ollama locally..."
            curl -fsSL https://ollama.ai/install.sh | sh
            print_status "Ollama installed!"
        fi
        
        # Install Redis CLI if not present
        if command -v redis-cli > /dev/null 2>&1; then
            print_warning "Redis CLI is already installed"
        else
            echo "📦 Installing Redis CLI..."
            if command -v apt-get > /dev/null 2>&1; then
                sudo apt-get update && sudo apt-get install -y redis-tools
            elif command -v brew > /dev/null 2>&1; then
                brew install redis
            else
                print_warning "Please install Redis CLI manually"
            fi
        fi
        
        print_status "Local tools installation completed!"
        ;;

    "help"|*)
        print_header
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  dev                 Start development environment"
        echo "  prod                Start production environment"
        echo "  stop                Stop all environments"
        echo "  stop-dev            Stop development environment"
        echo "  stop-prod           Stop production environment"
        echo "  status              Show container status"
        echo "  logs [env] [svc]    Show logs (env: dev|prod|full)"
        echo "  restart [env] [svc] Restart services"
        echo "  clean               Clean up Docker resources"
        echo "  backup              Create backups"
        echo "  update              Update and rebuild services"
        echo "  install-tools       Install local tools"
        echo "  help                Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 dev              # Start development"
        echo "  $0 logs dev llx-api  # Show llx-api logs in dev"
        echo "  $0 restart prod     # Restart production"
        echo "  $0 backup           # Create backup"
        ;;
esac
