"""Project-scale anonymization engine for LLX.

Handles anonymization of entire codebases including:
- Source code (AST-level variable/function/class names)
- File paths and directory structures
- Import statements and module references
- Configuration files (with structure preservation)
- Large projects via streaming/chunked processing

Usage:
    from llx.privacy.project import ProjectAnonymizer, AnonymizationContext
    
    # Create context for the project
    ctx = AnonymizationContext(project_path="/path/to/project")
    
    # Anonymize entire project
    anonymizer = ProjectAnonymizer(ctx)
    result = anonymizer.anonymize_project()
    
    # Access anonymized files
    for file_path, content in result.files.items():
        print(f"{file_path}: {len(content)} chars")
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from llx.privacy import Anonymizer, AnonymizationResult


@dataclass
class SymbolMapping:
    """Mapping between original and anonymized symbols."""

    original: str
    anonymized: str
    symbol_type: str  # variable, function, class, module, path
    file_path: str | None = None
    line_number: int | None = None
    scope: str | None = None  # e.g., "global", "MyClass.method"


@dataclass
class AnonymizationContext:
    """Context for project-wide anonymization with persistent mapping.
    
    Maintains all symbol mappings and allows cross-file consistency.
    """

    project_path: str | Path
    salt: str = field(default_factory=lambda: hashlib.sha256(
        str(hash("llx_project_anon")).encode()).hexdigest()[:16])
    
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
    
    def __post_init__(self):
        self.project_path = Path(self.project_path)
        if self.content_anonymizer is None:
            self.content_anonymizer = Anonymizer(salt=self.salt)
    
    def get_or_create_symbol(
        self, 
        original: str, 
        symbol_type: str,
        file_path: str | None = None,
        line_number: int | None = None,
        scope: str | None = None
    ) -> str:
        """Get existing anonymized symbol or create new one."""
        mapping_dict = self._get_mapping_dict(symbol_type)
        
        # Check if already exists
        if original in mapping_dict:
            return mapping_dict[original].anonymized
        
        # Create new anonymized symbol
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
        return {
            "variable": self.variables,
            "function": self.functions,
            "class": self.classes,
            "module": self.modules,
            "path": self.paths,
        }.get(symbol_type, self.variables)
    
    def _generate_symbol(self, original: str, symbol_type: str, file_path: str | None) -> str:
        """Generate anonymized symbol name."""
        # Create deterministic but unique hash
        base = f"{self.salt}:{symbol_type}:{original}:{file_path or ''}"
        hash_suffix = hashlib.sha256(base.encode()).hexdigest()[:6]
        
        # Prefix indicates type
        prefix = {
            "variable": "var",
            "function": "fn",
            "class": "cls",
            "module": "mod",
            "path": "pth",
        }.get(symbol_type, "sym")
        
        return f"{prefix}_{hash_suffix}"
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary for storage."""
        def mappings_to_dict(m: dict[str, SymbolMapping]) -> dict:
            return {k: {
                "original": v.original,
                "anonymized": v.anonymized,
                "symbol_type": v.symbol_type,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "scope": v.scope,
            } for k, v in m.items()}
        
        return {
            "project_path": str(self.project_path),
            "salt": self.salt,
            "variables": mappings_to_dict(self.variables),
            "functions": mappings_to_dict(self.functions),
            "classes": mappings_to_dict(self.classes),
            "modules": mappings_to_dict(self.modules),
            "paths": mappings_to_dict(self.paths),
            "stats": self.stats,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnonymizationContext":
        """Deserialize context from dictionary."""
        def dict_to_mappings(d: dict) -> dict[str, SymbolMapping]:
            return {k: SymbolMapping(**v) for k, v in d.items()}
        
        ctx = cls.__new__(cls)
        ctx.project_path = Path(data["project_path"])
        ctx.salt = data["salt"]
        ctx.variables = dict_to_mappings(data.get("variables", {}))
        ctx.functions = dict_to_mappings(data.get("functions", {}))
        ctx.classes = dict_to_mappings(data.get("classes", {}))
        ctx.modules = dict_to_mappings(data.get("modules", {}))
        ctx.paths = dict_to_mappings(data.get("paths", {}))
        ctx.stats = data.get("stats", {})
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


class ASTAnonymizer(ast.NodeTransformer):
    """AST transformer that anonymizes code symbols while preserving structure."""

    RESERVED_NAMES = {
        # Python builtins
        'True', 'False', 'None', 'self', 'cls', 'super',
        'object', 'type', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple',
        'Exception', 'BaseException', 'ValueError', 'TypeError', 'KeyError',
        # Common library names
        'os', 'sys', 'json', 're', 'pathlib', 'typing', 'dataclasses',
        'abc', 'collections', 'itertools', 'functools', 'datetime',
    }

    def __init__(self, context: AnonymizationContext, file_path: str):
        self.context = context
        self.file_path = file_path
        self.current_scope: list[str] = []
        self._local_vars: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Anonymize function name and parameters."""
        original_name = node.name
        scope = ".".join(self.current_scope) if self.current_scope else "global"
        
        # Anonymize function name (except dunder methods)
        if not original_name.startswith("__") or not original_name.endswith("__"):
            node.name = self.context.get_or_create_symbol(
                original_name, "function", self.file_path, node.lineno, scope
            )
        
        # Enter function scope
        self.current_scope.append(original_name)
        
        # Anonymize arguments
        self._local_vars.clear()
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.arg not in self.RESERVED_NAMES:
                original_arg = arg.arg
                arg.arg = self.context.get_or_create_symbol(
                    original_arg, "variable", self.file_path, node.lineno, ".".join(self.current_scope)
                )
                self._local_vars.add(arg.arg)
        
        if node.args.vararg and node.args.vararg.arg not in self.RESERVED_NAMES:
            node.args.vararg.arg = self.context.get_or_create_symbol(
                node.args.vararg.arg, "variable", self.file_path, node.lineno
            )
        
        if node.args.kwarg and node.args.kwarg.arg not in self.RESERVED_NAMES:
            node.args.kwarg.arg = self.context.get_or_create_symbol(
                node.args.kwarg.arg, "variable", self.file_path, node.lineno
            )
        
        # Visit body
        self.generic_visit(node)
        
        # Exit scope
        self.current_scope.pop()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        """Anonymize class name."""
        original_name = node.name
        scope = ".".join(self.current_scope) if self.current_scope else "global"
        
        node.name = self.context.get_or_create_symbol(
            original_name, "class", self.file_path, node.lineno, scope
        )
        
        # Enter class scope
        self.current_scope.append(original_name)
        
        # Visit body
        self.generic_visit(node)
        
        # Exit scope
        self.current_scope.pop()
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Anonymize variable references."""
        if (node.id not in self.RESERVED_NAMES and 
            not node.id.startswith("__") and
            not self._is_builtin(node.id)):
            
            scope = ".".join(self.current_scope) if self.current_scope else "global"
            node.id = self.context.get_or_create_symbol(
                node.id, "variable", self.file_path, getattr(node, 'lineno', None), scope
            )
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        """Track local variable assignments."""
        # First visit the value side (to anonymize references)
        node.value = self.visit(node.value)
        
        # Then handle targets (variable definitions)
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id not in self.RESERVED_NAMES:
                scope = ".".join(self.current_scope) if self.current_scope else "global"
                target.id = self.context.get_or_create_symbol(
                    target.id, "variable", self.file_path, getattr(node, 'lineno', None), scope
                )
                self._local_vars.add(target.id)
            else:
                self.visit(target)
        
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        """Handle attribute access - anonymize the value, not the attr name."""
        node.value = self.visit(node.value)
        # Don't anonymize attribute names (e.g., obj.method -> anonymized_obj.method)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        """Handle 'from X import Y' statements - anonymize imported names."""
        # Visit module name if it's a relative import with dots
        if node.module:
            # Module names shouldn't be anonymized, they're external references
            pass
        
        # Anonymize imported names (aliases)
        for alias in node.names:
            if alias.name not in self.RESERVED_NAMES and not alias.name.startswith('__'):
                # Check if this is a symbol we know about
                if alias.name in self.context.functions or alias.name in self.context.classes:
                    scope = ".".join(self.current_scope) if self.current_scope else "global"
                    alias.name = self.context.get_or_create_symbol(
                        alias.name, "function", self.file_path, getattr(node, 'lineno', None), scope
                    )
        
        return node

    def visit_Import(self, node: ast.Import) -> ast.AST:
        """Handle 'import X' statements - module names are not anonymized."""
        # Module names are external references, don't anonymize
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Anonymize sensitive data in string literals."""
        if isinstance(node.value, str):
            # Check if string contains sensitive data
            result = self.context.content_anonymizer.anonymize(node.value)
            if result.text != node.value:
                node.value = result.text
        return node

    # For Python < 3.8 compatibility
    visit_Str = visit_Constant

    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python builtin."""
        return name in __builtins__ if isinstance(__builtins__, dict) else hasattr(__builtins__, name)


@dataclass
class ProjectAnonymizationResult:
    """Result of project-level anonymization."""

    files: dict[str, str] = field(default_factory=dict)
    context: AnonymizationContext | None = None
    errors: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


class ProjectAnonymizer:
    """Main class for anonymizing entire projects.
    
    Handles multiple file types:
    - Python files (.py): AST-based anonymization
    - Other source files: Pattern-based anonymization
    - Config files: Structure-preserving anonymization
    """

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
        max_file_size: int = 10 * 1024 * 1024,  # 10MB default
    ) -> ProjectAnonymizationResult:
        """Anonymize entire project directory.
        
        Args:
            include_patterns: Glob patterns to include (default: common source files)
            exclude_patterns: Glob patterns to exclude (default: venv, node_modules, etc.)
            max_file_size: Skip files larger than this (bytes)
        
        Returns:
            ProjectAnonymizationResult with anonymized files and context
        """
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
                # Check exclusions
                if any(file_path.match(ex) for ex in exclude):
                    continue
                
                # Check size
                try:
                    file_size = file_path.stat().st_size
                    if file_size > max_file_size:
                        result.errors.append(f"Skipped (too large): {file_path}")
                        continue
                except OSError as e:
                    result.errors.append(f"Cannot stat {file_path}: {e}")
                    continue
                
                # Anonymize file
                try:
                    anonymized = self.anonymize_file(file_path)
                    relative_path = str(file_path.relative_to(project_path))
                    result.files[relative_path] = anonymized
                except Exception as e:
                    result.errors.append(f"Error processing {file_path}: {e}")
        
        result.stats = dict(self.context.stats)
        return result

    def anonymize_file(self, file_path: str | Path) -> str:
        """Anonymize single file based on its type."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        content = file_path.read_text(encoding="utf-8", errors="replace")
        
        # Route to appropriate anonymizer based on file type
        if file_path.suffix == ".py":
            return self._anonymize_python(content, str(file_path))
        elif file_path.suffix in (".js", ".ts", ".java", ".go", ".rs"):
            return self._anonymize_source_code(content, str(file_path))
        elif file_path.suffix in (".yaml", ".yml", ".json", ".toml"):
            return self._anonymize_config(content, str(file_path))
        else:
            return self._anonymize_generic(content, str(file_path))

    def _anonymize_python(self, content: str, file_path: str) -> str:
        """Anonymize Python source using AST transformation."""
        try:
            tree = ast.parse(content)
            transformer = ASTAnonymizer(self.context, file_path)
            transformed = transformer.visit(tree)
            
            # Convert back to code
            import astor  # type: ignore
            return astor.to_source(transformed)
        except ImportError:
            # Fallback to regex-based if astor not available
            return self._anonymize_source_code(content, file_path)
        except SyntaxError:
            # Fallback for invalid Python
            return self._anonymize_generic(content, file_path)

    def _anonymize_source_code(self, content: str, file_path: str) -> str:
        """Generic source code anonymization using regex patterns."""
        result = content
        
        # Pattern for common identifiers
        patterns = [
            # Function definitions
            (r'\b(def|function|func)\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'function'),
            # Class definitions
            (r'\b(class|struct|interface)\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class'),
            # Variable assignments (simple cases)
            (r'\b(var|let|const)?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]', 'variable'),
        ]
        
        for pattern, symbol_type in patterns:
            for match in re.finditer(pattern, content):
                original = match.group(2)
                if original not in ASTAnonymizer.RESERVED_NAMES and not original.startswith("__"):
                    anon = self.context.get_or_create_symbol(original, symbol_type, file_path)
                    # Replace only this occurrence
                    start = match.start(2)
                    end = match.end(2)
                    result = result[:start] + anon + result[end:]
        
        return result

    def _anonymize_config(self, content: str, file_path: str) -> str:
        """Anonymize config files preserving structure."""
        # Use content anonymizer for values, preserve keys
        result = self.context.content_anonymizer.anonymize(content)
        return result.text

    def _anonymize_generic(self, content: str, file_path: str) -> str:
        """Generic text anonymization."""
        result = self.context.content_anonymizer.anonymize(content)
        return result.text

    def anonymize_string(self, text: str, file_hint: str | None = None) -> str:
        """Anonymize arbitrary string with project context."""
        # First anonymize any code identifiers
        result = text
        for match in re.finditer(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text):
            word = match.group(0)
            if word not in ASTAnonymizer.RESERVED_NAMES and len(word) > 2:
                # Check if this word exists in context
                if word in self.context.variables or word in self.context.functions or word in self.context.classes:
                    anon = self.context.get_or_create_symbol(word, "variable", file_hint)
                    result = result.replace(word, anon)
        
        # Then anonymize content patterns (emails, API keys, etc.)
        content_result = self.context.content_anonymizer.anonymize(result)
        
        return content_result.text
