"""Tests for project-level deanonymization."""

from llx.privacy.project import (
    AnonymizationContext,
)
from llx.privacy.deanonymize import (
    ProjectDeanonymizer,
)


class TestProjectDeanonymizer:
    """Test project-level deanonymization."""

    def test_deanonymize_symbol(self):
        """Should restore original symbol from anonymized."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("original_function", "function", "file.py", 1)
        
        deanonymizer = ProjectDeanonymizer(ctx)
        
        # Get the anonymized name
        anon_name = ctx.functions["original_function"].anonymized
        
        # Deanonymize
        result = deanonymizer.deanonymize_text(f"Use {anon_name} to process data")
        
        assert "original_function" in result.text
        assert anon_name not in result.text

    def test_deanonymize_content_tokens(self):
        """Should restore content anonymization tokens."""
        ctx = AnonymizationContext(project_path="/tmp")
        # Simulate content anonymization
        content_result = ctx.content_anonymizer.anonymize("Email: test@example.com")
        ctx.content_anonymizer._last_anonymization_mapping = content_result.mapping
        
        deanonymizer = ProjectDeanonymizer(ctx)
        
        # Deanonymize text with content token
        anon_text = content_result.text
        result = deanonymizer.deanonymize_text(anon_text)
        
        assert "test@example.com" in result.text

    def test_deanonymize_chat_response(self):
        """Quick deanonymization for LLM responses."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("calculate_sum", "function", "file.py", 1)
        ctx.get_or_create_symbol("user_data", "variable", "file.py", 5)
        
        deanonymizer = ProjectDeanonymizer(ctx)
        
        llm_response = f"Call {ctx.functions['calculate_sum'].anonymized} with {ctx.variables['user_data'].anonymized}"
        restored = deanonymizer.deanonymize_chat_response(llm_response)
        
        assert "calculate_sum" in restored
        assert "user_data" in restored

    def test_deanonymize_project_files(self, tmp_path):
        """Should deanonymize multiple project files."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("process_data", "function", "main.py", 1)
        
        anon_func = ctx.functions["process_data"].anonymized
        
        files = {
            "main.py": f"def {anon_func}(): pass",
            "utils.py": f"from main import {anon_func}",
        }