"""Version checking utilities for llx CLI."""

import subprocess
import sys
from typing import Optional, Tuple
from pathlib import Path


def get_current_version() -> str:
    """Get current llx version."""
    try:
        from llx import __version__
        return __version__
    except Exception:
        return "unknown"


def get_pypi_version(package_name: str = "llx") -> Optional[str]:
    """Get latest version from PyPI."""
    try:
        result = subprocess.run(
            ["pip", "index", "versions", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Parse output: "llx (0.1.62, 0.1.61, ...)"
            output = result.stdout.strip()
            if package_name in output:
                # Extract versions list
                versions_part = output.split("(")[1].split(")")[0]
                latest_version = versions_part.split(",")[0].strip()
                return latest_version
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        pass
    return None


def compare_versions(current: str, latest: str) -> Tuple[int, str, str]:
    """Compare two version strings.
    
    Returns:
        (comparison, current, latest) where comparison is:
        -1 if current < latest (outdated)
        0 if current == latest (up to date)
        1 if current > latest (dev version)
    """
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        
        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        for c, l in zip(current_parts, latest_parts):
            if c < l:
                return -1, current, latest
            elif c > l:
                return 1, current, latest
        return 0, current, latest
    except (ValueError, AttributeError):
        # If parsing fails, assume up to date
        return 0, current, latest


def check_version() -> Optional[Tuple[str, str]]:
    """Check if llx is up to date.
    
    Returns:
        (current_version, latest_version) if outdated, None otherwise
    """
    current = get_current_version()
    if current == "unknown":
        return None
    
    latest = get_pypi_version()
    if not latest:
        return None
    
    comparison, _, _ = compare_versions(current, latest)
    if comparison < 0:
        return current, latest
    
    return None


def get_update_command() -> str:
    """Get the appropriate pip update command based on environment."""
    if sys.executable:
        return f"{sys.executable} -m pip install -U llx"
    return "pip install -U llx"
