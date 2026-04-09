"""
Instance Manager — Docker instance lifecycle and monitoring.
Extracted from the monolithic instance_manager.py.
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import docker
import requests

from .models import InstanceType, InstanceStatus, InstanceConfig, InstanceState
from .ports import PortAllocator
from .._utils import save_json


class InstanceManager:
    """Manages multiple Docker instances with intelligent allocation and monitoring."""

    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "instances.json"
        self.instances: Dict[str, InstanceConfig] = {}
        self.instance_states: Dict[str, InstanceState] = {}
        self.port_allocator = PortAllocator()
        self.lock = threading.RLock()

        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"❌ Docker client initialization failed: {e}")
            self.docker_client = None

        self.load_instances()

        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()

    # ── Config persistence ──────────────────────────────────

    def load_instances(self) -> bool:
        """Load instances from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    data = json.load(f)

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
                        metadata=instance_data.get("metadata", {}),
                    )
                    self.instances[config.instance_id] = config

                    state_data = data.get("states", {}).get(config.instance_id, {})
                    state = InstanceState(
                        instance_id=config.instance_id,
                        status=InstanceStatus(state_data.get("status", "stopped")),
                        container_id=state_data.get("container_id"),
                        created_at=datetime.fromisoformat(
                            state_data.get("created_at", datetime.now().isoformat())
                        ),
                        started_at=(
                            datetime.fromisoformat(state_data["started_at"])
                            if state_data.get("started_at")
                            else None
                        ),
                        last_used=datetime.fromisoformat(
                            state_data.get("last_used", datetime.now().isoformat())
                        ),
                        stopped_at=(
                            datetime.fromisoformat(state_data["stopped_at"])
                            if state_data.get("stopped_at")
                            else None
                        ),
                        cpu_usage=state_data.get("cpu_usage", 0.0),
                        memory_usage=state_data.get("memory_usage", 0.0),
                        network_usage=state_data.get("network_usage", 0.0),
                        error_count=state_data.get("error_count", 0),
                        last_error=state_data.get("last_error"),
                        health_check_url=state_data.get("health_check_url"),
                        health_status=state_data.get("health_status", "unknown"),
                        metadata=state_data.get("metadata", {}),
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
            data: Dict[str, Any] = {"instances": [], "states": {}}

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
                    "metadata": config.metadata,
                })

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
                    "metadata": state.metadata,
                }

            return save_json(self.config_file, data, "instances")

        except Exception as e:
            print(f"❌ Error saving instances: {e}")
            return False

    # ── Instance CRUD ───────────────────────────────────────

    def create_instance(self, config: InstanceConfig) -> bool:
        """Create a new instance."""
        with self.lock:
            if config.instance_id in self.instances:
                print(f"⚠️  Instance {config.instance_id} already exists")
                return False
            if config.port == 0:
                config.port = self.port_allocator.allocate_port(config.instance_type)

            self.instances[config.instance_id] = config
            self.instance_states[config.instance_id] = InstanceState(
                instance_id=config.instance_id,
                status=InstanceStatus.CREATING,
                created_at=datetime.now(),
                last_used=datetime.now(),
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
                        "llx.provider": config.provider,
                    },
                }
                container = self.docker_client.containers.run(**container_config)

                state.container_id = container.id
                state.status = InstanceStatus.RUNNING
                state.started_at = datetime.now()
                state.last_used = datetime.now()

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

            if self.instance_states[instance_id].status == InstanceStatus.RUNNING:
                self.stop_instance(instance_id)

            state = self.instance_states[instance_id]
            if state.container_id:
                try:
                    container = self.docker_client.containers.get(state.container_id)
                    container.remove(force=True)
                except:
                    pass

            config = self.instances[instance_id]
            self.port_allocator.release_port(config.port)

            del self.instances[instance_id]
            del self.instance_states[instance_id]

            print(f"✅ Removed instance {instance_id}")
            return True

    # ── Query methods ───────────────────────────────────────

    def get_available_instance(
        self, instance_type: InstanceType, account: str = None, provider: str = None
    ) -> Optional[str]:
        """Get the best available instance for given criteria."""
        with self.lock:
            available = []
            for instance_id, config in self.instances.items():
                if config.instance_type != instance_type:
                    continue
                if account and config.account != account:
                    continue
                if provider and config.provider != provider:
                    continue

                state = self.instance_states[instance_id]
                if state.status != InstanceStatus.RUNNING:
                    continue
                if state.error_count >= 3:
                    continue
                if state.started_at:
                    uptime = datetime.now() - state.started_at
                    if uptime.total_seconds() > config.max_uptime_hours * 3600:
                        continue
                available.append((instance_id, state.last_used))

            if not available:
                return None
            available.sort(key=lambda x: x[1])
            return available[0][0]

    def use_instance(self, instance_id: str) -> bool:
        """Mark an instance as being used."""
        with self.lock:
            if instance_id not in self.instance_states:
                return False
            self.instance_states[instance_id].last_used = datetime.now()
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
            "url": (
                f"http://localhost:{config.port}"
                if config.instance_type == InstanceType.VSCODE
                else None
            ),
        }

    def list_instances(
        self, instance_type: InstanceType = None, status: InstanceStatus = None
    ) -> List[Dict[str, Any]]:
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
            stats = container.stats(stream=False)

            cpu_usage = 0.0
            memory_usage = 0.0
            if stats:
                cpu_delta = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
                system_cpu_delta = stats.get("cpu_stats", {}).get("system_cpu_usage", 0)
                online_cpus = len(stats.get("cpu_stats", {}).get("online_cpus", [1]))
                if system_cpu_delta > 0:
                    cpu_usage = (cpu_delta / system_cpu_delta) * online_cpus * 100
                mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                mem_limit = stats.get("memory_stats", {}).get("limit", 1)
                if mem_limit > 0:
                    memory_usage = (mem_usage / mem_limit) * 100

            state.cpu_usage = cpu_usage
            state.memory_usage = memory_usage

            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "container_id": state.container_id,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
            }
        except Exception as e:
            print(f"❌ Error getting metrics for {instance_id}: {e}")
            return None

    # ── Health checks ───────────────────────────────────────

    def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all running instances."""
        results: Dict[str, Any] = {
            "total_instances": len(self.instances),
            "running_instances": 0,
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "instance_health": {},
        }
        for instance_id, state in self.instance_states.items():
            if state.status == InstanceStatus.RUNNING:
                results["running_instances"] += 1
                health = self._health_check_instance(instance_id)
                results["instance_health"][instance_id] = health
                if health["status"] == "healthy":
                    results["healthy_instances"] += 1
                else:
                    results["unhealthy_instances"] += 1
        return results

    def _health_check_instance(self, instance_id: str) -> Dict[str, Any]:
        """Perform health check on a specific instance."""
        state = self.instance_states[instance_id]
        result: Dict[str, Any] = {
            "instance_id": instance_id,
            "status": "unknown",
            "response_time": None,
            "error": None,
        }
        if not state.health_check_url:
            result["status"] = "no_health_check"
            return result
        try:
            start = time.time()
            response = requests.get(state.health_check_url, timeout=5)
            result["response_time"] = (time.time() - start) * 1000
            if response.status_code == 200:
                result["status"] = "healthy"
                state.health_status = "healthy"
            else:
                result["status"] = "unhealthy"
                result["error"] = f"HTTP {response.status_code}"
                state.health_status = "unhealthy"
        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["error"] = "Request timeout"
            state.health_status = "timeout"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            state.health_status = "error"
        return result

    # ── Internal helpers ────────────────────────────────────

    def _get_uptime_hours(self, instance_id: str) -> float:
        state = self.instance_states[instance_id]
        if state.started_at:
            return (datetime.now() - state.started_at).total_seconds() / 3600
        return 0.0

    # ── Background tasks ────────────────────────────────────

    def _monitor_worker(self):
        """Background worker for monitoring instances."""
        while True:
            try:
                time.sleep(30)
                for instance_id, state in self.instance_states.items():
                    if state.status == InstanceStatus.RUNNING:
                        self.get_instance_metrics(instance_id)
                self.health_check_all()
                self._check_auto_restart()
                if time.time() % 300 < 30:
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
                if state.status == InstanceStatus.STOPPED:
                    if state.error_count < 3:
                        print(f"🔄 Auto-restarting instance {instance_id}")
                        self.start_instance(instance_id)
                    else:
                        print(f"⚠️  Instance {instance_id} has too many errors, skipping auto-restart")
                elif (
                    state.status == InstanceStatus.RUNNING
                    and state.health_status in ("error", "timeout")
                ):
                    if state.error_count < 2:
                        print(f"🔄 Restarting unhealthy instance {instance_id}")
                        self.stop_instance(instance_id)
                        time.sleep(5)
                        self.start_instance(instance_id)

    # ── Print summary ───────────────────────────────────────

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🏗️  Instance Manager Status")
        print("==========================")

        total = len(self.instances)
        status_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}

        for state in self.instance_states.values():
            status_counts[state.status.value] = status_counts.get(state.status.value, 0) + 1
        for config in self.instances.values():
            type_counts[config.instance_type.value] = type_counts.get(config.instance_type.value, 0) + 1

        print(f"📊 Total Instances: {total}")
        print(f"📈 By Status: {dict(status_counts)}")
        print(f"🏷️  By Type: {dict(type_counts)}")

        health_results = self.health_check_all()
        print(f"\n🏥 Health Status:")
        print(f"  Running: {health_results['running_instances']}")
        print(f"  Healthy: {health_results['healthy_instances']}")
        print(f"  Unhealthy: {health_results['unhealthy_instances']}")

        port_status = self.port_allocator.get_status()
        print(f"\n🔌 Port Allocation:")
        print(f"  Used: {port_status['used_ports']}")
        print(f"  Available: {port_status['available_ports']}")
        print(f"  Range: {port_status['port_range']}")

        print()
