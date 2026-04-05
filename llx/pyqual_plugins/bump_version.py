#!/usr/bin/env python3
"""Version bump plugin for pyqual pipeline.

Automatically bumps patch version if current version already exists on PyPI.
"""

import re
import subprocess
import sys
from pathlib import Path


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
        return False


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse version string into components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_patch_version(version: str) -> str:
    """Bump patch component of version."""
    major, minor, patch = parse_version(version)
    return f"{major}.{minor}.{patch + 1}"


def update_version_file(version_path: Path, new_version: str) -> None:
    """Update VERSION file."""
    version_path.write_text(new_version + "\n", encoding="utf-8")
    print(f"Updated {version_path} to {new_version}")


def update_pyproject_toml(toml_path: Path, old_version: str, new_version: str) -> None:
    """Update version in pyproject.toml."""
    content = toml_path.read_text(encoding="utf-8")
    # Replace version line
    new_content = re.sub(
        rf'^version = "{re.escape(old_version)}"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    toml_path.write_text(new_content, encoding="utf-8")
    print(f"Updated {toml_path} to {new_version}")


def git_commit_version_bump(old_version: str, new_version: str) -> None:
    """Commit version bump changes."""
    try:
        subprocess.run(
            ["git", "add", "VERSION", "pyproject.toml"],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"chore: auto-bump version {old_version} -> {new_version} [pyqual]"],
            check=True,
            capture_output=True
        )
        print(f"Committed version bump: {old_version} -> {new_version}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git commit failed: {e}", file=sys.stderr)


def main() -> int:
    """Main entry point for version bump plugin."""
    repo_root = Path.cwd()
    version_path = repo_root / "VERSION"
    toml_path = repo_root / "pyproject.toml"

    if not version_path.exists():
        print(f"Error: VERSION file not found at {version_path}", file=sys.stderr)
        return 1

    if not toml_path.exists():
        print(f"Error: pyproject.toml not found at {toml_path}", file=sys.stderr)
        return 1

    # Read current version
    current_version = version_path.read_text(encoding="utf-8").strip()
    print(f"Current version: {current_version}")

    # Check if already on PyPI
    if not check_version_on_pypi(current_version):
        print(f"Version {current_version} not on PyPI, no bump needed")
        return 0

    print(f"Version {current_version} already on PyPI, bumping patch...")

    # Bump version
    try:
        new_version = bump_patch_version(current_version)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Bumping: {current_version} -> {new_version}")

    # Update files
    update_version_file(version_path, new_version)
    update_pyproject_toml(toml_path, current_version, new_version)

    # Git commit
    git_commit_version_bump(current_version, new_version)

    print(f"✓ Version bumped to {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
