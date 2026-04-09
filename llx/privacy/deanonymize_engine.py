from __future__ import annotations

from pathlib import Path

from llx.privacy.deanonymize_results import DeanonymizationResult, ProjectDeanonymizationResult
from llx.privacy.deanonymize_utils import (
    build_reverse_lookup,
    find_content_tokens,
    find_symbol_tokens,
    get_content_mapping,
    restore_decorators,
    restore_imports,
)
from llx.privacy.project import AnonymizationContext


class ProjectDeanonymizer:
    """Restores original values from anonymized project content.

    Uses AnonymizationContext to reverse all anonymization operations:
    - Symbol names (variables, functions, classes)
    - File paths
    - Module names
    - Content patterns (emails, keys, etc.)
    """

    def __init__(self, context: AnonymizationContext):
        self.context = context
        self._reverse_lookup: dict[str, str] = build_reverse_lookup(context)

    def deanonymize_text(self, text: str, strict: bool = False) -> DeanonymizationResult:
        restorations: list[tuple[str, str]] = []
        unknowns: list[str] = []
        result = text

        symbols = find_symbol_tokens(text)
        for match in symbols:
            token = match.group(0)
            if token in self._reverse_lookup:
                original = self._reverse_lookup[token]
                result = result.replace(token, original)
                restorations.append((token, original))
            else:
                unknowns.append(token)

        content_tokens = find_content_tokens(text)
        content_map = get_content_mapping(self.context)
        for match in content_tokens:
            token = match.group(0)
            if token in content_map:
                original = content_map[token]
                result = result.replace(token, original)
                restorations.append((token, original))
            elif strict:
                unknowns.append(token)

        total_tokens = len(symbols) + len(content_tokens)
        confidence = len(restorations) / total_tokens if total_tokens > 0 else 1.0

        return DeanonymizationResult(
            text=result,
            restorations=restorations,
            unknown_tokens=unknowns,
            confidence=confidence,
        )

    def deanonymize_file(self, content: str, file_path: str | None = None) -> DeanonymizationResult:
        """Deanonymize file content, restoring code symbols and structure."""
        result = self.deanonymize_text(content)
        if file_path and file_path.endswith('.py'):
            result.text = restore_imports(result.text, self._reverse_lookup)
            result.text = restore_decorators(result.text, self._reverse_lookup)
        return result

    def deanonymize_project_files(
        self,
        anonymized_files: dict[str, str],
        output_dir: str | Path | None = None,
    ) -> ProjectDeanonymizationResult:
        """Deanonymize multiple project files."""
        result = ProjectDeanonymizationResult()
        total_confidence = 0.0

        for relative_path, content in anonymized_files.items():
            file_result = self.deanonymize_file(content, relative_path)
            result.files[relative_path] = file_result.text
            result.restorations[relative_path] = len(file_result.restorations)
            result.unknowns[relative_path] = file_result.unknown_tokens
            total_confidence += file_result.confidence

            if output_dir is not None:
                output_path = Path(output_dir) / relative_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(file_result.text, encoding='utf-8')

        if anonymized_files:
            result.overall_confidence = total_confidence / len(anonymized_files)
        else:
            result.overall_confidence = 1.0

        return result
