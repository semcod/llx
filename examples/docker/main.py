#!/usr/bin/env python3
"""
llx Docker Integration Example

This example demonstrates:
1. Using llx with Docker services
2. Connecting to Redis, Ollama, and PostgreSQL
3. Running in containerized environment
4. Health checks and service discovery
"""

import os
import sys
import time
import requests
import redis
from pathlib import Path

# Add llx to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx import analyze_project, select_model, LlxConfig, ProjectMetrics


def check_service_health(service_name, url, timeout=5):
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"   ✓ {service_name} is healthy")
            return True
        else:
            print(f"   ❌ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {service_name} is unreachable: {e}")
        return False


def check_redis_connection():
    """Check Redis connection"""
    try:
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=5
        )
        redis_client.ping()
        print(f"   ✓ Redis connection successful")
        return True, redis_client
    except redis.ConnectionError as e:
        print(f"   ❌ Redis connection failed: {e}")
        return False, None


def check_ollama_connection():
    """Check Ollama connection"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"   ✓ Ollama connected with {len(models)} models")
            return True, models
        else:
            print(f"   ❌ Ollama returned status {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ollama connection failed: {e}")
        return False, None


def demonstrate_docker_integration():
    """Demonstrate llx integration with Docker services"""
    print("🐳 Docker Integration Demo")
    print("=" * 40)
    
    # Check if we're running in Docker
    in_docker = os.path.exists('/.dockerenv')
    if in_docker:
        print("📦 Running inside Docker container")
    else:
        print("🖥️  Running on host machine")
    
    print("\n🔍 Checking service health...")
    
    # Check llx API
    llx_healthy = check_service_health(
        "llx API", 
        "http://localhost:4000/health"
    )
    
    # Check Redis
    redis_ok, redis_client = check_redis_connection()
    
    # Check Ollama
    ollama_ok, ollama_models = check_ollama_connection()
    
    # Check WebUI
    webui_healthy = check_service_health(
        "WebUI",
        "http://localhost:3000"
    )
    
    # Check Grafana
    grafana_healthy = check_service_health(
        "Grafana",
        "http://localhost:3001/api/health"
    )
    
    return {
        'llx_api': llx_healthy,
        'redis': redis_ok,
        'ollama': ollama_ok,
        'webui': webui_healthy,
        'grafana': grafana_healthy
    }


def demonstrate_redis_usage(redis_client):
    """Demonstrate Redis caching with llx"""
    print("\n💾 Redis Caching Demo")
    print("=" * 25)
    
    if not redis_client:
        print("❌ Redis not available for demo")
        return
    
    # Cache a project analysis result
    project_path = "/app" if os.path.exists('/app') else "."
    cache_key = f"llx:analysis:{hash(project_path)}"
    
    try:
        # Check if result is cached
        cached_result = redis_client.get(cache_key)
        if cached_result:
            print("   ✓ Found cached analysis result")
            print(f"   📊 Cache hit: {cached_result}")
        else:
            print("   📝 No cached result, performing analysis...")
            
            # Perform analysis (simplified for demo)
            try:
                metrics = analyze_project(project_path)
                cache_value = f"files={metrics.total_files},lines={metrics.total_lines}"
                
                # Cache for 1 hour
                redis_client.setex(cache_key, 3600, cache_value)
                print(f"   💾 Cached analysis result: {cache_value}")
                
            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
                return
        
        # Show Redis info
        redis_info = redis_client.info()
        print(f"   📈 Redis memory used: {redis_info['used_memory_human']}")
        print(f"   🔢 Redis keys: {redis_info['db0']['keys']}")
        
    except Exception as e:
        print(f"   ❌ Redis demo failed: {e}")


def demonstrate_ollama_integration(ollama_models):
    """Demonstrate Ollama integration with llx"""
    print("\n🤖 Ollama Integration Demo")
    print("=" * 30)
    
    if not ollama_models:
        print("❌ Ollama not available for demo")
        return
    
    print(f"   📦 Available models: {len(ollama_models)}")
    
    # Show first few models
    for i, model in enumerate(ollama_models[:3]):
        name = model.get('name', 'Unknown')
        size = model.get('size', 0)
        size_gb = size / (1024**3) if size else 0
        print(f"     • {name} ({size_gb:.1f}GB)")
    
    # Try to use local model in llx
    try:
        project_path = "/app" if os.path.exists('/app') else "."
        config = LlxConfig.load(project_path)
        
        # Force local model selection
        print("\n   🎯 Testing local model selection...")
        
        # This would normally use the local models
        print(f"   ✓ Local models configured: {len(config.litellm_config.model_list)}")
        
        # Show local model configuration
        local_models = config.litellm_config.get_models_by_provider('ollama')
        for model in local_models:
            print(f"     • {model.model_name} - {', '.join(model.tags)}")
            
    except Exception as e:
        print(f"   ❌ Ollama integration test failed: {e}")


def demonstrate_container_metrics():
    """Demonstrate collecting container metrics"""
    print("\n📊 Container Metrics Demo")
    print("=" * 30)
    
    if os.path.exists('/sys/fs/cgroup'):
        print("   📦 Running in container with cgroups available")
        
        # Read memory usage
        try:
            with open('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r') as f:
                memory_bytes = int(f.read().strip())
                memory_mb = memory_bytes / (1024 * 1024)
                print(f"   💾 Memory usage: {memory_mb:.1f} MB")
        except:
            print("   ❌ Could not read memory usage")
        
        # Read CPU usage
        try:
            with open('/sys/fs/cgroup/cpu/cpuacct.usage', 'r') as f:
                cpu_usage_ns = int(f.read().strip())
                cpu_usage_ms = cpu_usage_ns / 1000000
                print(f"   ⚡ CPU usage: {cpu_usage_ms:.0f} ms")
        except:
            print("   ❌ Could not read CPU usage")
    else:
        print("   🖥️  Not running in container or cgroups not available")
    
    # Show environment variables
    print("\n   🔧 Environment variables:")
    docker_vars = ['DOCKER_HOST', 'CONTAINER_NAME', 'LLX_PROXY_HOST', 'REDIS_URL']
    for var in docker_vars:
        value = os.getenv(var, 'Not set')
        print(f"     • {var}: {value}")


def demonstrate_service_discovery():
    """Demonstrate service discovery in Docker network"""
    print("\n🔍 Service Discovery Demo")
    print("=" * 35)
    
    # Check if we can resolve Docker service names
    services_to_check = [
        ('llx-api', 4000),
        ('redis', 6379),
        ('ollama', 11434),
        ('postgres', 5432)
    ]
    
    print("   🔍 Checking service resolution...")
    
    for service_name, port in services_to_check:
        try:
            # Try to connect to the service
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((service_name, port))
            sock.close()
            
            if result == 0:
                print(f"   ✓ {service_name}:{port} reachable")
            else:
                print(f"   ❌ {service_name}:{port} not reachable")
        except Exception as e:
            print(f"   ❌ {service_name}:{port} error: {e}")


def main():
    """Main Docker integration example"""
    print("🚀 llx Docker Integration Example")
    print("=" * 50)
    
    # Check Docker environment
    health_status = demonstrate_docker_integration()
    
    # Demonstrate Redis if available
    if health_status['redis']:
        _, redis_client = check_redis_connection()
        demonstrate_redis_usage(redis_client)
    
    # Demonstrate Ollama if available
    if health_status['ollama']:
        _, ollama_models = check_ollama_connection()
        demonstrate_ollama_integration(ollama_models)
    
    # Show container metrics
    demonstrate_container_metrics()
    
    # Show service discovery
    demonstrate_service_discovery()
    
    # Summary
    print("\n📋 Docker Integration Summary")
    print("=" * 35)
    
    healthy_services = [k for k, v in health_status.items() if v]
    unhealthy_services = [k for k, v in health_status.items() if not v]
    
    print(f"   ✅ Healthy services: {', '.join(healthy_services)}")
    if unhealthy_services:
        print(f"   ❌ Unhealthy services: {', '.join(unhealthy_services)}")
    
    # Docker-specific tips
    print("\n💡 Docker Usage Tips:")
    print("   • Use 'docker-manage.sh dev' to start development stack")
    print("   • Use 'docker-manage.sh logs dev' to view logs")
    print("   • Use 'docker-manage.sh status' to check status")
    print("   • Use 'docker-manage.sh backup' to create backups")
    print("   • Access services via service names in Docker network")
    print("   • Use environment variables for configuration")
    
    print("\n✅ Docker integration example completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
