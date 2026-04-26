"""Patch application helpers for `llx.commands.fix`."""

from __future__ import annotations

from pathlib import Path


def _extract_json_from_content(content: str) -> str | None:
    """Extract a JSON array from content, handling 