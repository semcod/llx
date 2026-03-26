"""Port allocation for VS Code instances."""

import socket
import threading


class VSCodePortAllocator:
    """Manages port allocation for VS Code instances."""

    def __init__(self):
        self.port_range = (8080, 8999)
        self.allocated_ports: set = set()
        self.lock = threading.Lock()

    def allocate_port(self, instance_id: str) -> int:
        """Allocate a port for a VS Code instance."""
        with self.lock:
            for port in range(self.port_range[0], self.port_range[1] + 1):
                if port not in self.allocated_ports and self._is_port_available(port):
                    self.allocated_ports.add(port)
                    return port
            raise Exception(
                f"No available ports in range {self.port_range[0]}-{self.port_range[1]}"
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
