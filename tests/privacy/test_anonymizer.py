import pytest
from llx.privacy.project import AnonymizationContext, ProjectAnonymizer

class TestProjectAnonymizer:
    def test_anonymize_python_file(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("def calculate_total(items):\n    return sum(item.price for item in items)")
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        result = anonymizer.anonymize_file(test_file)
        assert "calculate_total" not in result
        assert "fn_" in result

    def test_anonymize_simple_text(self):
        ctx = AnonymizationContext(project_path="/tmp")
        anonymizer = ProjectAnonymizer(ctx)
        text = "Email: admin@example.com"
        result = anonymizer.anonymize_string(text)
        assert "admin@example.com" not in result

    def test_anonymize_project_directory(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src/main.py").write_text("def main(): pass")
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        result = anonymizer.anonymize_project(include_patterns=["*.py"])
        assert "src/main.py" in result.files

    def test_respects_file_size_limit(self, tmp_path):
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * 100)
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        result = anonymizer.anonymize_project(include_patterns=["*.py"], max_file_size=50)
        assert len(result.files) == 0