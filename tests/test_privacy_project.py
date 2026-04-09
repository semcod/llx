"""Tests for project-level anonymization and deanonymization."""

from pathlib import Path


from llx.privacy.project import (
    AnonymizationContext,
    ProjectAnonymizer,
)
from llx.privacy.deanonymize import (
    ProjectDeanonymizer,
    StreamingDeanonymizer,
)
from llx.privacy.streaming import (
    StreamingProjectAnonymizer,
    ChunkedProcessor,
)


class TestAnonymizationContext:
    """Test AnonymizationContext symbol management."""

    def test_context_creation(self):
        """Should create context with project path."""
        ctx = AnonymizationContext(project_path="/tmp/test")
        assert ctx.project_path == Path("/tmp/test")
        assert ctx.salt is not None
        assert ctx.content_anonymizer is not None

    def test_get_or_create_symbol_consistency(self):
        """Same symbol should return same anonymized name."""
        ctx = AnonymizationContext(project_path="/tmp/test")
        
        anon1 = ctx.get_or_create_symbol("my_function", "function", "file.py", 10)
        anon2 = ctx.get_or_create_symbol("my_function", "function", "file.py", 10)
        
        assert anon1 == anon2
        assert anon1.startswith("fn_")

    def test_different_types_get_different_prefixes(self):
        """Different symbol types should get different prefixes."""
        ctx = AnonymizationContext(project_path="/tmp/test")
        
        var = ctx.get_or_create_symbol("x", "variable", "file.py")
        func = ctx.get_or_create_symbol("foo", "function", "file.py")
        cls = ctx.get_or_create_symbol("Bar", "class", "file.py")
        mod = ctx.get_or_create_symbol("baz", "module", "file.py")
        
        assert var.startswith("var_")
        assert func.startswith("fn_")
        assert cls.startswith("cls_")
        assert mod.startswith("mod_")

    def test_context_serialization(self):
        """Should serialize and deserialize context."""
        ctx = AnonymizationContext(project_path="/tmp/test")
        ctx.get_or_create_symbol("test_func", "function", "file.py", 1, "global")
        
        # Serialize
        data = ctx.to_dict()
        
        # Deserialize
        ctx2 = AnonymizationContext.from_dict(data)
        
        assert ctx2.project_path == ctx.project_path
        assert "test_func" in ctx2.functions
        assert ctx2.functions["test_func"].anonymized == ctx.functions["test_func"].anonymized

    def test_context_save_load(self, tmp_path):
        """Should save and load context from file."""
        ctx = AnonymizationContext(project_path="/tmp/test")
        ctx.get_or_create_symbol("my_var", "variable", "file.py", 5)
        
        save_path = tmp_path / "context.json"
        ctx.save(save_path)
        
        assert save_path.exists()
        
        loaded = AnonymizationContext.load(save_path)
        assert "my_var" in loaded.variables


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
        
        deanonymizer = ProjectDeanonymizer(ctx)
        result = deanonymizer.deanonymize_project_files(files)
        
        assert "process_data" in result.files["main.py"]
        assert "process_data" in result.files["utils.py"]
        assert result.overall_confidence == 1.0

    def test_get_symbol_info(self):
        """Should retrieve symbol information."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("my_function", "function", "file.py", 10, "global")
        
        deanonymizer = ProjectDeanonymizer(ctx)
        anon_name = ctx.functions["my_function"].anonymized
        
        info = deanonymizer.get_symbol_info(anon_name)
        
        assert info is not None
        assert info["original"] == "my_function"
        assert info["type"] == "function"
        assert info["file"] == "file.py"


class TestStreamingDeanonymizer:
    """Test streaming deanonymization."""

    def test_feed_chunk_basic(self):
        """Should process chunks and deanonymize."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("test_func", "function", "file.py", 1)
        
        streamer = StreamingDeanonymizer(ctx)
        anon_name = ctx.functions["test_func"].anonymized
        
        result = streamer.feed_chunk(f"Call {anon_name}")
        
        assert "test_func" in result
        assert anon_name not in result

    def test_streaming_finalize(self):
        """Should process remaining buffer on finalize."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("test_func", "function", "file.py", 1)
        
        streamer = StreamingDeanonymizer(ctx)
        anon_name = ctx.functions["test_func"].anonymized
        
        streamer.feed_chunk(f"Call {anon_name}")
        final = streamer.finalize()
        
        # Should include any remaining content
        assert "test_func" in final or final == ""

    def test_streaming_stats(self):
        """Should track streaming statistics."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("func1", "function", "file.py", 1)
        
        streamer = StreamingDeanonymizer(ctx)
        anon_name = ctx.functions["func1"].anonymized
        
        streamer.feed_chunk(f"Use {anon_name}")
        stats = streamer.get_stats()
        
        assert stats["total_restorations"] > 0


class TestChunkedProcessor:
    """Test chunked file processing."""

    def test_process_small_file_single_chunk(self, tmp_path):
        """Small files should be processed as single chunk."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("Small content")
        
        processor = ChunkedProcessor(max_chunk_size=1024)
        
        def anon(content: str) -> str:
            return content.upper()
        
        chunks = list(processor.process_file(test_file, anon))
        
        assert len(chunks) == 1
        assert chunks[0].is_complete
        assert "SMALL CONTENT" in chunks[0].content

    def test_process_large_file_multiple_chunks(self, tmp_path):
        """Large files should be split into chunks."""
        test_file = tmp_path / "large.txt"
        # Create content larger than chunk size
        test_file.write_text("Line\n" * 100)
        
        processor = ChunkedProcessor(max_chunk_size=50)  # 50 bytes
        
        def anon(content: str) -> str:
            return content
        
        chunks = list(processor.process_file(test_file, anon))
        
        assert len(chunks) > 1
        assert chunks[-1].is_complete


class TestStreamingProjectAnonymizer:
    """Test streaming project anonymization."""

    def test_streaming_anonymization_progress(self, tmp_path):
        """Should yield progress updates during anonymization."""
        # Create test files
        (tmp_path / "a.py").write_text("def func_a(): pass")
        (tmp_path / "b.py").write_text("def func_b(): pass")
        
        streamer = StreamingProjectAnonymizer(tmp_path)
        
        progress_updates = []
        for progress in streamer.anonymize_streaming(chunk_size=1):
            progress_updates.append(progress)
        
        assert len(progress_updates) > 0
        # Final progress should show all files processed
        final = progress_updates[-1]
        assert final.files_completed == 2

    def test_progress_callback_cancellation(self, tmp_path):
        """Should allow cancellation via callback."""
        (tmp_path / "a.py").write_text("def func_a(): pass")
        (tmp_path / "b.py").write_text("def func_b(): pass")
        
        streamer = StreamingProjectAnonymizer(tmp_path)
        
        def cancel_callback(progress):
            return False  # Cancel immediately
        
        updates = list(streamer.anonymize_streaming(
            chunk_size=1,
            progress_callback=cancel_callback
        ))
        
        # Should stop early due to cancellation
        assert len(updates) <= 1


class TestIntegration:
    """Integration tests for full anonymization/deanonymization roundtrip."""

    def test_full_roundtrip_python_code(self, tmp_path):
        """Full roundtrip: anonymize then deanonymize Python code."""
        original_code = """
def process_payment(user_id, amount):
    customer = get_customer(user_id)
    return charge(customer, amount)

class PaymentProcessor:
    def handle(self, request):
        return process_payment(request.user, request.amount)
"""
        test_file = tmp_path / "payment.py"
        test_file.write_text(original_code)
        
        # Anonymize
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        anon_result = anonymizer.anonymize_file(test_file)
        
        # Verify anonymization happened
        assert "process_payment" not in anon_result or "PaymentProcessor" not in anon_result
        
        # Deanonymize
        deanonymizer = ProjectDeanonymizer(ctx)
        deanon_result = deanonymizer.deanonymize_file(anon_result, str(test_file))
        
        # Verify restoration
        assert "process_payment" in deanon_result.text
        assert "PaymentProcessor" in deanon_result.text
        assert deanon_result.confidence == 1.0

    def test_context_persistence_roundtrip(self, tmp_path):
        """Should persist and restore context for later deanonymization."""
        # Anonymize phase
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "code.py").write_text("def secret_function(): pass")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        anonymizer.anonymize_project(include_patterns=["*.py"])
        
        # Save context
        context_path = tmp_path / "context.json"
        ctx.save(context_path)
        
        # Later... load context and deanonymize
        loaded_ctx = AnonymizationContext.load(context_path)
        deanonymizer = ProjectDeanonymizer(loaded_ctx)
        
        anon_name = loaded_ctx.functions["secret_function"].anonymized
        result = deanonymizer.deanonymize_text(f"Fix {anon_name}")
        
        assert "secret_function" in result.text

    def test_mixed_content_anonymization(self, tmp_path):
        """Should handle code and sensitive data together."""
        mixed_content = '''
def send_email(to_address):
    api_key = "sk-abcdefghijklmnopqrstuv"
    return post("https://api.example.com", 
                auth=api_key, 
                to=to_address)
'''
        test_file = tmp_path / "mixed.py"
        test_file.write_text(mixed_content)
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_file(test_file)
        
        # Both code symbols and sensitive data should be anonymized
        assert "sk-abcdefghijklmnopqrstuv" not in result
        assert "[APIKEY_" in result


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_empty_project(self, tmp_path):
        """Should handle empty project directory."""
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_project(include_patterns=["*.py"])
        
        assert len(result.files) == 0
        assert len(result.errors) == 0

    def test_syntax_error_file(self, tmp_path):
        """Should handle Python files with syntax errors."""
        test_file = tmp_path / "broken.py"
        test_file.write_text("def foo(:\n  pass")  # Invalid syntax
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        # Should fall back to generic anonymization
        result = anonymizer.anonymize_file(test_file)
        
        # Should not crash, should return content
        assert isinstance(result, str)

    def test_unicode_content(self, tmp_path):
        """Should handle unicode content correctly."""
        test_file = tmp_path / "unicode.py"
        test_file.write_text('# -*- coding: utf-8 -*-\ndef 日本語(): pass', encoding="utf-8")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        # Should not crash
        result = anonymizer.anonymize_file(test_file)
        assert isinstance(result, str)

    def test_binary_file_handling(self, tmp_path):
        """Should gracefully skip binary files."""
        test_file = tmp_path / "binary.dat"
        test_file.write_bytes(b"\x00\x01\x02\x03")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        # Should handle binary content without crashing
        result = anonymizer.anonymize_file(test_file)
        assert isinstance(result, str)  # Converts to str with errors="replace"

    def test_very_long_symbol_names(self):
        """Should handle very long symbol names."""
        ctx = AnonymizationContext(project_path="/tmp")
        long_name = "a" * 200
        
        anon = ctx.get_or_create_symbol(long_name, "function", "file.py", 1)
        
        assert anon.startswith("fn_")
        # Should be truncated or hashed
        assert len(anon) < 100
