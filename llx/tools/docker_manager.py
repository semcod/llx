"""
Docker Manager for llx
Comprehensive Docker container management for llx services.
"""

import os
import subprocess
import json
import time
from typing import Dict, List
from pathlib import Path
import requests

from ._utils import cli_main


class DockerManager:
    """Manages Docker containers for llx ecosystem."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.compose_files = {
            "dev": "docker-compose-dev.yml",
            "prod": "docker-compose-prod.yml", 
            "full": "docker-compose.yml"
        }
        self.services = {
            "llx-api": {"port": 4000, "health": "/health"},
            "redis": {"port": 6379, "health": None},
            "vscode": {"port": 8080, "health": None},
            "ai-tools": {"port": None, "health": None}
        }
    
    def get_compose_cmd(self) -> str:
        """Get appropriate docker-compose command."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "docker compose"
        except:
            pass
        
        try:
            result = subprocess.run(
                ["docker-compose", "--version"], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "docker-compose"
        except:
            pass
        
        raise RuntimeError("Neither docker-compose nor docker compose is available")
    
    def run_compose_cmd(self, env: str, cmd: str, *args, **kwargs) -> subprocess.CompletedProcess:
        """Run docker-compose command."""
        compose_file = self.compose_files.get(env, "docker-compose.yml")
        compose_cmd = self.get_compose_cmd()
        
        command = [compose_cmd, "-f", compose_file, "-p", f"llx-{env}"]
        if cmd:
            command.append(cmd)
        command.extend(args)
        
        env_vars = os.environ.copy()
        if kwargs.get("capture_output"):
            return subprocess.run(command, capture_output=True, text=True, env=env_vars)
        else:
            return subprocess.run(command, env=env_vars)
    
    def start_environment(self, env: str = "dev", services: List[str] = None) -> bool:
        """Start Docker environment."""
        try:
            print(f"🚀 Starting {env} environment...")
            
            cmd_args = []
            if services:
                cmd_args.extend(services)
            
            result = self.run_compose_cmd(env, "up", "-d", *cmd_args)
            
            if result.returncode == 0:
                print(f"✅ {env} environment started successfully!")
                return True
            else:
                print(f"❌ Failed to start {env} environment")
                return False
                
        except Exception as e:
            print(f"❌ Error starting environment: {e}")
            return False
    
    def stop_environment(self, env: str = "dev", services: List[str] = None) -> bool:
        """Stop Docker environment."""
        try:
            print(f"🛑 Stopping {env} environment...")
            
            cmd_args = []
            if services:
                cmd_args.extend(services)
            
            result = self.run_compose_cmd(env, "stop", *cmd_args)
            
            if result.returncode == 0:
                print(f"✅ {env} environment stopped successfully!")
                return True
            else:
                print(f"❌ Failed to stop {env} environment")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping environment: {e}")
            return False
    
    def restart_service(self, env: str = "dev", service: str = None) -> bool:
        """Restart specific service."""
        try:
            print(f"🔄 Restarting {service} in {env} environment...")
            
            cmd_args = [service] if service else []
            result = self.run_compose_cmd(env, "restart", *cmd_args)
            
            if result.returncode == 0:
                print(f"✅ {service or 'all services'} restarted successfully!")
                return True
            else:
                print(f"❌ Failed to restart {service or 'services'}")
                return False
                
        except Exception as e:
            print(f"❌ Error restarting service: {e}")
            return False
    
    def get_service_status(self, env: str = "dev") -> Dict[str, Dict]:
        """Get status of all services."""
        try:
            result = self.run_compose_cmd(env, "ps", "--format", "json", capture_output=True)
            
            if result.returncode != 0:
                return {}
            
            services = json.loads(result.stdout)
            status_info = {}
            
            for service in services:
                service_name = service.get("Name", "").replace(f"llx-{env}_", "")
                status_info[service_name] = {
                    "state": service.get("State", "unknown"),
                    "status": service.get("Status", ""),
                    "ports": service.get("Publishers", []),
                    "health": service.get("Health", "")
                }
            
            return status_info
            
        except Exception as e:
            print(f"❌ Error getting service status: {e}")
            return {}
    
    def get_service_logs(self, env: str = "dev", service: str = None, tail: int = 50) -> str:
        """Get service logs."""
        try:
            cmd_args = ["--tail", str(tail)]
            if service:
                cmd_args.append(service)
            
            result = self.run_compose_cmd(env, "logs", *cmd_args, capture_output=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error getting logs: {result.stderr}"
                
        except Exception as e:
            return f"Error getting logs: {e}"
    
    def check_service_health(self, service_name: str, env: str = "dev") -> bool:
        """Check if service is healthy."""
        try:
            if service_name not in self.services:
                return False
            
            service_config = self.services[service_name]
            port = service_config.get("port")
            health_endpoint = service_config.get("health")
            
            if port:
                # Try to connect to the port
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(("localhost", port))
                sock.close()
                
                if result != 0:
                    return False
                
                # If health endpoint specified, check it too
                if health_endpoint:
                    try:
                        response = requests.get(f"http://localhost:{port}{health_endpoint}", timeout=5)
                        return response.status_code == 200
                    except:
                        return False
                
                return True
            
            # For services without ports, check container status
            status = self.get_service_status(env)
            service_status = status.get(f"{service_name}-{env}", {})
            return service_status.get("state") == "running"
            
        except Exception as e:
            print(f"❌ Error checking service health: {e}")
            return False
    
    def wait_for_service(self, service_name: str, env: str = "dev", timeout: int = 60) -> bool:
        """Wait for service to be ready."""
        print(f"⏳ Waiting for {service_name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service_health(service_name, env):
                print(f"✅ {service_name} is ready!")
                return True
            
            time.sleep(2)
        
        print(f"❌ Timeout waiting for {service_name}")
        return False
    
    def cleanup_environment(self, env: str = "dev", remove_volumes: bool = False) -> bool:
        """Clean up Docker environment."""
        try:
            print(f"🧹 Cleaning up {env} environment...")
            
            cmd_args = ["-v"] if remove_volumes else []
            result = self.run_compose_cmd(env, "down", *cmd_args)
            
            if result.returncode == 0:
                print(f"✅ {env} environment cleaned up successfully!")
                return True
            else:
                print(f"❌ Failed to clean up {env} environment")
                return False
                
        except Exception as e:
            print(f"❌ Error cleaning up environment: {e}")
            return False
    
    def build_images(self, env: str = "dev", service: str = None) -> bool:
        """Build Docker images."""
        try:
            print(f"🔨 Building images for {env} environment...")
            
            cmd_args = []
            if service:
                cmd_args.append(service)
            
            result = self.run_compose_cmd(env, "build", *cmd_args)
            
            if result.returncode == 0:
                print(f"✅ Images built successfully!")
                return True
            else:
                print(f"❌ Failed to build images")
                return False
                
        except Exception as e:
            print(f"❌ Error building images: {e}")
            return False
    
    def pull_images(self, env: str = "dev", service: str = None) -> bool:
        """Pull Docker images."""
        try:
            print(f"📦 Pulling images for {env} environment...")
            
            cmd_args = []
            if service:
                cmd_args.append(service)
            
            result = self.run_compose_cmd(env, "pull", *cmd_args)
            
            if result.returncode == 0:
                print(f"✅ Images pulled successfully!")
                return True
            else:
                print(f"❌ Failed to pull images")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling images: {e}")
            return False
    
    def get_resource_usage(self, env: str = "dev") -> Dict[str, Dict]:
        """Get resource usage for services."""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return {}
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {}
            
            # Skip header line
            usage_info = {}
            for line in lines[1:]:
                parts = line.split('\t')
                if len(parts) >= 3:
                    container = parts[0]
                    cpu_percent = parts[1]
                    memory_usage = parts[2]
                    
                    # Extract service name from container name
                    service_name = container.replace(f"llx-{env}_", "")
                    usage_info[service_name] = {
                        "cpu": cpu_percent,
                        "memory": memory_usage
                    }
            
            return usage_info
            
        except Exception as e:
            print(f"❌ Error getting resource usage: {e}")
            return {}
    
    def backup_volumes(self, env: str = "dev", backup_dir: str = None) -> bool:
        """Backup Docker volumes."""
        try:
            if not backup_dir:
                backup_dir = self.project_root / "backups" / f"docker-{env}-{int(time.time())}"
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            print(f"💾 Backing up volumes to {backup_path}...")
            
            # Get volumes for environment
            result = self.run_compose_cmd(env, "config", "--volumes", capture_output=True)
            if result.returncode != 0:
                return False
            
            volumes = result.stdout.strip().split('\n')
            
            for volume in volumes:
                if volume.strip():
                    volume_name = f"llx-{env}_{volume.strip()}"
                    backup_file = backup_path / f"{volume.strip()}.tar"
                    
                    # Create backup
                    subprocess.run([
                        "docker", "run", "--rm",
                        "-v", f"{volume_name}:/data",
                        "-v", f"{backup_path}:/backup",
                        "alpine", "tar", "czf", f"/backup/{volume.strip()}.tar", "-C", "/data", "."
                    ])
                    
                    print(f"  ✅ Backed up {volume.strip()}")
            
            print(f"✅ Backup completed: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error backing up volumes: {e}")
            return False
    
    def restore_volumes(self, backup_dir: str, env: str = "dev") -> bool:
        """Restore Docker volumes from backup."""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                print(f"❌ Backup directory not found: {backup_path}")
                return False
            
            print(f"📦 Restoring volumes from {backup_path}...")
            
            # Stop services first
            self.stop_environment(env)
            
            # Restore each volume
            for backup_file in backup_path.glob("*.tar"):
                volume_name = backup_file.stem
                full_volume_name = f"llx-{env}_{volume_name}"
                
                # Create volume if it doesn't exist
                subprocess.run(["docker", "volume", "create", full_volume_name])
                
                # Restore data
                subprocess.run([
                    "docker", "run", "--rm",
                    "-v", f"{full_volume_name}:/data",
                    "-v", f"{backup_path}:/backup",
                    "alpine", "tar", "xzf", f"/backup/{backup_file.name}", "-C", "/data"
                ])
                
                print(f"  ✅ Restored {volume_name}")
            
            print(f"✅ Restore completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error restoring volumes: {e}")
            return False
    
    def get_network_info(self, env: str = "dev") -> Dict[str, str]:
        """Get network information."""
        try:
            network_name = f"llx-{env}_llx-network"
            
            result = subprocess.run(
                ["docker", "network", "inspect", network_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return {}
            
            network_data = json.loads(result.stdout)
            if not network_data:
                return {}
            
            network = network_data[0]
            return {
                "name": network.get("Name"),
                "driver": network.get("Driver"),
                "subnet": network.get("IPAM", {}).get("Config", [{}])[0].get("Subnet", ""),
                "gateway": network.get("IPAM", {}).get("Config", [{}])[0].get("Gateway", "")
            }
            
        except Exception as e:
            print(f"❌ Error getting network info: {e}")
            return {}
    
    def print_status_summary(self, env: str = "dev"):
        """Print comprehensive status summary."""
        print(f"📊 {env.upper()} Environment Status")
        print("=" * 50)
        
        # Service status
        status = self.get_service_status(env)
        print("🔍 Services:")
        for service, info in status.items():
            status_icon = "✅" if info.get("state") == "running" else "❌"
            print(f"  {status_icon} {service}: {info.get('status', 'Unknown')}")
        
        # Health checks
        print("\n🏥 Health Checks:")
        for service_name in self.services.keys():
            health_icon = "✅" if self.check_service_health(service_name, env) else "❌"
            print(f"  {health_icon} {service_name}")
        
        # Resource usage
        usage = self.get_resource_usage(env)
        if usage:
            print("\n💾 Resource Usage:")
            for service, info in usage.items():
                print(f"  📊 {service}: CPU {info.get('cpu', 'N/A')}, Memory {info.get('memory', 'N/A')}")
        
        # Network info
        network = self.get_network_info(env)
        if network:
            print(f"\n🌐 Network: {network.get('name', 'Unknown')}")
            if network.get("subnet"):
                print(f"  📡 Subnet: {network['subnet']}")
            if network.get("gateway"):
                print(f"  🚪 Gateway: {network['gateway']}")
        
        print()


# CLI interface

def _build_parser() -> "argparse.ArgumentParser":
    import argparse
    parser = argparse.ArgumentParser(description="llx Docker Manager")
    parser.add_argument("command", choices=[
        "start", "stop", "restart", "status", "logs", "build", "pull",
        "cleanup", "backup", "restore", "health", "wait"
    ])
    parser.add_argument("--env", default="dev", choices=["dev", "prod", "full"])
    parser.add_argument("--service", help="Specific service")
    parser.add_argument("--tail", type=int, default=50, help="Log tail lines")
    parser.add_argument("--timeout", type=int, default=60, help="Wait timeout")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument("--remove-volumes", action="store_true", help="Remove volumes on cleanup")
    return parser


def _dispatch(args, manager: DockerManager) -> bool:
    """Dispatch command to appropriate handler."""
    handlers = {
        "start": lambda a, m: m.start_environment(a.env, [a.service] if a.service else None),
        "stop": lambda a, m: m.stop_environment(a.env, [a.service] if a.service else None),
        "restart": lambda a, m: m.restart_service(a.env, a.service),
        "status": lambda a, m: (m.print_status_summary(a.env), True)[1],
        "logs": lambda a, m: (print(m.get_service_logs(a.env, a.service, a.tail)), True)[1],
        "build": lambda a, m: m.build_images(a.env, a.service),
        "pull": lambda a, m: m.pull_images(a.env, a.service),
        "cleanup": lambda a, m: m.cleanup_environment(a.env, a.remove_volumes),
        "backup": lambda a, m: m.backup_volumes(a.env, a.backup_dir),
        "restore": _handle_restore,
        "health": _handle_health,
        "wait": _handle_wait,
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args, manager)
    return False


def _handle_restore(args, manager: DockerManager) -> bool:
    """Handle restore command with validation."""
    if not args.backup_dir:
        print("❌ --backup-dir required for restore")
        return False
    return manager.restore_volumes(args.backup_dir, args.env)


def _handle_health(args, manager: DockerManager) -> bool:
    """Handle health command."""
    if args.service:
        ok = manager.check_service_health(args.service, args.env)
        print(f"🏥 {args.service}: {'✅ Healthy' if ok else '❌ Unhealthy'}")
        return ok
    manager.print_status_summary(args.env)
    return True


def _handle_wait(args, manager: DockerManager) -> bool:
    """Handle wait command with validation."""
    if not args.service:
        print("❌ --service required for wait")
        return False
    return manager.wait_for_service(args.service, args.env, args.timeout)


def main():
    """CLI entry point for Docker manager."""
    cli_main(_build_parser, _dispatch, DockerManager)


if __name__ == "__main__":
    main()
