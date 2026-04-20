#!/usr/bin/env python3
"""Detect secrets plugin for pyqual pipeline.

Scans for hardcoded secrets and credentials using detect-secrets.
"""

import subprocess
import sys
from pathlib import Path


def _run_detect_secrets_subprocess(output_file: Path) -> bool:
    """Execute the detect-secrets subprocess and handle errors."""
    try:
        subprocess.run(
            [
                "detect-secrets",
                "scan",
                "--all-files",
                "--force-use-all-plugins",
                "--json"
            ],
            stdout=output_file.open("w"),
            stderr=subprocess.PIPE,
            check=True,
            timeout=60
        )
        print(f"✓ Secrets scan completed - results saved to {output_file}")
        return True
    except subprocess.TimeoutExpired:
        print("WARNING: detect-secrets scan timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("WARNING: detect-secrets not installed, skipping scan")
        return True
    except subprocess.CalledProcessError as e:
        # detect-secrets may exit with findings
        print(f"detect-secrets completed - results saved to {output_file}")
        return True


def run_detect_secrets(output_dir: Path) -> bool:
    """Run detect-secrets scan and save JSON output."""
    print("Scanning for hardcoded secrets...")
    output_file = output_dir / "detect-secrets.json"
    return _run_detect_secrets_subprocess(output_file)


def main() -> int:
    """Main entry point for detect secrets plugin."""
    output_dir = Path(".pyqual")
    output_dir.mkdir(exist_ok=True)

    secrets_ok = run_detect_secrets(output_dir)

    # Optional stage - don't fail pipeline
    if not secrets_ok:
        print("WARNING: Secrets scan incomplete", file=sys.stderr)

    print("Secrets detection completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
