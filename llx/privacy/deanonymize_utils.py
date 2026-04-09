from __future__ import annotations

import re
from typing import Any

from llx.privacy.project import AnonymizationContext, SymbolMapping

SYMBOL_PATTERN = r'\b(var_|fn_|cls_|mod_|pth_)[a-zA-Z0-9_]+\b'
CONTENT_PATTERN = r'\[[A-Z_]+_[A-F0-9]{4,}\]'
IMPORT_PATTERN = r'\b(from|import)\s+(mod_[a-f0-9]{6,})\b'
DECORATOR_PATTERN = r'@\b(fn_|cls_)[a-f0-9]{6,}\b'


def build_reverse_lookup(context: AnonymizationContext) -> dict[str, str]:
    """Build reverse mapping from anonymized token to original name."""
    reverse_lookup: dict[str, str] = {}
    all_mappings: list[dict[str, SymbolMapping]] = [
        context.variables,
        context.functions,
        context.classes,
        context.modules,
        context.paths,
    ]

    for mapping_dict in all_mappings:
        for original, mapping in mapping_dict.items():
            reverse_lookup[mapping.anonymized] = original

    return reverse_lookup


def find_symbol_tokens(text: str) -> list[re.Match[str]]:
    """Find symbol tokens in anonymized text."""
    symbols = list(re.finditer(SYMBOL_PATTERN, text))
    symbols.sort(key=lambda m: len(m.group(0)), reverse=True)
    return symbols


def find_content_tokens(text: str) -> list[re.Match[str]]:
    """Find content anonymization tokens in text."""
    return list(re.finditer(CONTENT_PATTERN, text))


def get_content_mapping(context: AnonymizationContext) -> dict[str, str]:
    """Safely access the last content anonymization mapping."""
    return context.content_anonymizer._last_anonymization_mapping if hasattr(
        context.content_anonymizer,
        '_last_anonymization_mapping',
    ) else {}


def restore_imports(content: str, reverse_lookup: dict[str, str]) -> str:
    """Restore module names in import statements."""
    def replace_import(match: re.Match[str]) -> str:
        keyword = match.group(1)
        module_token = match.group(2)
        if module_token in reverse_lookup:
            return f"{keyword} {reverse_lookup[module_token]}"
        return match.group(0)

    return re.sub(IMPORT_PATTERN, replace_import, content)


def restore_decorators(content: str, reverse_lookup: dict[str, str]) -> str:
    """Restore decorator names."""
    def replace_decorator(match: re.Match[str]) -> str:
        token = match.group(0)[1:]
        if token in reverse_lookup:
            return f"@{reverse_lookup[token]}"
        return match.group(0)

    return re.sub(DECORATOR_PATTERN, replace_decorator, content)
