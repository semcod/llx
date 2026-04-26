from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from llx.privacy._project_ast import ASTAnonymizer
from llx.privacy._project_context import AnonymizationContext


@dataclass
class ProjectAnonymizationResult:
    files: dict[str, str] = field(default_factory=dict)
    context: AnonymizationContext | None = None
    errors: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


class ProjectAnonymizer:
    def __init__(self, context: AnonymizationContext | None = None, project_path: str | Path | None = None):
        if context is None:
            if project_path is None:
                raise ValueError("Either context or project_path must be provided")
            context = AnonymizationContext(project_path)

        self.context = context
        self.errors: list[str] = []

    def anonymize_project(
        self,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        max_file_size: int = 10 * 1024 * 1024,
    ) -> ProjectAnonymizationResult:
        include = include_patterns or ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.yaml", "*.json", "*.toml"]
        exclude = exclude_patterns or [
            "**/.git/**", "**/venv/**", "**/.venv/**", "**/node_modules/**",
            "**/__pycache__/**", "**/.pytest_cache/**", "**/*.pyc",
            "**/.llx/**", "**/dist/**", "**/build/**",
        ]

        result = ProjectAnonymizationResult(context=self.context)
        project_path = Path(self.context.project_path)

        for pattern in include:
            for file_path in project_path.rglob(pattern):
                if any(file_path.match(ex) for ex in exclude):
                    continue

                try:
                    file_size = file_path.stat().st_size
                    if file_size > max_file_size:
                        result.errors.append(f"Skipped (too large): {file_path}")
                        continue
                except OSError as e:
                    result.errors.append(f"Cannot stat {file_path}: {e}")
                    continue

                try:
                    anonymized = self.anonymize_file(file_path)
                    relative_path = str(file_path.relative_to(project_path))
                    result.files[relative_path] = anonymized
                except Exception as e:
                    result.errors.append(f"Error processing {file_path}: {e}")

        result.stats = dict(self.context.stats)
        return result

    def anonymize_file(self, file_path: str | Path) -> str:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8", errors="replace")

        if file_path.suffix == ".py":
            return self._anonymize_python(content, str(file_path))
        if file_path.suffix in (".js", ".ts", ".java", ".go", ".rs"):
            return self._anonymize_source_code(content, str(file_path))
        if file_path.suffix in (".yaml", ".yml", ".json", ".toml"):
            return self._anonymize_config(content, str(file_path))
        return self._anonymize_generic(content, str(file_path))

    def _anonymize_python(self, content: str, file_path: str) -> str:
        try:
            tree = ast.parse(content)
            transformer = ASTAnonymizer(self.context, file_path)
            transformed = transformer.visit(tree)

            transformed = ast.fix_missing_locations(transformed)

            if hasattr(ast, "unparse"):
                return ast.unparse(transformed)

            import astor  # type: ignore

            return astor.to_source(transformed)
        except SyntaxError:
            return self._anonymize_generic(content, file_path)
        except Exception:
            return self._anonymize_source_code(content, file_path)

    def _anonymize_source_code(self, content: str, file_path: str) -> str:
        result = content

        patterns = [
            (r'\b(def|function|func)\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'function'),
            (r'\b(class|struct|interface)\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
            (r'\b(var|let|const)?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]', 'variable'),
        ]

        for pattern, symbol_type in patterns:
            for match in re.finditer(pattern, content):
                original = match.group(2)
                if original not in ASTAnonymizer.RESERVED_NAMES and not original.startswith("__"):
                    anon = self.context.get_or_create_symbol(original, symbol_type, file_path)
                    start = match.start(2)
                    end = match.end(2)
                    result = result[:start] + anon + result[end:]

        return result

    def _anonymize_config(self, content: str, file_path: str) -> str:
        result = self.context.content_anonymizer.anonymize(content)
        return result.text

    def _anonymize_generic(self, content: str, file_path: str) -> str:
        result = self.context.content_anonymizer.anonymize(content)
        return result.text

    def anonymize_string(self, text: str, file_hint: str | None = None) -> str:
        result = text
        for match in re.finditer(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text):
            word = match.group(0)
            if word not in ASTAnonymizer.RESERVED_NAMES and len(word) > 2:
                if word in self.context.variables or word in self.context.functions or word in self.context.classes:
                    anon = self.context.get_or_create_symbol(word, "variable", file_hint)
                    result = result.replace(word, anon)

        content_result = self.context.content_anonymizer.anonymize(result)
        return content_result.text
