import pytest
from llx.privacy.project import AnonymizationContext
from llx.privacy.deanonymize import ProjectDeanonymizer

class TestProjectDeanonymizer:
    def test_deanonymize_symbol(self):
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("original_function", "function", "file.py", 1)
        deanonymizer = ProjectDeanonymizer(ctx)
        anon_name = ctx.functions["original_function"].anonymized
        result = deanonymizer.deanonymize_text(f"Use {anon_name} to process data")
        assert "original_function" in result.text

    def test_deanonymize_chat_response(self):
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("calculate_sum", "function", "file.py", 1)
        deanonymizer = ProjectDeanonymizer(ctx)
        llm_response = f"Call {ctx.functions['calculate_sum'].anonymized}"
        restored = deanonymizer.deanonymize_chat_response(llm_response)
        assert "calculate_sum" in restored