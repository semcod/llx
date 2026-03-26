# llx Docker Integration Example

This example demonstrates how to use llx with Docker services, including Redis caching, Ollama local models, and monitoring with Grafana.

## What it does

1. **Docker Environment Detection**: Checks if running inside Docker or on host
2. **Service Health Monitoring**: Tests connectivity to all Docker services
3. **Redis Integration**: Demonstrates caching of analysis results
4. **Ollama Integration**: Shows local model usage and configuration
5. **Container Metrics**: Collects resource usage from cgroups
6. **Service Discovery**: Tests Docker network name resolution

## Architecture

```
Docker Network (172.20.0.0/16)
├── llx-api (4000)           # Main API server
├── redis (6379)              # Caching and session storage
├── ollama (11434)            # Local LLM models
├── postgres (5432)           # Data persistence
├── webui (3000)              # Web interface
├── grafana (3001)            # Monitoring dashboard
├── prometheus (9090)         # Metrics collection
├── nginx (80/443)            # Reverse proxy
└── vscode (8080)             # Development IDE
```

## Prerequisites

- Docker and docker-compose installed
- Docker daemon running
- At least one llx Docker stack running

## Quick Start

### 1. Start Development Stack
```bash
# Using the management script
./docker-manage.sh dev

# Or manually
docker-compose -f docker-compose-dev.yml up -d
```

### 2. Run the Example
```bash
cd examples/docker
./run.sh
```

### 3. Check Results
The example will:
- Test connectivity to all services
- Demonstrate Redis caching
- Show Ollama model integration
- Display container metrics
- Test service discovery

## Docker Management Commands

### Environment Management
```bash
./docker-manage.sh dev              # Start development stack
./docker-manage.sh prod             # Start production stack
./docker-manage.sh stop             # Stop all environments
./docker-manage.sh stop-dev         # Stop development only
./docker-manage.sh stop-prod        # Stop production only
```

### Monitoring and Logs
```bash
./docker-manage.sh status           # Show container status
./docker-manage.sh logs dev          # View development logs
./docker-manage.sh logs prod         # View production logs
./docker-manage.sh logs dev llx-api # View specific service logs
```

### Maintenance
```bash
./docker-manage.sh restart dev       # Restart services
./docker-manage.sh backup            # Create backups
./docker-manage.sh clean             # Clean up resources
./docker-manage.sh update            # Update and rebuild
```

## Service URLs

When running, services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| **llx API** | http://localhost:4000 | Main API server |
| **WebUI** | http://localhost:3000 | Chat interface |
| **Grafana** | http://localhost:3001 | Monitoring dashboard |
| **Prometheus** | http://localhost:9090 | Metrics storage |
| **VS Code** | http://localhost:8080 | Development IDE |
| **Ollama** | http://localhost:11434 | Local models API |
| **Redis** | localhost:6379 | Cache server |
| **PostgreSQL** | localhost:5432 | Database |

## Configuration Files

### docker-compose.yml
Full production stack with:
- All services enabled
- Resource limits
- Health checks
- Persistent volumes
- Monitoring integration

### docker-compose-dev.yml
Development stack with:
- Essential services only
- Hot reload enabled
- Development tools
- Debug logging

### docker-compose-prod.yml
Production optimized stack with:
- Resource constraints
- Backup integration
- Security hardening
- Performance tuning

## Service Integration

### Redis Caching
```python
# Cache analysis results
cache_key = f"llx:analysis:{hash(project_path)}"
redis_client.setex(cache_key, 3600, analysis_result)
```

### Ollama Local Models
```python
# Use local models in Docker network
ollama_url = "http://ollama:11434/api/generate"
response = requests.post(ollama_url, json=model_request)
```

### Container Metrics
```python
# Read from cgroups (inside container)
with open('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r') as f:
    memory_bytes = int(f.read().strip())
```

## Development Workflow

### 1. Local Development
```bash
# Start development stack
./docker-manage.sh dev

# Work in VS Code
xdg-open http://localhost:8080

# Test changes
cd examples/docker && ./run.sh
```

### 2. Production Deployment
```bash
# Start production stack
./docker-manage.sh prod

# Monitor services
xdg-open http://localhost:3001  # Grafana
xdg-open http://localhost:9090  # Prometheus

# Check logs
./docker-manage.sh logs prod
```

### 3. Service Updates
```bash
# Update images and rebuild
./docker-manage.sh update

# Restart with new images
./docker-manage.sh restart prod
```

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using ports
netstat -tuln | grep -E ":(4000|3000|11434|6379|5432)"

# Use different ports in docker-compose.yml
```

**Service not starting:**
```bash
# Check logs
./docker-manage.sh logs dev [service_name]

# Check health status
docker ps
docker inspect [container_name]
```

**Network issues:**
```bash
# Check Docker network
docker network ls
docker network inspect llx_llx-network

# Test connectivity
docker exec llx-api-dev ping redis
```

**Resource limits:**
```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
```

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export DEBUG=true

# Or in docker-compose.yml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
```

## Performance Optimization

### Resource Allocation
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### Caching Strategy
```yaml
# Redis configuration
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Database Optimization
```yaml
postgres:
  environment:
    POSTGRES_SHARED_PRELOAD_LIBRARIES: pg_stat_statements
  command: postgres -c shared_preload_libraries=pg_stat_statements
```

## Security Considerations

### Network Security
```yaml
# Use internal networks for sensitive services
networks:
  internal:
    driver: bridge
    internal: true
```

### Environment Variables
```bash
# Use .env file for secrets
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
LLX_PROXY_MASTER_KEY=${LLX_PROXY_MASTER_KEY}
```

### Container Security
```yaml
# Run as non-root user
user: "1000:1000"
read_only: true
tmpfs:
  - /tmp
  - /var/tmp
```

## Backup and Recovery

### Automated Backups
```bash
# Create backup
./docker-manage.sh backup

# Restore from backup
docker exec postgres psql -U llx -d llx < backup/postgres.sql
```

### Volume Management
```bash
# List volumes
docker volume ls | grep llx

# Backup volumes
docker run --rm -v llx_ollama_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/ollama-backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v llx_ollama_data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/ollama-backup.tar.gz -C /data
```

## Monitoring and Alerting

### Grafana Dashboards
- API response times and error rates
- Resource usage (CPU, memory, disk)
- Request volume and patterns
- Model performance metrics

### Prometheus Metrics
```python
# Custom metrics in llx
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('llx_requests_total', 'Total requests', ['model', 'provider'])
REQUEST_DURATION = Histogram('llx_request_duration_seconds', 'Request duration')
```

### Health Checks
```bash
# API health endpoint
curl http://localhost:4000/health

# Service-specific checks
docker exec llx-api curl -f http://localhost:4000/health
```

## Scaling and Load Balancing

### Horizontal Scaling
```bash
# Scale API service
docker-compose -f docker-compose.yml up -d --scale llx-api=3
```

### Load Balancing with Nginx
```nginx
upstream llx_api {
    server llx-api-1:4000;
    server llx-api-2:4000;
    server llx-api-3:4000;
}
```

## Next Steps

- Try the [Basic Example](../basic/) for core functionality
- Explore the [Multi-Provider Example](../multi-provider/) for advanced routing
- Check the [Local Models Example](../local/) for offline usage
- Read the main [llx Documentation](../../README.md)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Redis Documentation](https://redis.io/documentation)
- [Ollama Documentation](https://ollama.ai/documentation)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
