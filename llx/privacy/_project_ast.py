"""AST-based anonymization helpers for project-level privacy."""

from __future__ import annotations

import ast

from llx.privacy._project_context import AnonymizationContext


__all__ = ["ASTAnonymizer"]


class ASTAnonymizer(ast.NodeTransformer):
    """AST transformer that anonymizes code symbols while preserving structure."""

    RESERVED_NAMES = {
        # Python builtins
        "True",
        "False",
        "None",
        "self",
        "cls",
        "super",
        "object",
        "type",
        "int",
        "str",
        "float",
        "list",
        "dict",
        "set",
        "tuple",
        "Exception",
        "BaseException",
        "ValueError",
        "TypeError",
        "KeyError",
        # Common library names
        "os",
        "sys",
        "json",
        "re",
        "pathlib",
        "typing",
        "dataclasses",
        "abc",
        "collections",
        "itertools",
        "functools",
        "datetime",
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
                original_name,
                "function",
                self.file_path,
                node.lineno,
                scope,
            )

        # Enter function scope
        self.current_scope.append(original_name)

        # Anonymize arguments
        self._local_vars.clear()
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.arg not in self.RESERVED_NAMES:
                original_arg = arg.arg
                arg.arg = self.context.get_or_create_symbol(
                    original_arg,
                    "variable",
                    self.file_path,
                    node.lineno,
                    ".".join(self.current_scope),
                )
                self._local_vars.add(arg.arg)

        if node.args.vararg and node.args.vararg.arg not in self.RESERVED_NAMES:
            node.args.vararg.arg = self.context.get_or_create_symbol(
                node.args.vararg.arg,
                "variable",
                self.file_path,
                node.lineno,
            )

        if node.args.kwarg and node.args.kwarg.arg not in self.RESERVED_NAMES:
            node.args.kwarg.arg = self.context.get_or_create_symbol(
                node.args.kwarg.arg,
                "variable",
                self.file_path,
                node.lineno,
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
            original_name,
            "class",
            self.file_path,
            node.lineno,
            scope,
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
        if (
            node.id not in self.RESERVED_NAMES
            and not node.id.startswith("__")
            and not self._is_builtin(node.id)
        ):
            scope = ".".join(self.current_scope) if self.current_scope else "global"
            node.id = self.context.get_or_create_symbol(
                node.id,
                "variable",
                self.file_path,
                getattr(node, "lineno", None),
                scope,
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
                    target.id,
                    "variable",
                    self.file_path,
                    getattr(node, "lineno", None),
                    scope,
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
            if alias.name not in self.RESERVED_NAMES and not alias.name.startswith("__"):
                # Check if this is a symbol we know about
                if alias.name in self.context.functions or alias.name in self.context.classes:
                    scope = ".".join(self.current_scope) if self.current_scope else "global"
                    alias.name = self.context.get_or_create_symbol(
                        alias.name,
                        "function",
                        self.file_path,
                        getattr(node, "lineno", None),
                        scope,
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
