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

from llx.privacy import _project_anonymizer as _project_anonymizer
from llx.privacy import _project_ast as _project_ast
from llx.privacy import _project_context as _project_context


AnonymizationContext = _project_context.AnonymizationContext
SymbolMapping = _project_context.SymbolMapping
ASTAnonymizer = _project_ast.ASTAnonymizer
ProjectAnonymizationResult = _project_anonymizer.ProjectAnonymizationResult
ProjectAnonymizer = _project_anonymizer.ProjectAnonymizer

__all__ = [
    "AnonymizationContext",
    "SymbolMapping",
    "ASTAnonymizer",
    "ProjectAnonymizationResult",
    "ProjectAnonymizer",
]
