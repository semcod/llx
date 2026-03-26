#!/bin/bash
# LLX Docker Integration - Bash version
# Demonstrates LLX with Docker services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
COMMAND=""
COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="llx-demo"
SERVICE=""
VERBOSE=false

# Help function
show_help() {
    cat << EOF
LLX Docker Integration

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start           Start Docker services
    stop            Stop Docker services
    status          Check service status
    logs            Show service logs
    exec            Execute LLX in container
    test            Run integration tests
    clean           Clean up containers and volumes

Options:
    -f, --file FILE        Docker compose file [default: docker-compose.yml]
    -p, --project NAME     Project name [default: llx-demo]
    -s, --service SERVICE  Specific service
    -v, --verbose          Verbose output
    -h, --help             Show this help

Services:
    ollama         Local LLM server
    redis          Cache and queue
    postgres       Database
    llx            LLX application

Examples:
    $0 start                    # Start all services
    $0 status                   # Check all services
    $0 exec --service ollama    # Execute in ollama container
    $0 logs --service redis     # Show redis logs
    $0 test                     # Run integration tests

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|status|logs|exec|test|clean)
            COMMAND="$1"
            shift
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

# Determine docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Build docker command
build_docker_cmd() {
    local cmd="$DOCKER_COMPOSE"
    [ -f "$COMPOSE_FILE" ] && cmd="$cmd -f $COMPOSE_FILE"
    cmd="$cmd -p $PROJECT_NAME"
    echo "$cmd"
}

# Service health check
check_service_health() {
    local service="$1"
    local url="$2"
    
    echo -e "${CYAN}Checking $service...${NC}"
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✓ $service is healthy${NC}"
        return 0
    else
        echo -e "${RED}   ❌ $service is unhealthy${NC}"
        return 1
    fi
}

# Check Redis connection
check_redis() {
    echo -e "${CYAN}Checking Redis connection...${NC}"
    
    if docker exec "${PROJECT_NAME}_redis_1" redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "${GREEN}   ✓ Redis connection successful${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Redis connection failed${NC}"
        return 1
    fi
}

# Check PostgreSQL connection
check_postgres() {
    echo -e "${CYAN}Checking PostgreSQL connection...${NC}"
    
    if docker exec "${PROJECT_NAME}_postgres_1" pg_isready -U postgres 2>/dev/null; then
        echo -e "${GREEN}   ✓ PostgreSQL is ready${NC}"
        return 0
    else
        echo -e "${RED}   ❌ PostgreSQL is not ready${NC}"
        return 1
    fi
}

# Main functions
docker_start() {
    echo -e "${BLUE}🚀 Starting Docker services...${NC}"
    
    DOCKER_CMD=$(build_docker_cmd)
    $DOCKER_CMD up -d
    
    if [ "$VERBOSE" = true ]; then
        echo
        $DOCKER_CMD ps
    fi
    
    echo -e "${GREEN}✅ Services started${NC}"
}

docker_stop() {
    echo -e "${BLUE}🛑 Stopping Docker services...${NC}"
    
    DOCKER_CMD=$(build_docker_cmd)
    $DOCKER_CMD down
    
    echo -e "${GREEN}✅ Services stopped${NC}"
}

docker_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo
    
    DOCKER_CMD=$(build_docker_cmd)
    $DOCKER_CMD ps
    
    echo
    echo -e "${CYAN}Health Checks:${NC}"
    
    # Check individual services
    check_service_health "Ollama" "http://localhost:11434/api/tags"
    check_redis
    check_postgres
}

docker_logs() {
    DOCKER_CMD=$(build_docker_cmd)
    
    if [ -n "$SERVICE" ]; then
        echo -e "${BLUE}📋 Logs for $SERVICE:${NC}"
        $DOCKER_CMD logs -f "$SERVICE"
    else
        echo -e "${BLUE}📋 Logs for all services:${NC}"
        $DOCKER_CMD logs -f
    fi
}

docker_exec() {
    if [ -z "$SERVICE" ]; then
        echo -e "${RED}Error: Service required for exec. Use -s SERVICE${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}🔧 Executing in $SERVICE...${NC}"
    
    DOCKER_CMD=$(build_docker_cmd)
    $DOCKER_CMD exec "$SERVICE" /bin/bash
}

docker_test() {
    echo -e "${BLUE}🧪 Running integration tests...${NC}"
    echo
    
    # Test service connectivity
    echo -e "${CYAN}1. Testing service connectivity...${NC}"
    docker_status
    
    echo
    echo -e "${CYAN}2. Testing LLX with Ollama...${NC}"
    
    # Check if LLX is available
    if command -v llx &> /dev/null; then
        # Test with local model
        response=$(llx chat --local --task test --prompt "Hello Docker!" 2>/dev/null || echo "Failed")
        if [ "$response" != "Failed" ]; then
            echo -e "${GREEN}   ✓ LLX + Ollama integration working${NC}"
        else
            echo -e "${RED}   ❌ LLX + Ollama integration failed${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠ LLX not installed locally${NC}"
    fi
    
    echo
    echo -e "${CYAN}3. Testing container communication...${NC}"
    
    # Test Redis from LLX container
    if docker exec "${PROJECT_NAME}_llx_1" python -c "import redis; r=redis.Redis('redis'); r.ping()" 2>/dev/null; then
        echo -e "${GREEN}   ✓ LLX can reach Redis${NC}"
    else
        echo -e "${RED}   ❌ LLX cannot reach Redis${NC}"
    fi
    
    echo
    echo -e "${GREEN}✅ Integration tests completed${NC}"
}

docker_clean() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    
    DOCKER_CMD=$(build_docker_cmd)
    
    # Stop and remove containers
    $DOCKER_CMD down -v --remove-orphans
    
    # Remove images
    echo -e "${CYAN}Removing images...${NC}"
    docker images | grep "$PROJECT_NAME" | awk '{print $3}' | xargs -r docker rmi -f
    
    # Clean up volumes
    echo -e "${CYAN}Cleaning volumes...${NC}"
    docker volume prune -f
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Create docker-compose file if it doesn't exist
create_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${YELLOW}Creating $COMPOSE_FILE...${NC}"
        
        cat > "$COMPOSE_FILE" << EOF
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: llx_demo
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  llx:
    image: python:3.11-slim
    depends_on:
      - ollama
      - redis
      - postgres
    volumes:
      - ../..:/app
    working_dir: /app
    command: tail -f /dev/null
    environment:
      - LLX_LITELLM_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/llx_demo

volumes:
  ollama_data:
  redis_data:
  postgres_data:
EOF
        
        echo -e "${GREEN}✅ Created $COMPOSE_FILE${NC}"
    fi
}

# Main execution
main() {
    # Check if command provided
    if [ -z "$COMMAND" ]; then
        echo -e "${RED}Error: No command specified${NC}"
        show_help
        exit 1
    fi
    
    # Create compose file if needed
    create_compose_file
    
    # Execute command
    case $COMMAND in
        start)
            docker_start
            ;;
        stop)
            docker_stop
            ;;
        status)
            docker_status
            ;;
        logs)
            docker_logs
            ;;
        exec)
            docker_exec
            ;;
        test)
            docker_test
            ;;
        clean)
            docker_clean
            ;;
        *)
            echo -e "${RED}Unknown command: $COMMAND${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main
