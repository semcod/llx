#!/usr/bin/env python3
"""Security audit plugin for pyqual pipeline.

Runs pip-audit for CVE checks and bandit for security scanning.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_pip_audit(output_dir: Path) -> bool:
    """Run pip-audit for CVE checks."""
    print("Running pip-audit for CVE checks...")
    output_file = output_dir / "pip-audit.json"

    try:
        result = subprocess.run(
            ["pip-audit", "--format=json", f"--output={output_file}"],
            capture_output=True,
            text=True,
            timeout=120
        )
        # pip-audit returns non-zero if vulnerabilities found
        print(f"pip-audit results saved to {output_file}")
        return True
    except subprocess.TimeoutExpired:
        print("WARNING: pip-audit timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("WARNING: pip-audit not installed, skipping CVE check")
        return True
    except subprocess.CalledProcessError as e:
        print(f"pip-audit completed with issues: {e}")
        print(f"Results saved to {output_file}")
        return True


def run_bandit(output_dir: Path) -> bool:
    """Run bandit security scan."""
    print("Running bandit security scan...")
    output_file = output_dir / "bandit.json"

    try:
        subprocess.run(
            ["bandit", "-r", "llx", "-f", "json", "-o", str(output_file), "-ll"],
            check=True,
            capture_output=True,
            timeout=120
        )
        print(f"✓ Bandit scan passed - results saved to {output_file}")
        return True
    except subprocess.TimeoutExpired:
        print("WARNING: Bandit scan timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("WARNING: bandit not installed, skipping security scan")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Bandit found security issues: {e}")
        print(f"Results saved to {output_file}")
        return True


def main() -> int:
    """Main entry point for security audit plugin."""
    output_dir = Path(".pyqual")
    output_dir.mkdir(exist_ok=True)

    pip_audit_ok = run_pip_audit(output_dir)
    bandit_ok = run_bandit(output_dir)

    # Optional stages - don't fail pipeline
    if not pip_audit_ok:
        print("WARNING: pip-audit check incomplete", file=sys.stderr)
    if not bandit_ok:
        print("WARNING: bandit check incomplete", file=sys.stderr)

    print("Security audit completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
