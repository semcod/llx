"""Tests for project-level anonymization."""

from pathlib import Path

from llx.privacy.project import (
    AnonymizationContext,
    ProjectAnonymizer,
)


class TestProjectAnonymizer:
    """Test project-level anonymization."""

    def test_anonymize_python_file(self, tmp_path):
        """Should anonymize Python file AST."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def calculate_total(items):
    result = 0
    for item in items:
        result += item.price
    return result

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, product):
        self.items.append(product)
""")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_file(test_file)
        
        # Original names should not be present
        assert "calculate_total" not in result or "items" not in result
        # Anonymized names should be present
        assert "fn_" in result or "cls_" in result

    def test_anonymize_simple_text(self):
        """Should anonymize text with context."""
        ctx = AnonymizationContext(project_path="/tmp")
        anonymizer = ProjectAnonymizer(ctx)
        
        text = "Email: admin@example.com, API: sk-abcdefghijklmnopqrstuv"
        result = anonymizer.anonymize_string(text)
        
        assert "admin@example.com" not in result
        assert "[EMAIL_" in result

    def test_anonymize_project_directory(self, tmp_path):
        """Should anonymize entire project directory."""
        # Create project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("""
def main():
    user_data = load_data()
    process(user_data)
""")
        (tmp_path / "config.yaml").write_text("api_key: sk-abcdefghijklmnopqrstuv")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_project(include_patterns=["*.py", "*.yaml"])
        
        assert len(result.files) == 2
        assert "src/main.py" in result.files
        assert "config.yaml" in result.files

    def test_respects_file_size_limit(self, tmp_path):
        """Should skip files exceeding size limit."""
        # Create large file
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * 100)
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_project(
            include_patterns=["*.py"],
            max_file_size=50  # 50 bytes - file is 100 bytes
        )
        
        assert len(result.files) == 0
        assert len(result.errors) > 0