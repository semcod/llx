#!/usr/bin/env python3
"""Idempotent PyPI publish plugin for pyqual pipeline.

Skips upload if version already exists on PyPI.
"""

import subprocess
import sys
from pathlib import Path


def get_current_version() -> str:
    """Read current version from VERSION file."""
    version_path = Path("VERSION")
    if not version_path.exists():
        raise FileNotFoundError("VERSION file not found")
    return version_path.read_text(encoding="utf-8").strip()


def check_version_on_pypi(version: str) -> bool:
    """Check if version already exists on PyPI."""
    try:
        result = subprocess.run(
            ["pip", "index", "versions", "llx"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return version in result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        # If check fails, assume not exists to attempt publish
        return False


def upload_to_pypi() -> int:
    """Upload distribution to PyPI using twine."""
    try:
        result = subprocess.run(
            ["python", "-m", "twine", "upload", "dist/*"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for publish plugin."""
    try:
        version = get_current_version()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Checking PyPI for version {version}...")

    # Check if already published
    if check_version_on_pypi(version):
        print(f"Version {version} already on PyPI, skipping upload")
        return 0

    print(f"Publishing version {version} to PyPI...")

    # Perform upload
    return upload_to_pypi()


if __name__ == "__main__":
    sys.exit(main())
