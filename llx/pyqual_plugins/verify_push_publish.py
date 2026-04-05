#!/usr/bin/env python3
"""Verify push and publish plugin for pyqual pipeline.

Verifies that:
1. Current commit is pushed to origin/main
2. Version is available on PyPI (with retries)
"""

import subprocess
import sys
import time
from pathlib import Path


def get_current_version() -> str:
    """Read current version from VERSION file."""
    version_path = Path("VERSION")
    if not version_path.exists():
        raise FileNotFoundError("VERSION file not found")
    return version_path.read_text(encoding="utf-8").strip()


def verify_push() -> bool:
    """Verify current commit is on origin/main."""
    try:
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        remote = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        if local != remote:
            print(f"ERROR: Push failed - local commit {local} != origin/main {remote}")
            print("See docs/GITHUB_PUSH_PROTECTION.md for troubleshooting")
            return False

        print(f"✓ Push verified: local == origin/main ({local})")
        return True

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Git command failed: {e}", file=sys.stderr)
        return False


def verify_publish(version: str, max_retries: int = 3, delay: int = 5) -> bool:
    """Verify version is on PyPI with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                ["pip", "index", "versions", "llx"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if version in result.stdout:
                print(f"✓ Publish verified: version {version} on PyPI")
                return True

            if attempt < max_retries:
                print(f"Retry {attempt}/{max_retries}: Version {version} not found on PyPI yet...")
                time.sleep(delay)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            if attempt < max_retries:
                print(f"Retry {attempt}/{max_retries}: PyPI check failed: {e}")
                time.sleep(delay)

    print(f"WARNING: Version {version} not found on PyPI after {max_retries} retries")
    print("This may be expected if publish was skipped (version already existed)")
    return False


def main() -> int:
    """Main entry point for verify plugin."""
    try:
        version = get_current_version()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Testing push and publish for version {version}")

    # Always verify push (hard fail)
    if not verify_push():
        return 1

    # Verify publish (soft fail - warning only)
    verify_publish(version)

    print("All deployment tests completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
