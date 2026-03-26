"""Health Check Runner - Extracted comprehensive health check logic from HealthChecker.

This module contains the high-CC (16) execution logic that was split from
health_checker.py to reduce complexity per the evolution.toon.yaml backlog.
"""

import time
from typing import Dict, Any, List


class HealthCheckRunner:
    """Runs comprehensive health checks and generates reports."""
    
    def __init__(self, checker):
        self.checker = checker
    
    def run_comprehensive(self) -> Dict[str, Any]:
        """Run comprehensive health check of entire llx ecosystem."""
        print("🏥 Running Comprehensive Health Check")
        print("=====================================")
        
        health_report = {
            "timestamp": time.time(),
            "overall_status": "healthy",
            "services": {},
            "containers": {},
            "system": {},
            "filesystem": {},
            "network": {},
            "issues": [],
            "recommendations": []
        }
        
        # Check services
        print("🔍 Checking services...")
        for service_name in self.checker.endpoints.keys():
            service_health = self.checker.check_service_health(service_name)
            health_report["services"][service_name] = service_health
            
            status_icon = "✅" if service_health["status"] == "healthy" else "❌"
            response_time = f" ({service_health.get('response_time', 0):.0f}ms)" if service_health.get("response_time") else ""
            print(f"  {status_icon} {service_name}: {service_health['status']}{response_time}")
            
            if service_health["status"] != "healthy":
                health_report["issues"].append(
                    f"Service {service_name} unhealthy: {service_health.get('error', 'Unknown')}"
                )
        
        # Check containers
        print("\n🐳 Checking containers...")
        container_status = self.checker.docker_manager.get_service_status("dev")
        
        for service_name, config in self.checker.expected_services.items():
            container_name = config["container"]
            container_health = self.checker.check_container_health(container_name)
            health_report["containers"][service_name] = container_health
            
            status_icon = "✅" if container_health["status"] == "running" else "❌"
            print(f"  {status_icon} {container_name}: {container_health['status']}")
            
            if container_health["status"] != "running":
                health_report["issues"].append(f"Container {container_name} not running")
        
        # Check system resources
        print("\n💻 Checking system resources...")
        system_resources = self.checker.check_system_resources()
        health_report["system"] = system_resources
        
        print(f"  🧠 CPU: {system_resources['cpu']['cores']} cores")
        print(f"  🧠 Memory: {system_resources['memory']['available'] // 1024}GB available / {system_resources['memory']['total'] // 1024}GB total")
        print(f"  💾 Disk: {system_resources['disk']['available']}GB available / {system_resources['disk']['total']}GB total")
        
        if system_resources["memory"]["usage"] > 90:
            health_report["issues"].append("High memory usage (>90%)")
            health_report["recommendations"].append("Consider closing unused applications")
        
        if system_resources["disk"]["usage"] > 90:
            health_report["issues"].append("Low disk space (<10%)")
            health_report["recommendations"].append("Clean up unused files and containers")
        
        # Check filesystem
        print("\n📁 Checking filesystem...")
        filesystem_health = self.checker.check_filesystem_health()
        health_report["filesystem"] = filesystem_health
        
        if not filesystem_health["project_accessible"]:
            health_report["issues"].append("Project directory not accessible")
        
        for issue in filesystem_health.get("issues", []):
            health_report["issues"].append(f"Filesystem: {issue}")
        
        # Check network
        print("\n🌐 Checking network connectivity...")
        network_health = self.checker.check_network_connectivity()
        health_report["network"] = network_health
        
        internet_icon = "✅" if network_health["internet"] else "❌"
        print(f"  {internet_icon} Internet: {'Connected' if network_health['internet'] else 'Disconnected'}")
        
        for issue in network_health.get("issues", []):
            health_report["issues"].append(f"Network: {issue}")
        
        # Overall status
        if health_report["issues"]:
            health_report["overall_status"] = "unhealthy"
        
        # Generate recommendations
        health_report["recommendations"].extend(self._generate_recommendations(health_report))
        
        # Print summary
        self._print_health_summary(health_report)
        
        return health_report
    
    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []
        
        # Service recommendations
        services = health_report["services"]
        
        if services.get("ollama", {}).get("status") != "healthy":
            recommendations.append("Start Ollama: `ollama serve`")
        
        if services.get("llx_api", {}).get("status") != "healthy":
            recommendations.append("Start llx API: `python -m llx proxy start`")
        
        if services.get("redis", {}).get("status") != "healthy":
            recommendations.append("Start Redis: `docker-compose -f docker-compose-dev.yml up -d redis`")
        
        # Container recommendations
        containers = health_report["containers"]
        
        stopped_containers = [
            name for name, health in containers.items()
            if health.get("status") != "running"
        ]
        
        if stopped_containers:
            recommendations.append(f"Start containers: `./docker-manage.sh dev`")
        
        # System recommendations
        system = health_report.get("system", {})
        
        if system.get("memory", {}).get("usage", 0) > 80:
            recommendations.append("Free up memory: close unused applications")
        
        if system.get("disk", {}).get("usage", 0) > 80:
            recommendations.append("Free up disk space: `docker system prune`")
        
        # Network recommendations
        network = health_report.get("network", {})
        
        if not network.get("internet"):
            recommendations.append("Check internet connection for external API access")
        
        return recommendations
    
    def _print_health_summary(self, health_report: Dict[str, Any]):
        """Print health check summary."""
        print("\n" + "="*50)
        print("🏥 HEALTH CHECK SUMMARY")
        print("="*50)
        
        # Overall status
        status_icon = "✅" if health_report["overall_status"] == "healthy" else "❌"
        status_text = "HEALTHY" if health_report["overall_status"] == "healthy" else "UNHEALTHY"
        print(f"{status_icon} Overall Status: {status_text}")
        
        # Issues count
        issues_count = len(health_report["issues"])
        if issues_count > 0:
            print(f"❌ Issues Found: {issues_count}")
            print("\n🚨 Issues:")
            for i, issue in enumerate(health_report["issues"][:10], 1):
                print(f"  {i}. {issue}")
            
            if issues_count > 10:
                print(f"  ... and {issues_count - 10} more issues")
        else:
            print("✅ No issues found!")
        
        # Recommendations
        recommendations = health_report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Quick fix commands
        print("\n🔧 Quick Fix Commands:")
        print("  ./docker-manage.sh dev          # Start all services")
        print("  ./docker-manage.sh status       # Check status")
        print("  ./docker-manage.sh logs dev     # View logs")
        print("  ollama serve                    # Start Ollama")
        print("  python -m llx proxy start      # Start llx API")
        
        print()
    
    def analyze_monitoring_data(self, monitoring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monitoring data and generate statistics."""
        data_points = monitoring_data["data_points"]
        
        if not data_points:
            return {}
        
        analysis = {
            "uptime_percentage": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float('inf'),
            "service_uptime": {},
            "service_response_times": {}
        }
        
        total_points = len(data_points)
        healthy_points = 0
        all_response_times = []
        
        for service_name in self.checker.endpoints.keys():
            service_healthy = 0
            service_response_times = []
            
            for data_point in data_points:
                service_data = data_point["services"].get(service_name, {})
                
                if service_data["status"] == "healthy":
                    service_healthy += 1
                    healthy_points += 1
                
                if service_data.get("response_time"):
                    service_response_times.append(service_data["response_time"])
                    all_response_times.append(service_data["response_time"])
            
            # Service-specific stats
            if service_response_times:
                analysis["service_response_times"][service_name] = {
                    "avg": sum(service_response_times) / len(service_response_times),
                    "max": max(service_response_times),
                    "min": min(service_response_times)
                }
            
            analysis["service_uptime"][service_name] = (
                (service_healthy / total_points * 100) if total_points > 0 else 0
            )
        
        # Overall stats
        if all_response_times:
            analysis["avg_response_time"] = sum(all_response_times) / len(all_response_times)
            analysis["max_response_time"] = max(all_response_times)
            analysis["min_response_time"] = min(all_response_times)
        
        analysis["uptime_percentage"] = (
            (healthy_points / (total_points * len(self.checker.endpoints)) * 100)
            if total_points > 0 else 0
        )
        
        return analysis
