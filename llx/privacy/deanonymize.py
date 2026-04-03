"""Project-scale deanonymization engine for LLX.

Restores original values from anonymized LLM responses and code.
Works with AnonymizationContext to provide full project restoration.

Usage:
    from llx.privacy.deanonymize import ProjectDeanonymizer, DeanonymizationResult
    from llx.privacy.project import AnonymizationContext
    
    # Load saved context from anonymization phase
    ctx = AnonymizationContext.load("project.anon.json")
    
    # Create deanonymizer
    deanonymizer = ProjectDeanonymizer(ctx)
    
    # Restore LLM response
    llm_response = "Use fn_ABC123 to call the api with var_XYZ789"
    restored = deanonymizer.deanonymize_text(llm_response)
    # Result: "Use calculate_total to call the api with user_data"
    
    # Restore entire project files
    anon_files = {"src/main.py": "def fn_ABC123(): pass"}
    result = deanonymizer.deanonymize_project_files(anon_files)
    # Result: {"src/main.py": "def calculate_total(): pass"}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from llx.privacy.project import AnonymizationContext, SymbolMapping


@dataclass
class DeanonymizationResult:
    """Result of deanonymization operation."""

    text: str
    restorations: list[tuple[str, str]] = field(default_factory=list)  # (token, original)
    unknown_tokens: list[str] = field(default_factory=list)
    confidence: float = 1.0  # Ratio of found tokens to total tokens


@dataclass
class ProjectDeanonymizationResult:
    """Result of project-level deanonymization."""

    files: dict[str, str] = field(default_factory=dict)
    restorations: dict[str, int] = field(default_factory=dict)
    unknowns: dict[str, list[str]] = field(default_factory=dict)
    overall_confidence: float = 0.0


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
        
        # Build reverse lookup: anonymized -> original
        self._reverse_lookup: dict[str, str] = {}
        self._build_reverse_lookup()

    def _build_reverse_lookup(self) -> None:
        """Build reverse mapping from all symbol mappings."""
        all_mappings: list[dict[str, SymbolMapping]] = [
            self.context.variables,
            self.context.functions,
            self.context.classes,
            self.context.modules,
            self.context.paths,
        ]
        
        for mapping_dict in all_mappings:
            for original, mapping in mapping_dict.items():
                self._reverse_lookup[mapping.anonymized] = original

    def deanonymize_text(
        self, 
        text: str,
        strict: bool = False
    ) -> DeanonymizationResult:
        """Deanonymize text (e.g., LLM response) using context.
        
        Args:
            text: Anonymized text with tokens like "fn_ABC123", "[EMAIL_...]"
            strict: If True, report unknown tokens as errors
            
        Returns:
            DeanonymizationResult with restored text and restoration info
        """
        restorations: list[tuple[str, str]] = []
        unknowns: list[str] = []
        result = text
        
        # Find all potential anonymized tokens
        # Pattern 1: Project symbols (var_*, fn_*, cls_*, mod_*, pth_*)
        # Match any alphanumeric after prefix (not just hex, to catch unknown/invalid tokens)
        symbol_pattern = r'\b(var_|fn_|cls_|mod_|pth_)[a-zA-Z0-9_]+\b'
        
        # Pattern 2: Content anonymization tokens ([EMAIL_...], [APIKEY_...], etc.)
        content_pattern = r'\[[A-Z_]+_[A-F0-9]{4,}\]'
        
        # Process symbols (longer first to avoid partial matches)
        symbols = list(re.finditer(symbol_pattern, text))
        symbols.sort(key=lambda m: len(m.group(0)), reverse=True)
        
        for match in symbols:
            token = match.group(0)
            if token in self._reverse_lookup:
                original = self._reverse_lookup[token]
                result = result.replace(token, original)
                restorations.append((token, original))
            else:
                unknowns.append(token)
        
        # Process content tokens from content_anonymizer mapping
        content_tokens = list(re.finditer(content_pattern, text))
        for match in content_tokens:
            token = match.group(0)
            # Check in content anonymizer mapping
            content_map = self.context.content_anonymizer._last_anonymization_mapping if hasattr(
                self.context.content_anonymizer, '_last_anonymization_mapping') else {}
            
            if token in content_map:
                original = content_map[token]
                result = result.replace(token, original)
                restorations.append((token, original))
            elif strict:
                unknowns.append(token)
        
        # Calculate confidence
        total_tokens = len(symbols) + len(content_tokens)
        if total_tokens > 0:
            confidence = len(restorations) / total_tokens
        else:
            confidence = 1.0
        
        return DeanonymizationResult(
            text=result,
            restorations=restorations,
            unknown_tokens=unknowns,
            confidence=confidence,
        )

    def deanonymize_file(self, content: str, file_path: str | None = None) -> DeanonymizationResult:
        """Deanonymize file content, restoring code symbols and structure."""
        # First do standard text deanonymization
        result = self.deanonymize_text(content)
        
        # Additional processing for code files
        if file_path and file_path.endswith('.py'):
            # Restore import statements (modules)
            result.text = self._restore_imports(result.text)
            
            # Restore decorators
            result.text = self._restore_decorators(result.text)
        
        return result

    def _restore_imports(self, content: str) -> str:
        """Restore module names in import statements."""
        # Pattern: import mod_XYZ or from mod_XYZ import ...
        import_pattern = r'\b(from|import)\s+(mod_[a-f0-9]{6,})\b'
        
        def replace_import(match: re.Match) -> str:
            keyword = match.group(1)
            module_token = match.group(2)
            if module_token in self._reverse_lookup:
                original_module = self._reverse_lookup[module_token]
                return f"{keyword} {original_module}"
            return match.group(0)
        
        return re.sub(import_pattern, replace_import, content)

    def _restore_decorators(self, content: str) -> str:
        """Restore decorator names."""
        # Pattern: @fn_XYZ or @cls_XYZ
        decorator_pattern = r'@\b(fn_|cls_)[a-f0-9]{6,}\b'
        
        def replace_decorator(match: re.Match) -> str:
            token = match.group(0)[1:]  # Remove @
            if token in self._reverse_lookup:
                original = self._reverse_lookup[token]
                return f"@{original}"
            return match.group(0)
        
        return re.sub(decorator_pattern, replace_decorator, content)

    def deanonymize_project_files(
        self,
        anonymized_files: dict[str, str],
        output_dir: str | Path | None = None
    ) -> ProjectDeanonymizationResult:
        """Deanonymize multiple project files.
        
        Args:
            anonymized_files: Dict of {relative_path: anonymized_content}
            output_dir: Optional directory to write restored files
            
        Returns:
            ProjectDeanonymizationResult with all restored files
        """
        result = ProjectDeanonymizationResult()
        total_restorations = 0
        
        for file_path, content in anonymized_files.items():
            deanonymized = self.deanonymize_file(content, file_path)
            result.files[file_path] = deanonymized.text
            total_restorations += len(deanonymized.restorations)
            result.restorations[file_path] = len(deanonymized.restorations)
            
            if deanonymized.unknown_tokens:
                result.unknowns[file_path] = deanonymized.unknown_tokens
        
        # Calculate overall confidence
        if result.files:
            confidences = []
            for file_path, content in anonymized_files.items():
                deanon = self.deanonymize_text(content)
                confidences.append(deanon.confidence)
            result.overall_confidence = sum(confidences) / len(confidences)
        
        # Write to output if specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            for file_path, content in result.files.items():
                target = output_path / file_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
        
        return result

    def deanonymize_chat_response(self, response_text: str) -> str:
        """Quick deanonymization for LLM chat responses.
        
        This is a convenience method for simple use cases.
        For full control, use deanonymize_text().
        """
        result = self.deanonymize_text(response_text)
        return result.text

    def get_symbol_info(self, anonymized_name: str) -> dict[str, Any] | None:
        """Get information about an anonymized symbol."""
        if anonymized_name in self._reverse_lookup:
            original = self._reverse_lookup[anonymized_name]
            
            # Find which mapping dict it came from
            for mapping_dict in [
                self.context.variables,
                self.context.functions,
                self.context.classes,
                self.context.modules,
                self.context.paths,
            ]:
                if original in mapping_dict:
                    mapping = mapping_dict[original]
                    return {
                        "anonymized": anonymized_name,
                        "original": original,
                        "type": mapping.symbol_type,
                        "file": mapping.file_path,
                        "line": mapping.line_number,
                        "scope": mapping.scope,
                    }
        return None

    def list_all_mappings(self) -> dict[str, list[dict[str, Any]]]:
        """List all symbol mappings organized by type."""
        result: dict[str, list[dict[str, Any]]] = {
            "variables": [],
            "functions": [],
            "classes": [],
            "modules": [],
            "paths": [],
        }
        
        for type_name, mapping_dict in [
            ("variables", self.context.variables),
            ("functions", self.context.functions),
            ("classes", self.context.classes),
            ("modules", self.context.modules),
            ("paths", self.context.paths),
        ]:
            for mapping in mapping_dict.values():
                result[type_name].append({
                    "original": mapping.original,
                    "anonymized": mapping.anonymized,
                    "file": mapping.file_path,
                    "line": mapping.line_number,
                    "scope": mapping.scope,
                })
        
        return result


class StreamingDeanonymizer:
    """Deanonymizer for streaming/chunked LLM responses.
    
    Handles cases where LLM output arrives in chunks and tokens
    might be split across chunk boundaries.
    """

    def __init__(self, context: AnonymizationContext):
        self.context = context
        self.deanonymizer = ProjectDeanonymizer(context)
        self._buffer = ""
        self._completed_restorations: list[tuple[str, str]] = []

    def feed_chunk(self, chunk: str) -> str:
        """Process a chunk of text, handling split tokens.
        
        Args:
            chunk: New text chunk from LLM
            
        Returns:
            Deanonymized text ready to output
        """
        self._buffer += chunk
        
        # Check if buffer ends with what looks like an incomplete anonymized token
        # Anonymized tokens look like: fn_xxxxxx, var_xxxxxx, cls_xxxxxx, etc.
        # where xxxxxx is 6 hex characters
        
        # Pattern for complete tokens (prefix + 6+ hex chars)
        complete_token_pattern = r'(var_|fn_|cls_|mod_|pth_)[a-f0-9]{6,}'
        # Pattern for partial/incomplete tokens (prefix + <6 hex chars or no boundary)
        partial_token_pattern = r'(var_|fn_|cls_|mod_|pth_)[a-f0-9]{0,5}$'
        
        # Check if buffer ends with a partial token
        ends_with_partial = bool(re.search(partial_token_pattern, self._buffer, re.IGNORECASE))
        
        # Also check if there's a word boundary after any complete token
        has_boundary_after = bool(re.search(complete_token_pattern + r'[^a-zA-Z0-9_]', self._buffer, re.IGNORECASE))
        
        if ends_with_partial and not chunk.endswith(('\n', ' ', '\t', '.', ',', ';', ':', '(', ')', '[', ']', '{', '}')):
            # Potential partial token at end, keep in buffer
            # Find the last safe position (whitespace or punctuation before the partial token)
            match = re.search(partial_token_pattern, self._buffer, re.IGNORECASE)
            if match:
                # Process everything before the partial token
                to_process = self._buffer[:match.start()]
                self._buffer = self._buffer[match.start():]
            else:
                # No clear partial token, try to find last boundary
                last_boundary = max(
                    self._buffer.rfind(' '),
                    self._buffer.rfind('\n'),
                    self._find_punctuation_boundary(),
                )
                if last_boundary > 0:
                    to_process = self._buffer[:last_boundary]
                    self._buffer = self._buffer[last_boundary:]
                else:
                    return ""  # Nothing safe to output yet
        else:
            to_process = self._buffer
            self._buffer = ""
        
        # Deanonymize the safe portion
        if to_process:
            result = self.deanonymizer.deanonymize_text(to_process)
            self._completed_restorations.extend(result.restorations)
            return result.text
        
        return ""
    
    def _find_punctuation_boundary(self) -> int:
        """Find the last punctuation boundary in buffer."""
        for i in range(len(self._buffer) - 1, -1, -1):
            if self._buffer[i] in '.,;:!?()[]{}<>"\'':
                return i
        return -1

    def finalize(self) -> str:
        """Process any remaining buffered content."""
        if self._buffer:
            result = self.deanonymizer.deanonymize_text(self._buffer)
            self._completed_restorations.extend(result.restorations)
            self._buffer = ""
            return result.text
        return ""

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about processed stream."""
        return {
            "total_restorations": len(self._completed_restorations),
            "unique_symbols_restored": len(set(r[1] for r in self._completed_restorations)),
            "buffer_remaining": len(self._buffer),
        }


def quick_project_deanonymize(
    text: str,
    context_path: str | Path | AnonymizationContext
) -> str:
    """One-shot deanonymization using saved context.
    
    Args:
        text: Anonymized text
        context_path: Path to saved context JSON file or AnonymizationContext object
        
    Returns:
        Deanonymized text
    """
    if isinstance(context_path, (str, Path)):
        context = AnonymizationContext.load(context_path)
    else:
        context = context_path
    
    deanonymizer = ProjectDeanonymizer(context)
    return deanonymizer.deanonymize_chat_response(text)
