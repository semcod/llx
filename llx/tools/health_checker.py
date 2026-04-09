"""
Health Checker for llx
Comprehensive health monitoring for llx ecosystem.
"""

import os
import subprocess
import json
import time
from typing import Dict, List, Any
from pathlib import Path
import requests
from .docker_manager import DockerManager
from .model_manager import ModelManager
from ._utils import cli_main
from .vscode_manager import VSCodeManager
from .ai_tools_manager import AIToolsManager
from .health_runner import HealthCheckRunner


class HealthChecker:
    """Comprehensive health monitoring for llx ecosystem."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        # Initialize managers
        self.docker_manager = DockerManager(project_root)
        self.model_manager = ModelManager(project_root)
        self.vscode_manager = VSCodeManager(project_root)
        self.ai_tools_manager = AIToolsManager(project_root)
        
        # Health check endpoints
        self.endpoints = {
            "llx_api": {
                "url": "http://localhost:4000",
                "health": "/health",
                "models": "/v1/models",
                "timeout": 5
            },
            "ollama": {
                "url": "http://localhost:11434",
                "health": "/api/tags",
                "models": "/api/tags",
                "timeout": 5
            },
            "redis": {
                "url": "redis://localhost:6379",
                "timeout": 3
            },
            "vscode": {
                "url": "http://localhost:8080",
                "timeout": 5
            }
        }
        
        # Expected services
        self.expected_services = {
            "llx-api": {"required": True, "container": "llx-api-dev"},
            "redis": {"required": False, "container": "llx-redis-dev"},
            "vscode": {"required": False, "container": "llx-vscode-dev"},
            "ai-tools": {"required": False, "container": "llx-ai-tools-dev"}
        }
    
    def _build_service_result(self, service_name: str) -> Dict[str, Any]:
        return {
            "service": service_name,
            "status": "unhealthy",
            "response_time": None,
            "error": None,
            "details": {}
        }

    def _check_redis_health(self, endpoint: Dict[str, Any], result: Dict[str, Any], start_time: float) -> None:
        try:
            subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=endpoint["timeout"]
            )
            result["status"] = "healthy"
            result["response_time"] = (time.time() - start_time) * 1000
        except subprocess.TimeoutExpired:
            result["error"] = "Timeout"
        except FileNotFoundError:
            result["error"] = "Redis CLI not available"
        except Exception as e:
            result["error"] = str(e)

    def _populate_service_details(self, service_name: str, endpoint: Dict[str, Any], result: Dict[str, Any]) -> None:
        if "models" not in endpoint:
            return

        models_url = f"{endpoint['url']}{endpoint['models']}"
        try:
            models_response = requests.get(models_url, timeout=endpoint["timeout"])
            if models_response.status_code != 200:
                return

            data = models_response.json()
            if service_name == "ollama":
                result["details"]["models"] = len(data.get("models", []))
                result["details"]["total_size"] = sum(
                    model.get("size", 0) for model in data.get("models", [])
                )
            elif service_name == "llx_api":
                result["details"]["models"] = len(data.get("data", []))
        except:
            pass

    def _check_http_health(self, service_name: str, endpoint: Dict[str, Any], result: Dict[str, Any], start_time: float) -> None:
        health_url = f"{endpoint['url']}{endpoint.get('health', '/')}"
        response = requests.get(health_url, timeout=endpoint["timeout"])

        result["response_time"] = (time.time() - start_time) * 1000

        if response.status_code == 200:
            result["status"] = "healthy"
            self._populate_service_details(service_name, endpoint, result)
        else:
            result["error"] = f"HTTP {response.status_code}"

    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        if service_name not in self.endpoints:
            return {"status": "unknown", "error": f"Unknown service: {service_name}"}
        
        endpoint = self.endpoints[service_name]
        result = self._build_service_result(service_name)
        
        try:
            start_time = time.time()
            
            if service_name == "redis":
                self._check_redis_health(endpoint, result, start_time)
            
            else:
                self._check_http_health(service_name, endpoint, result, start_time)
        
        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection refused"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def check_container_health(self, container_name: str) -> Dict[str, Any]:
        """Check health of a Docker container."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "container": container_name,
                    "status": "not_found",
                    "error": "Container not found"
                }
            
            data = json.loads(result.stdout)
            if not data:
                return {
                    "container": container_name,
                    "status": "error",
                    "error": "Invalid inspect result"
                }
            
            container_info = data[0]
            state = container_info.get("State", {})
            
            return {
                "container": container_name,
                "status": state.get("Status", "unknown").lower(),
                "health": state.get("Health", {}).get("Status", "unknown"),
                "running": state.get("Running", False),
                "started_at": state.get("StartedAt"),
                "exit_code": state.get("ExitCode"),
                "error": state.get("Error")
            }
            
        except subprocess.TimeoutExpired:
            return {
                "container": container_name,
                "status": "timeout",
                "error": "Docker inspect timeout"
            }
        except Exception as e:
            return {
                "container": container_name,
                "status": "error",
                "error": str(e)
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        resources = {
            "cpu": {"usage": 0, "cores": 0},
            "memory": {"total": 0, "available": 0, "usage": 0},
            "disk": {"total": 0, "available": 0, "usage": 0},
            "load_average": []
        }
        
        try:
            # CPU info
            resources["cpu"]["cores"] = os.cpu_count()
            
            # Memory info
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        resources["memory"]["total"] = int(line.split()[1]) // 1024  # MB
                    elif line.startswith('MemAvailable:'):
                        resources["memory"]["available"] = int(line.split()[1]) // 1024  # MB
            
            if resources["memory"]["total"] > 0:
                resources["memory"]["usage"] = (
                    (resources["memory"]["total"] - resources["memory"]["available"]) /
                    resources["memory"]["total"] * 100
                )
            
            # Disk space
            stat = os.statvfs(self.project_root)
            total_space = stat.f_blocks * stat.f_frsize // (1024**3)  # GB
            available_space = stat.f_bavail * stat.f_frsize // (1024**3)  # GB
            
            resources["disk"]["total"] = total_space
            resources["disk"]["available"] = available_space
            resources["disk"]["usage"] = ((total_space - available_space) / total_space * 100) if total_space > 0 else 0
            
            # Load average
            try:
                with open('/proc/loadavg', 'r') as f:
                    resources["load_average"] = f.read().strip().split()[:3]
            except:
                pass
            
        except Exception as e:
            resources["error"] = str(e)
        
        return resources
    
    def check_filesystem_health(self) -> Dict[str, Any]:
        """Check filesystem health and permissions."""
        health = {
            "project_accessible": True,
            "permissions": {},
            "disk_space": {},
            "important_files": {},
            "issues": []
        }
        
        try:
            # Check project directory access
            if not os.access(self.project_root, os.R_OK | os.W_OK | os.X_OK):
                health["project_accessible"] = False
                health["issues"].append("Project directory not accessible")
            
            # Check important files
            important_files = [
                "pyproject.toml",
                ".env",
                "docker-compose-dev.yml",
                "docker-compose-prod.yml",
                "docker-compose.yml",
                "litellm-config.yaml"
            ]
            
            for filename in important_files:
                file_path = self.project_root / filename
                file_info = {
                    "exists": file_path.exists(),
                    "readable": False,
                    "writable": False,
                    "size": 0
                }
                
                if file_path.exists():
                    file_info["readable"] = os.access(file_path, os.R_OK)
                    file_info["writable"] = os.access(file_path, os.W_OK)
                    file_info["size"] = file_path.stat().st_size
                else:
                    health["issues"].append(f"Missing important file: {filename}")
                
                health["important_files"][filename] = file_info
            
            # Check directory permissions
            directories = [".", "logs", "cache", "backups"]
            
            for dirname in directories:
                dir_path = self.project_root / dirname
                perm_info = {
                    "exists": dir_path.exists(),
                    "readable": False,
                    "writable": False
                }
                
                if dir_path.exists():
                    perm_info["readable"] = os.access(dir_path, os.R_OK | os.X_OK)
                    perm_info["writable"] = os.access(dir_path, os.W_OK | os.X_OK)
                    
                    if not perm_info["readable"]:
                        health["issues"].append(f"Directory not readable: {dirname}")
                    if not perm_info["writable"]:
                        health["issues"].append(f"Directory not writable: {dirname}")
                
                health["permissions"][dirname] = perm_info
            
        except Exception as e:
            health["error"] = str(e)
            health["issues"].append(f"Filesystem check error: {e}")
        
        return health
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity and DNS resolution."""
        connectivity = {
            "localhost": True,
            "internet": False,
            "dns": True,
            "ports": {},
            "issues": []
        }
        
        try:
            # Check localhost connectivity
            try:
                requests.get("http://localhost", timeout=2)
            except:
                connectivity["localhost"] = False
                connectivity["issues"].append("localhost not reachable")
            
            # Check internet connectivity
            try:
                requests.get("https://httpbin.org/ip", timeout=5)
                connectivity["internet"] = True
            except:
                connectivity["issues"].append("No internet connection")
            
            # Check DNS resolution
            try:
                import socket
                socket.gethostbyname("google.com")
            except:
                connectivity["dns"] = False
                connectivity["issues"].append("DNS resolution failed")
            
            # Check critical ports
            critical_ports = {
                4000: "llx API",
                11434: "Ollama",
                6379: "Redis",
                8080: "VS Code"
            }
            
            for port, service in critical_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(("localhost", port))
                    sock.close()
                    
                    connectivity["ports"][port] = {
                        "service": service,
                        "open": result == 0,
                        "status": "open" if result == 0 else "closed"
                    }
                    
                    if result != 0 and service in ["llx API", "Ollama"]:
                        connectivity["issues"].append(f"Critical port closed: {port} ({service})")
                
                except Exception as e:
                    connectivity["ports"][port] = {
                        "service": service,
                        "open": False,
                        "error": str(e)
                    }
        
        except Exception as e:
            connectivity["error"] = str(e)
            connectivity["issues"].append(f"Network check error: {e}")
        
        return connectivity
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check of entire llx ecosystem."""
        runner = HealthCheckRunner(self)
        return runner.run_comprehensive()
    
    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations (delegated to runner)."""
        runner = HealthCheckRunner(self)
        return runner._generate_recommendations(health_report)
    
    def _print_health_summary(self, health_report: Dict[str, Any]):
        """Print health check summary (delegated to runner)."""
        runner = HealthCheckRunner(self)
        runner._print_health_summary(health_report)
    
    def run_quick_health_check(self) -> bool:
        """Run quick health check for critical services only."""
        critical_services = ["llx_api", "ollama"]
        all_healthy = True
        
        print("🏥 Quick Health Check")
        print("====================")
        
        for service in critical_services:
            health = self.check_service_health(service)
            status_icon = "✅" if health["status"] == "healthy" else "❌"
            print(f"{status_icon} {service}: {health['status']}")
            
            if health["status"] != "healthy":
                all_healthy = False
        
        if all_healthy:
            print("\n✅ All critical services are healthy!")
        else:
            print("\n❌ Some services are unhealthy. Run full check for details.")
        
        return all_healthy
    
    def monitor_services(self, interval: int = 30, duration: int = 300) -> Dict[str, Any]:
        """Monitor services over time."""
        print(f"🔍 Monitoring services for {duration} seconds (interval: {interval}s)")
        print("="*60)
        
        monitoring_data = {
            "start_time": time.time(),
            "end_time": time.time() + duration,
            "interval": interval,
            "data_points": []
        }
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            timestamp = time.time()
            data_point = {
                "timestamp": timestamp,
                "services": {}
            }
            
            for service_name in self.endpoints.keys():
                health = self.check_service_health(service_name)
                data_point["services"][service_name] = {
                    "status": health["status"],
                    "response_time": health.get("response_time"),
                    "error": health.get("error")
                }
            
            monitoring_data["data_points"].append(data_point)
            
            # Print current status
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            status_line = f"{time_str} | "
            
            for service_name, service_data in data_point["services"].items():
                status_icon = "✅" if service_data["status"] == "healthy" else "❌"
                response_time = f" ({service_data.get('response_time', 0):.0f}ms)" if service_data.get("response_time") else ""
                status_line += f"{status_icon} {service_name}{response_time} | "
            
            print(f"\r{status_line}", end="", flush=True)
            
            time.sleep(interval)
        
        print()  # New line after monitoring
        
        # Analyze monitoring data
        analysis = HealthCheckRunner(self).analyze_monitoring_data(monitoring_data)
        monitoring_data["analysis"] = analysis
        
        print(f"\n📊 Monitoring Analysis:")
        print(f"  Duration: {duration} seconds")
        print(f"  Data points: {len(monitoring_data['data_points'])}")
        print(f"  Uptime: {analysis.get('uptime_percentage', 0):.1f}%")
        print(f"  Avg response time: {analysis.get('avg_response_time', 0):.1f}ms")
        
        return monitoring_data
    

def _build_parser() -> "argparse.ArgumentParser":
    import argparse
    parser = argparse.ArgumentParser(description="llx Health Checker")
    parser.add_argument("command", choices=[
        "check", "quick", "monitor", "service", "container", "system",
        "filesystem", "network"
    ])
    parser.add_argument("--service", help="Specific service to check")
    parser.add_argument("--container", help="Specific container to check")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval (seconds)")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration (seconds)")
    parser.add_argument("--output", help="Output file for results")
    return parser


def _write_json_output(output_path: str, data: Dict[str, Any]) -> None:
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


def _handle_check_command(args, checker: "HealthChecker") -> bool:
    results = checker.run_comprehensive_health_check()
    if args.output:
        _write_json_output(args.output, results)
    return results["overall_status"] == "healthy"


def _handle_quick_command(args, checker: "HealthChecker") -> bool:
    return checker.run_quick_health_check()


def _handle_monitor_command(args, checker: "HealthChecker") -> bool:
    results = checker.monitor_services(args.interval, args.duration)
    if args.output:
        _write_json_output(args.output, results)
    return True


def _handle_service_command(args, checker: "HealthChecker") -> bool:
    if not args.service:
        print("❌ --service required for service check")
        return False

    results = checker.check_service_health(args.service)
    print(json.dumps(results, indent=2))
    return results["status"] == "healthy"


def _handle_container_command(args, checker: "HealthChecker") -> bool:
    if not args.container:
        print("❌ --container required for container check")
        return False

    results = checker.check_container_health(args.container)
    print(json.dumps(results, indent=2))
    return results["status"] == "running"


def _handle_system_command(args, checker: "HealthChecker") -> bool:
    results = checker.check_system_resources()
    print(json.dumps(results, indent=2))
    return True


def _handle_filesystem_command(args, checker: "HealthChecker") -> bool:
    results = checker.check_filesystem_health()
    print(json.dumps(results, indent=2))
    return len(results.get("issues", [])) == 0


def _handle_network_command(args, checker: "HealthChecker") -> bool:
    results = checker.check_network_connectivity()
    print(json.dumps(results, indent=2))
    return len(results.get("issues", [])) == 0


def _dispatch(args, checker: "HealthChecker") -> bool:
    handlers = {
        "check": _handle_check_command,
        "quick": _handle_quick_command,
        "monitor": _handle_monitor_command,
        "service": _handle_service_command,
        "container": _handle_container_command,
        "system": _handle_system_command,
        "filesystem": _handle_filesystem_command,
        "network": _handle_network_command,
    }

    handler = handlers.get(args.command)
    if not handler:
        return False

    return handler(args, checker)


def main():
    """CLI entry point for health checker."""
    cli_main(_build_parser, _dispatch, HealthChecker)


if __name__ == "__main__":
    main()
