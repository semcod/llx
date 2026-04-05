"""Shared project anonymization context and symbol mapping utilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llx.privacy.__core import Anonymizer


__all__ = ["SymbolMapping", "AnonymizationContext"]


_SYMBOL_PREFIXES: dict[str, str] = {
    "variable": "var",
    "function": "fn",
    "class": "cls",
    "module": "mod",
    "path": "pth",
}


@dataclass
class SymbolMapping:
    """Mapping between original and anonymized symbols."""

    original: str
    anonymized: str
    symbol_type: str  # variable, function, class, module, path
    file_path: str | None = None
    line_number: int | None = None
    scope: str | None = None  # e.g., "global", "MyClass.method"


def _default_salt() -> str:
    return hashlib.sha256(str(hash("llx_project_anon")).encode()).hexdigest()[:16]


def _mapping_dict_for(
    context: "AnonymizationContext",
    symbol_type: str,
) -> dict[str, SymbolMapping]:
    return {
        "variable": context.variables,
        "function": context.functions,
        "class": context.classes,
        "module": context.modules,
        "path": context.paths,
    }.get(symbol_type, context.variables)


def _symbol_prefix(symbol_type: str) -> str:
    return _SYMBOL_PREFIXES.get(symbol_type, "sym")


def _mappings_to_dict(mappings: dict[str, SymbolMapping]) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "original": value.original,
            "anonymized": value.anonymized,
            "symbol_type": value.symbol_type,
            "file_path": value.file_path,
            "line_number": value.line_number,
            "scope": value.scope,
        }
        for key, value in mappings.items()
    }


def _dict_to_mappings(data: dict[str, Any]) -> dict[str, SymbolMapping]:
    return {key: SymbolMapping(**value) for key, value in data.items()}


@dataclass
class AnonymizationContext:
    """Context for project-wide anonymization with persistent mapping.

    Maintains all symbol mappings and allows cross-file consistency.
    """

    project_path: str | Path
    salt: str = field(default_factory=_default_salt)

    # Symbol mappings by type
    variables: dict[str, SymbolMapping] = field(default_factory=dict)
    functions: dict[str, SymbolMapping] = field(default_factory=dict)
    classes: dict[str, SymbolMapping] = field(default_factory=dict)
    modules: dict[str, SymbolMapping] = field(default_factory=dict)
    paths: dict[str, SymbolMapping] = field(default_factory=dict)

    # Content anonymization for non-code data
    content_anonymizer: Anonymizer | None = None

    # Statistics
    stats: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.project_path = Path(self.project_path)
        if self.content_anonymizer is None:
            self.content_anonymizer = Anonymizer(salt=self.salt)

    def get_or_create_symbol(
        self,
        original: str,
        symbol_type: str,
        file_path: str | None = None,
        line_number: int | None = None,
        scope: str | None = None,
    ) -> str:
        """Get existing anonymized symbol or create new one."""
        mapping_dict = self._get_mapping_dict(symbol_type)

        if original in mapping_dict:
            return mapping_dict[original].anonymized

        anon_symbol = self._generate_symbol(original, symbol_type, file_path)
        mapping = SymbolMapping(
            original=original,
            anonymized=anon_symbol,
            symbol_type=symbol_type,
            file_path=file_path,
            line_number=line_number,
            scope=scope,
        )
        mapping_dict[original] = mapping
        self.stats[symbol_type] = self.stats.get(symbol_type, 0) + 1

        return anon_symbol

    def _get_mapping_dict(self, symbol_type: str) -> dict[str, SymbolMapping]:
        """Get appropriate mapping dictionary for symbol type."""
        return _mapping_dict_for(self, symbol_type)

    def _generate_symbol(
        self,
        original: str,
        symbol_type: str,
        file_path: str | None,
    ) -> str:
        """Generate anonymized symbol name."""
        base = f"{self.salt}:{symbol_type}:{original}:{file_path or ''}"
        hash_suffix = hashlib.sha256(base.encode()).hexdigest()[:6]
        return f"{_symbol_prefix(symbol_type)}_{hash_suffix}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary for storage."""
        return {
            "project_path": str(self.project_path),
            "salt": self.salt,
            "variables": _mappings_to_dict(self.variables),
            "functions": _mappings_to_dict(self.functions),
            "classes": _mappings_to_dict(self.classes),
            "modules": _mappings_to_dict(self.modules),
            "paths": _mappings_to_dict(self.paths),
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnonymizationContext":
        """Deserialize context from dictionary."""
        ctx = cls.__new__(cls)
        ctx.project_path = Path(data["project_path"])
        ctx.salt = data["salt"]
        ctx.variables = _dict_to_mappings(data.get("variables", {}))
        ctx.functions = _dict_to_mappings(data.get("functions", {}))
        ctx.classes = _dict_to_mappings(data.get("classes", {}))
        ctx.modules = _dict_to_mappings(data.get("modules", {}))
        ctx.paths = _dict_to_mappings(data.get("paths", {}))
        ctx.stats = dict(data.get("stats", {}))
        ctx.content_anonymizer = Anonymizer(salt=ctx.salt)
        return ctx

    def save(self, path: str | Path) -> None:
        """Save context to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "AnonymizationContext":
        """Load context from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
