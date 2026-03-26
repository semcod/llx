"""
Instance Manager for llx Orchestration
Manages Docker instances for VS Code and AI tools with dynamic port allocation.
"""

import os
import sys
import json
import time
import uuid
import threading
import socket
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import docker
import requests


class InstanceType(Enum):
    """Types of instances."""
    VSCODE = "vscode"
    AI_TOOLS = "ai_tools"
    LLM_PROXY = "llm_proxy"


class InstanceStatus(Enum):
    """Instance status."""
    CREATING = "creating"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class InstanceConfig:
    """Configuration for an instance."""
    instance_id: str
    instance_type: InstanceType
    account: str
    provider: str
    port: int
    image: str
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    auto_start: bool = True
    auto_restart: bool = True
    max_uptime_hours: int = 24
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstanceState:
    """Current state of an instance."""
    instance_id: str
    status: InstanceStatus
    container_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    last_used: datetime
    stopped_at: Optional[datetime]
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_usage: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    health_check_url: Optional[str] = None
    health_status: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstanceManager:
    """Manages multiple Docker instances with intelligent allocation and monitoring."""
    
    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "instances.json"
        self.instances: Dict[str, InstanceConfig] = {}
        self.instance_states: Dict[str, InstanceState] = {}
        self.port_allocator = PortAllocator()
        self.lock = threading.RLock()
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"❌ Docker client initialization failed: {e}")
            self.docker_client = None
        
        # Load existing instances
        self.load_instances()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
    
    def load_instances(self) -> bool:
        """Load instances from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load instance configurations
                for instance_data in data.get("instances", []):
                    config = InstanceConfig(
                        instance_id=instance_data["instance_id"],
                        instance_type=InstanceType(instance_data["instance_type"]),
                        account=instance_data["account"],
                        provider=instance_data["provider"],
                        port=instance_data["port"],
                        image=instance_data["image"],
                        environment=instance_data.get("environment", {}),
                        volumes=instance_data.get("volumes", {}),
                        networks=instance_data.get("networks", []),
                        auto_start=instance_data.get("auto_start", True),
                        auto_restart=instance_data.get("auto_restart", True),
                        max_uptime_hours=instance_data.get("max_uptime_hours", 24),
                        metadata=instance_data.get("metadata", {})
                    )
                    self.instances[config.instance_id] = config
                    
                    # Load or create instance state
                    state_data = data.get("states", {}).get(config.instance_id, {})
                    state = InstanceState(
                        instance_id=config.instance_id,
                        status=InstanceStatus(state_data.get("status", "stopped")),
                        container_id=state_data.get("container_id"),
                        created_at=datetime.fromisoformat(state_data.get("created_at", datetime.now().isoformat())),
                        started_at=datetime.fromisoformat(state_data["started_at"]) if state_data.get("started_at") else None,
                        last_used=datetime.fromisoformat(state_data.get("last_used", datetime.now().isoformat())),
                        stopped_at=datetime.fromisoformat(state_data["stopped_at"]) if state_data.get("stopped_at") else None,
                        cpu_usage=state_data.get("cpu_usage", 0.0),
                        memory_usage=state_data.get("memory_usage", 0.0),
                        network_usage=state_data.get("network_usage", 0.0),
                        error_count=state_data.get("error_count", 0),
                        last_error=state_data.get("last_error"),
                        health_check_url=state_data.get("health_check_url"),
                        health_status=state_data.get("health_status", "unknown"),
                        metadata=state_data.get("metadata", {})
                    )
                    self.instance_states[config.instance_id] = state
                
                print(f"✅ Loaded {len(self.instances)} instances")
                return True
            else:
                print("📝 No existing instances found, starting fresh")
                return True
                
        except Exception as e:
            print(f"❌ Error loading instances: {e}")
            return False
    
    def save_instances(self) -> bool:
        """Save instances to configuration file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "instances": [],
                "states": {}
            }
            
            # Save instance configurations
            for config in self.instances.values():
                data["instances"].append({
                    "instance_id": config.instance_id,
                    "instance_type": config.instance_type.value,
                    "account": config.account,
                    "provider": config.provider,
                    "port": config.port,
                    "image": config.image,
                    "environment": config.environment,
                    "volumes": config.volumes,
                    "networks": config.networks,
                    "auto_start": config.auto_start,
                    "auto_restart": config.auto_restart,
                    "max_uptime_hours": config.max_uptime_hours,
                    "metadata": config.metadata
                })
            
            # Save instance states
            for state in self.instance_states.values():
                data["states"][state.instance_id] = {
                    "status": state.status.value,
                    "container_id": state.container_id,
                    "created_at": state.created_at.isoformat(),
                    "started_at": state.started_at.isoformat() if state.started_at else None,
                    "last_used": state.last_used.isoformat(),
                    "stopped_at": state.stopped_at.isoformat() if state.stopped_at else None,
                    "cpu_usage": state.cpu_usage,
                    "memory_usage": state.memory_usage,
                    "network_usage": state.network_usage,
                    "error_count": state.error_count,
                    "last_error": state.last_error,
                    "health_check_url": state.health_check_url,
                    "health_status": state.health_status,
                    "metadata": state.metadata
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving instances: {e}")
            return False
    
    def create_instance(self, config: InstanceConfig) -> bool:
        """Create a new instance."""
        with self.lock:
            if config.instance_id in self.instances:
                print(f"⚠️  Instance {config.instance_id} already exists")
                return False
            
            # Allocate port if not specified
            if config.port == 0:
                config.port = self.port_allocator.allocate_port(config.instance_type)
            
            self.instances[config.instance_id] = config
            
            # Create initial state
            self.instance_states[config.instance_id] = InstanceState(
                instance_id=config.instance_id,
                status=InstanceStatus.CREATING,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            print(f"✅ Created instance: {config.instance_id}")
            return True
    
    def start_instance(self, instance_id: str) -> bool:
        """Start an instance."""
        if not self.docker_client:
            print("❌ Docker client not available")
            return False
        
        with self.lock:
            if instance_id not in self.instances:
                print(f"❌ Instance {instance_id} not found")
                return False
            
            config = self.instances[instance_id]
            state = self.instance_states[instance_id]
            
            if state.status == InstanceStatus.RUNNING:
                print(f"⚠️  Instance {instance_id} is already running")
                return True
            
            try:
                # Prepare container configuration
                container_config = {
                    "image": config.image,
                    "name": f"llx-{config.instance_type.value}-{instance_id}",
                    "detach": True,
                    "ports": {f"{config.port}/tcp": config.port},
                    "environment": config.environment,
                    "volumes": config.volumes,
                    "restart_policy": {"Name": "unless-stopped"} if config.auto_restart else {},
                    "labels": {
                        "llx.instance_id": instance_id,
                        "llx.instance_type": config.instance_type.value,
                        "llx.account": config.account,
                        "llx.provider": config.provider
                    }
                }
                
                # Create and start container
                container = self.docker_client.containers.run(**container_config)
                
                # Update state
                state.container_id = container.id
                state.status = InstanceStatus.RUNNING
                state.started_at = datetime.now()
                state.last_used = datetime.now()
                
                # Set health check URL for VS Code instances
                if config.instance_type == InstanceType.VSCODE:
                    state.health_check_url = f"http://localhost:{config.port}"
                
                print(f"✅ Started instance {instance_id} (port {config.port})")
                return True
                
            except Exception as e:
                state.status = InstanceStatus.ERROR
                state.last_error = str(e)
                state.error_count += 1
                print(f"❌ Failed to start instance {instance_id}: {e}")
                return False
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop an instance."""
        if not self.docker_client:
            print("❌ Docker client not available")
            return False
        
        with self.lock:
            if instance_id not in self.instances:
                print(f"❌ Instance {instance_id} not found")
                return False
            
            state = self.instance_states[instance_id]
            
            if state.status != InstanceStatus.RUNNING:
                print(f"⚠️  Instance {instance_id} is not running")
                return True
            
            try:
                if state.container_id:
                    container = self.docker_client.containers.get(state.container_id)
                    container.stop()
                
                state.status = InstanceStatus.STOPPED
                state.stopped_at = datetime.now()
                
                print(f"✅ Stopped instance {instance_id}")
                return True
                
            except Exception as e:
                state.status = InstanceStatus.ERROR
                state.last_error = str(e)
                state.error_count += 1
                print(f"❌ Failed to stop instance {instance_id}: {e}")
                return False
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance."""
        if not self.docker_client:
            print("❌ Docker client not available")
            return False
        
        with self.lock:
            if instance_id not in self.instances:
                print(f"❌ Instance {instance_id} not found")
                return False
            
            # Stop if running
            if self.instance_states[instance_id].status == InstanceStatus.RUNNING:
                self.stop_instance(instance_id)
            
            # Remove container
            state = self.instance_states[instance_id]
            if state.container_id:
                try:
                    container = self.docker_client.containers.get(state.container_id)
                    container.remove(force=True)
                except:
                    pass
            
            # Release port
            config = self.instances[instance_id]
            self.port_allocator.release_port(config.port)
            
            # Remove from memory
            del self.instances[instance_id]
            del self.instance_states[instance_id]
            
            print(f"✅ Removed instance {instance_id}")
            return True
    
    def get_available_instance(self, instance_type: InstanceType, account: str = None, provider: str = None) -> Optional[str]:
        """Get the best available instance for given criteria."""
        with self.lock:
            available_instances = []
            
            for instance_id, config in self.instances.items():
                if config.instance_type != instance_type:
                    continue
                
                if account and config.account != account:
                    continue
                
                if provider and config.provider != provider:
                    continue
                
                state = self.instance_states[instance_id]
                
                # Skip non-running instances
                if state.status != InstanceStatus.RUNNING:
                    continue
                
                # Skip instances with too many errors
                if state.error_count >= 3:
                    continue
                
                # Skip instances past max uptime
                if state.started_at:
                    uptime = datetime.now() - state.started_at
                    if uptime.total_seconds() > config.max_uptime_hours * 3600:
                        continue
                
                available_instances.append((instance_id, state.last_used))
            
            if not available_instances:
                return None
            
            # Sort by last used (least recently used first)
            available_instances.sort(key=lambda x: x[1])
            
            return available_instances[0][0]
    
    def use_instance(self, instance_id: str) -> bool:
        """Mark an instance as being used."""
        with self.lock:
            if instance_id not in self.instance_states:
                return False
            
            state = self.instance_states[instance_id]
            state.last_used = datetime.now()
            
            return True
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of an instance."""
        if instance_id not in self.instances:
            return None
        
        config = self.instances[instance_id]
        state = self.instance_states[instance_id]
        
        return {
            "instance_id": instance_id,
            "type": config.instance_type.value,
            "account": config.account,
            "provider": config.provider,
            "port": config.port,
            "image": config.image,
            "status": state.status.value,
            "container_id": state.container_id,
            "created_at": state.created_at.isoformat(),
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "last_used": state.last_used.isoformat(),
            "stopped_at": state.stopped_at.isoformat() if state.stopped_at else None,
            "cpu_usage": state.cpu_usage,
            "memory_usage": state.memory_usage,
            "network_usage": state.network_usage,
            "error_count": state.error_count,
            "last_error": state.last_error,
            "health_check_url": state.health_check_url,
            "health_status": state.health_status,
            "uptime_hours": self._get_uptime_hours(instance_id),
            "url": f"http://localhost:{config.port}" if config.instance_type == InstanceType.VSCODE else None
        }
    
    def list_instances(self, instance_type: InstanceType = None, status: InstanceStatus = None) -> List[Dict[str, Any]]:
        """List all instances with optional filtering."""
        instances = []
        
        for instance_id, config in self.instances.items():
            if instance_type and config.instance_type != instance_type:
                continue
            
            state = self.instance_states[instance_id]
            if status and state.status != status:
                continue
            
            instances.append(self.get_instance_status(instance_id))
        
        return instances
    
    def get_instance_metrics(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for an instance."""
        if not self.docker_client or instance_id not in self.instances:
            return None
        
        state = self.instance_states[instance_id]
        
        if not state.container_id:
            return None
        
        try:
            container = self.docker_client.containers.get(state.container_id)
            
            # Get container stats
            stats = container.stats(stream=False)
            
            # Calculate resource usage
            cpu_usage = 0.0
            memory_usage = 0.0
            
            if stats:
                # CPU usage calculation
                cpu_delta = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
                system_cpu_delta = stats.get("cpu_stats", {}).get("system_cpu_usage", 0)
                online_cpus = len(stats.get("cpu_stats", {}).get("online_cpus", [1]))
                
                if system_cpu_delta > 0:
                    cpu_usage = (cpu_delta / system_cpu_delta) * online_cpus * 100
                
                # Memory usage
                memory_usage = stats.get("memory_stats", {}).get("usage", 0)
                memory_limit = stats.get("memory_stats", {}).get("limit", 1)
                
                if memory_limit > 0:
                    memory_usage = (memory_usage / memory_limit) * 100
            
            # Update state
            state.cpu_usage = cpu_usage
            state.memory_usage = memory_usage
            
            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "container_id": state.container_id,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown"
            }
            
        except Exception as e:
            print(f"❌ Error getting metrics for {instance_id}: {e}")
            return None
    
    def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all running instances."""
        results = {
            "total_instances": len(self.instances),
            "running_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "instance_health": {}
        }
        
        for instance_id, state in self.instance_states.items():
            if state.status == InstanceStatus.RUNNING:
                results["running_instances"] += 1
                
                # Perform health check
                health_status = self._health_check_instance(instance_id)
                results["instance_health"][instance_id] = health_status
                
                if health_status["status"] == "healthy":
                    results["healthy_instances"] += 1
                else:
                    results["unhealthy_instances"] += 1
        
        return results
    
    def _health_check_instance(self, instance_id: str) -> Dict[str, Any]:
        """Perform health check on a specific instance."""
        state = self.instance_states[instance_id]
        config = self.instances[instance_id]
        
        health_result = {
            "instance_id": instance_id,
            "status": "unknown",
            "response_time": None,
            "error": None
        }
        
        if not state.health_check_url:
            health_result["status"] = "no_health_check"
            return health_result
        
        try:
            start_time = time.time()
            response = requests.get(state.health_check_url, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            health_result["response_time"] = response_time
            
            if response.status_code == 200:
                health_result["status"] = "healthy"
                state.health_status = "healthy"
            else:
                health_result["status"] = "unhealthy"
                health_result["error"] = f"HTTP {response.status_code}"
                state.health_status = "unhealthy"
                
        except requests.exceptions.Timeout:
            health_result["status"] = "timeout"
            health_result["error"] = "Request timeout"
            state.health_status = "timeout"
        except Exception as e:
            health_result["status"] = "error"
            health_result["error"] = str(e)
            state.health_status = "error"
        
        return health_result
    
    def _get_uptime_hours(self, instance_id: str) -> float:
        """Get instance uptime in hours."""
        state = self.instance_states[instance_id]
        
        if state.started_at:
            uptime = datetime.now() - state.started_at
            return uptime.total_seconds() / 3600
        
        return 0.0
    
    def _monitor_worker(self):
        """Background worker for monitoring instances."""
        while True:
            try:
                time.sleep(30)  # Run every 30 seconds
                
                # Update metrics for running instances
                for instance_id, state in self.instance_states.items():
                    if state.status == InstanceStatus.RUNNING:
                        self.get_instance_metrics(instance_id)
                
                # Health check
                self.health_check_all()
                
                # Check for instances that need restart
                self._check_auto_restart()
                
                # Save state periodically
                if time.time() % 300 < 30:  # Every 5 minutes
                    self.save_instances()
                
            except Exception as e:
                print(f"❌ Monitor worker error: {e}")
    
    def _check_auto_restart(self):
        """Check if any instances need auto-restart."""
        with self.lock:
            for instance_id, config in self.instances.items():
                if not config.auto_restart:
                    continue
                
                state = self.instance_states[instance_id]
                
                # Check if instance is stopped and should be restarted
                if state.status == InstanceStatus.STOPPED:
                    if state.error_count < 3:  # Only restart if not too many errors
                        print(f"🔄 Auto-restarting instance {instance_id}")
                        self.start_instance(instance_id)
                    else:
                        print(f"⚠️  Instance {instance_id} has too many errors, skipping auto-restart")
                
                # Check if instance is unhealthy
                elif state.status == InstanceStatus.RUNNING and state.health_status in ["error", "timeout"]:
                    if state.error_count < 2:
                        print(f"🔄 Restarting unhealthy instance {instance_id}")
                        self.stop_instance(instance_id)
                        time.sleep(5)
                        self.start_instance(instance_id)
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🏗️  Instance Manager Status")
        print("==========================")
        
        # Overall stats
        total_instances = len(self.instances)
        status_counts = {}
        type_counts = {}
        
        for state in self.instance_states.values():
            status_counts[state.status.value] = status_counts.get(state.status.value, 0) + 1
        
        for config in self.instances.values():
            type_counts[config.instance_type.value] = type_counts.get(config.instance_type.value, 0) + 1
        
        print(f"📊 Total Instances: {total_instances}")
        print(f"📈 By Status: {dict(status_counts)}")
        print(f"🏷️  By Type: {dict(type_counts)}")
        
        # Health check results
        health_results = self.health_check_all()
        print(f"\n🏥 Health Status:")
        print(f"  Running: {health_results['running_instances']}")
        print(f"  Healthy: {health_results['healthy_instances']}")
        print(f"  Unhealthy: {health_results['unhealthy_instances']}")
        
        # Port allocation
        port_status = self.port_allocator.get_status()
        print(f"\n🔌 Port Allocation:")
        print(f"  Used: {port_status['used_ports']}")
        print(f"  Available: {port_status['available_ports']}")
        print(f"  Range: {port_status['port_range']}")
        
        print()


class PortAllocator:
    """Manages port allocation for instances."""
    
    def __init__(self):
        self.port_ranges = {
            InstanceType.VSCODE: (8080, 8999),
            InstanceType.AI_TOOLS: (9000, 9999),
            InstanceType.LLM_PROXY: (4000, 4099)
        }
        self.allocated_ports = set()
        self.lock = threading.Lock()
    
    def allocate_port(self, instance_type: InstanceType) -> int:
        """Allocate a port for an instance type."""
        with self.lock:
            start_port, end_port = self.port_ranges[instance_type]
            
            for port in range(start_port, end_port + 1):
                if port not in self.allocated_ports and self._is_port_available(port):
                    self.allocated_ports.add(port)
                    return port
            
            raise Exception(f"No available ports for {instance_type} in range {start_port}-{end_port}")
    
    def release_port(self, port: int) -> bool:
        """Release a port."""
        with self.lock:
            if port in self.allocated_ports:
                self.allocated_ports.remove(port)
                return True
            return False
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get port allocation status."""
        total_ports = sum(end - start + 1 for start, end in self.port_ranges.values())
        
        return {
            "used_ports": len(self.allocated_ports),
            "available_ports": total_ports - len(self.allocated_ports),
            "port_range": f"{min(start for start, _ in self.port_ranges.values())}-{max(end for _, end in self.port_ranges.values())}",
            "allocated_ports": sorted(list(self.allocated_ports))
        }


# CLI interface
def main():
    """CLI interface for instance manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx Instance Manager")
    parser.add_argument("command", choices=[
        "create", "start", "stop", "remove", "list", "status", "metrics", "health", "cleanup"
    ])
    parser.add_argument("--instance-id", help="Instance ID")
    parser.add_argument("--type", choices=["vscode", "ai_tools", "llm_proxy"], help="Instance type")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--port", type=int, help="Port number")
    parser.add_argument("--image", help="Docker image")
    parser.add_argument("--auto-start", action="store_true", help="Auto start instance")
    parser.add_argument("--auto-restart", action="store_true", help="Auto restart instance")
    
    args = parser.parse_args()
    
    manager = InstanceManager()
    
    if args.command == "create":
        if not args.instance_id or not args.type:
            print("❌ --instance-id and --type required for create")
            sys.exit(1)
        
        config = InstanceConfig(
            instance_id=args.instance_id,
            instance_type=InstanceType(args.type),
            account=args.account or "default",
            provider=args.provider or "default",
            port=args.port or 0,
            image=args.image or "default",
            auto_start=args.auto_start,
            auto_restart=args.auto_restart
        )
        
        success = manager.create_instance(config)
        if success and config.auto_start:
            manager.start_instance(config.instance_id)
        
        if success:
            manager.save_instances()
    
    elif args.command == "start":
        if not args.instance_id:
            print("❌ --instance-id required for start")
            sys.exit(1)
        
        success = manager.start_instance(args.instance_id)
        if success:
            manager.save_instances()
    
    elif args.command == "stop":
        if not args.instance_id:
            print("❌ --instance-id required for stop")
            sys.exit(1)
        
        success = manager.stop_instance(args.instance_id)
        if success:
            manager.save_instances()
    
    elif args.command == "remove":
        if not args.instance_id:
            print("❌ --instance-id required for remove")
            sys.exit(1)
        
        success = manager.remove_instance(args.instance_id)
        if success:
            manager.save_instances()
    
    elif args.command == "list":
        instance_type = InstanceType(args.type) if args.type else None
        instances = manager.list_instances(instance_type)
        
        print(f"📋 Instances ({len(instances)}):")
        for instance in instances:
            print(f"  • {instance['instance_id']}: {instance['status']} ({instance['type']}, port {instance['port']})")
    
    elif args.command == "status":
        if args.instance_id:
            status = manager.get_instance_status(args.instance_id)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print(f"❌ Instance {args.instance_id} not found")
                sys.exit(1)
        else:
            manager.print_status_summary()
    
    elif args.command == "metrics":
        if not args.instance_id:
            print("❌ --instance-id required for metrics")
            sys.exit(1)
        
        metrics = manager.get_instance_metrics(args.instance_id)
        if metrics:
            print(json.dumps(metrics, indent=2))
        else:
            print(f"❌ Could not get metrics for {args.instance_id}")
            sys.exit(1)
    
    elif args.command == "health":
        results = manager.health_check_all()
        print(json.dumps(results, indent=2))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
