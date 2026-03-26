"""Port allocation for Docker instances."""

import socket
import threading
from typing import Dict, Any

from .models import InstanceType


class PortAllocator:
    """Manages port allocation for instances."""

    def __init__(self):
        self.port_ranges = {
            InstanceType.VSCODE: (8080, 8999),
            InstanceType.AI_TOOLS: (9000, 9999),
            InstanceType.LLM_PROXY: (4000, 4099),
        }
        self.allocated_ports: set = set()
        self.lock = threading.Lock()

    def allocate_port(self, instance_type: InstanceType) -> int:
        """Allocate a port for an instance type."""
        with self.lock:
            start_port, end_port = self.port_ranges[instance_type]
            for port in range(start_port, end_port + 1):
                if port not in self.allocated_ports and self._is_port_available(port):
                    self.allocated_ports.add(port)
                    return port
            raise Exception(
                f"No available ports for {instance_type} in range {start_port}-{end_port}"
            )

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
            result = sock.connect_ex(("localhost", port))
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
            "port_range": (
                f"{min(s for s, _ in self.port_ranges.values())}"
                f"-{max(e for _, e in self.port_ranges.values())}"
            ),
            "allocated_ports": sorted(list(self.allocated_ports)),
        }
