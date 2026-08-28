"""Shared safety helpers for mutating MCP tools."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

MCP_WRITE_ENV = "LLX_MCP_ALLOW_WRITE"
MCP_SECRET_ENV = "LLX_MCP_ALLOW_SECRET_OUTPUT"


def approval_hash(action: str, payload: dict[str, Any], actor: str) -> str:
    """Bind an approval to one actor and one exact mutation payload."""
    encoded = json.dumps(
        {"action": action, "payload": {**payload, "actor": actor.strip()}},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def approval_required(
    action: str,
    payload: dict[str, Any],
    *,
    actor: str,
    supplied_hash: str,
) -> tuple[bool, str]:
    expected = approval_hash(action, payload, actor)
    capability_enabled = os.getenv(MCP_WRITE_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    approved = capability_enabled and bool(actor.strip()) and supplied_hash.strip() == expected
    return not approved, expected


def approval_response(
    action: str,
    payload: dict[str, Any],
    *,
    actor: str,
    supplied_hash: str,
) -> dict[str, Any]:
    required, expected = approval_required(
        action,
        payload,
        actor=actor,
        supplied_hash=supplied_hash,
    )
    return {
        "requires_approval": required,
        "approval_hash": expected,
        "approval_payload": payload,
        "required_env": MCP_WRITE_ENV,
        "approved_by": actor.strip() if not required else "",
    }


def resolve_workspace_path(path: str, workspace_root: str, *, must_exist: bool = False) -> Path:
    """Resolve a path and reject escapes outside the selected workspace."""
    root = Path(workspace_root).expanduser().resolve()
    candidate = Path(path).expanduser()
    target = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {path}") from exc
    if must_exist and not target.exists():
        raise ValueError(f"Path does not exist: {target}")
    return target


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_manifest_sha256(files: Mapping[str, str]) -> str:
    """Hash relative paths and exact output contents in stable order."""
    digest = hashlib.sha256()
    for relative, content in sorted(files.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content.encode("utf-8")).digest())
    return digest.hexdigest()


def secret_output_enabled() -> bool:
    return os.getenv(MCP_SECRET_ENV, "").strip().lower() in {"1", "true", "yes", "on"}
