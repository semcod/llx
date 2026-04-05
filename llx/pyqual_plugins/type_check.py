#!/usr/bin/env python3
"""Type check plugin for pyqual pipeline.

Runs mypy static type analysis with JSON output.
"""

import subprocess
import sys
from pathlib import Path


def run_mypy(output_dir: Path) -> bool:
    """Run mypy type checker and save JSON output."""
    print("Running mypy type checker...")
    output_file = output_dir / "mypy.json"

    try:
        result = subprocess.run(
            [
                "mypy",
                "llx",
                "--ignore-missing-imports",
                "--show-error-codes",
                "--json"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Write JSON output
        output_file.write_text(result.stdout or "[]", encoding="utf-8")

        if result.returncode == 0:
            print(f"✓ Mypy type check passed - results saved to {output_file}")
        else:
            # Count errors from JSON output
            import json
            try:
                errors = json.loads(result.stdout or "[]")
                print(f"Mypy found {len(errors)} type issues")
            except json.JSONDecodeError:
                print("Mypy found type issues")
            print(f"Results saved to {output_file}")
        return True

    except subprocess.TimeoutExpired:
        print("WARNING: Mypy type check timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("WARNING: mypy not installed, skipping type check")
        return True


def main() -> int:
    """Main entry point for type check plugin."""
    output_dir = Path(".pyqual")
    output_dir.mkdir(exist_ok=True)

    type_check_ok = run_mypy(output_dir)

    # Optional stage - don't fail pipeline
    if not type_check_ok:
        print("WARNING: Type check incomplete", file=sys.stderr)

    print("Type check completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
