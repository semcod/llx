"""
Shared utilities for orchestration sub-packages.
Eliminates repeated JSON I/O and CLI boilerplate.
"""

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional


# ── JSON config I/O ─────────────────────────────────────

def load_json(path: Path, label: str = "config") -> Optional[Dict[str, Any]]:
    """Load JSON from *path*, returning None on missing file or error."""
    try:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ Error loading {label}: {e}")
        return None


def save_json(path: Path, data: Dict[str, Any], label: str = "config") -> bool:
    """Save *data* as JSON to *path*, creating parent dirs as needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving {label}: {e}")
        return False


# ── CLI boilerplate ──────────────────────────────────────

from ..utils.cli_main import cli_main
