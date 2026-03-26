"""
Shared Docker subprocess helpers for tools sub-package.
Eliminates repeated docker ps/exec/cp boilerplate across managers.
"""

import subprocess
from typing import Optional


def is_container_running(container_name: str) -> bool:
    """Check if a Docker container is running by name."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10,
        )
        return container_name in result.stdout
    except Exception:
        return False


def docker_exec(
    container: str,
    cmd: list[str],
    timeout: int = 30,
    interactive: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command inside a Docker container.

    Parameters
    ----------
    container : container name
    cmd : command and arguments to run
    interactive : if True, run with -it (no capture)
    timeout : seconds before TimeoutExpired
    """
    base = ["docker", "exec"]
    if interactive:
        base.append("-it")
    base.append(container)
    base.extend(cmd)

    if interactive:
        return subprocess.run(base)
    return subprocess.run(base, capture_output=True, text=True, timeout=timeout)


def docker_cp(src: str, dest: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Copy files between host and container via ``docker cp``."""
    return subprocess.run(
        ["docker", "cp", src, dest],
        capture_output=True, text=True, timeout=timeout,
    )
