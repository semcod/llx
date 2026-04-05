#!/usr/bin/env python3
"""Lint plugin for pyqual pipeline.

Runs ruff linter and format check, outputs JSON for analysis.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_ruff_lint(output_dir: Path) -> bool:
    """Run ruff linter and save JSON output."""
    print("Running ruff linter...")
    output_file = output_dir / "ruff.json"

    try:
        result = subprocess.run(
            ["ruff", "check", "llx", "tests", "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        # Write output even if ruff finds issues
        output_file.write_text(result.stdout or "[]", encoding="utf-8")

        if result.returncode == 0:
            print(f"✓ Ruff lint passed - results saved to {output_file}")
        else:
            print(f"Ruff found {len(json.loads(result.stdout or '[]'))} issues")
            print(f"Results saved to {output_file}")
        return True
    except subprocess.TimeoutExpired:
        print("WARNING: Ruff lint timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("WARNING: ruff not installed, skipping lint")
        return True


def run_ruff_format_check() -> bool:
    """Run ruff format check."""
    print("Running ruff format check...")

    try:
        result = subprocess.run(
            ["ruff", "format", "--check", "llx", "tests"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✓ Ruff format check passed")
        else:
            print("Ruff format issues found (non-blocking)")
        return True
    except subprocess.TimeoutExpired:
        print("WARNING: Ruff format check timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("WARNING: ruff not installed, skipping format check")
        return True


def main() -> int:
    """Main entry point for lint plugin."""
    output_dir = Path(".pyqual")
    output_dir.mkdir(exist_ok=True)

    lint_ok = run_ruff_lint(output_dir)
    format_ok = run_ruff_format_check()

    # Optional stages - don't fail pipeline
    if not lint_ok:
        print("WARNING: Lint check incomplete", file=sys.stderr)
    if not format_ok:
        print("WARNING: Format check incomplete", file=sys.stderr)

    print("Lint completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
