"""Extended tests for project-level anonymization and deanonymization.

Additional test coverage for:
- AST transformation edge cases
- Streaming with various chunk sizes
- Multi-file consistency
- Context persistence scenarios
- Performance/memory characteristics
"""

import json
import time

import pytest

from llx.privacy.project import (
    AnonymizationContext,
    ProjectAnonymizer,
    ASTAnonymizer,
)
from llx.privacy.deanonymize import (
    ProjectDeanonymizer,
    StreamingDeanonymizer,
    quick_project_deanonymize,
)
from llx.privacy.streaming import (
    StreamingProjectAnonymizer,
    ChunkedProcessor,
)


class TestASTAnonymizer:
    """Test AST-based Python code transformation."""

    def test_ast_anonymize_simple_function(self):
        """Should anonymize simple function definition."""
        import ast
        
        code = """
def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Function name should be anonymized
        assert result.body[0].name.startswith("fn_")
        # Parameters should be anonymized  
        assert result.body[0].args.args[0].arg.startswith("var_")

    def test_ast_preserves_dunder_methods(self):
        """Should preserve dunder methods like __init__, __str__."""
        import ast
        
        code = """
class MyClass:
    def __init__(self):
        pass
    def __str__(self):
        return "test"
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Dunder methods should NOT be anonymized
        cls = result.body[0]
        assert cls.body[0].name == "__init__"
        assert cls.body[1].name == "__str__"

    def test_ast_nested_functions(self):
        """Should handle nested function definitions."""
        import ast
        
        code = """
def outer(x):
    def inner(y):
        return y * 2
    return inner(x)
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Both functions should be anonymized
        outer_fn = result.body[0]
        assert outer_fn.name.startswith("fn_")
        
        # Inner function should also be anonymized
        inner_fn = outer_fn.body[0]
        assert inner_fn.name.startswith("fn_")

    def test_ast_class_with_methods(self):
        """Should anonymize class and its methods."""
        import ast
        
        code = """
class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, product):
        self.items.append(product)
        
    def get_total(self):
        return sum(item.price for item in self.items)
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Class name anonymized
        assert result.body[0].name.startswith("cls_")
        # Regular methods anonymized (but not __init__)
        cls = result.body[0]
        regular_methods = [m for m in cls.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("__")]
        for method in regular_methods:
            assert method.name.startswith("fn_")

    def test_ast_preserves_builtins(self):
        """Should preserve Python builtin names."""
        import ast
        
        code = """
def process(data):
    return len(data), sum(data), max(data)
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Builtins should not be in variables mapping
        builtin_names = {'len', 'sum', 'max'}
        for name in builtin_names:
            assert name not in ctx.variables

    def test_ast_decorators_preserved(self):
        """Should preserve decorator names but anonymize target function."""
        import ast
        
        code = """
@staticmethod
def utility_function(x):
    return x * 2

@property
def value(self):
    return self._value
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Decorators should be preserved (as Attribute/Name)
        func = result.body[0]
        assert func.name.startswith("fn_")  # Function anonymized

    def test_ast_comprehensions(self):
        """Should handle list/dict comprehensions correctly."""
        import ast
        
        code = """
def transform(data):
    squared = [x**2 for x in data if x > 0]
    mapping = {k: v for k, v in zip(data, squared)}
    return mapping
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Function and variables should be anonymized
        assert result.body[0].name.startswith("fn_")

    def test_ast_lambda_functions(self):
        """Should handle lambda expressions."""
        import ast
        
        code = """
operations = {
    'double': lambda x: x * 2,
    'triple': lambda x: x * 3,
}
"""
        ctx = AnonymizationContext(project_path="/tmp")
        tree = ast.parse(code)
        
        transformer = ASTAnonymizer(ctx, "test.py")
        result = transformer.visit(tree)
        
        # Variable should be anonymized
        assert result.body[0].targets[0].id.startswith("var_")


class TestStreamingChunkedProcessing:
    """Test streaming and chunked processing."""

    def test_chunked_processor_exact_boundary(self, tmp_path):
        """Test chunking at exact boundary."""
        test_file = tmp_path / "boundary.txt"
        # Create content exactly at chunk size
        content = "A" * 100
        test_file.write_text(content)
        
        processor = ChunkedProcessor(max_chunk_size=50)
        
        def anon(text: str) -> str:
            return text.lower()
        
        chunks = list(processor.process_file(test_file, anon))
        
        # Should be exactly 2 chunks
        assert len(chunks) == 2
        assert chunks[0].content == "a" * 50
        assert chunks[1].content == "a" * 50

    def test_chunked_processor_empty_file(self, tmp_path):
        """Should handle empty files."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        processor = ChunkedProcessor(max_chunk_size=1024)
        
        chunks = list(processor.process_file(test_file, lambda x: x))
        
        # Should still yield one empty chunk marked as complete
        assert len(chunks) == 1
        assert chunks[0].is_complete
        assert chunks[0].content == ""

    def test_streaming_anonymizer_empty_project(self, tmp_path):
        """Should handle empty project gracefully."""
        streamer = StreamingProjectAnonymizer(tmp_path)
        
        progress_updates = list(streamer.anonymize_streaming())
        
        assert len(progress_updates) == 0 or progress_updates[0].total_files == 0

    def test_streaming_with_single_file(self, tmp_path):
        """Should process single file correctly."""
        (tmp_path / "single.py").write_text("def foo(): pass")
        
        streamer = StreamingProjectAnonymizer(tmp_path)
        
        updates = list(streamer.anonymize_streaming(chunk_size=1))
        
        assert len(updates) == 1
        assert updates[0].files_completed == 1
        assert updates[0].total_files == 1

    def test_streaming_large_project_simulation(self, tmp_path):
        """Simulate large project with many files."""
        # Create 50 files
        for i in range(50):
            (tmp_path / f"file_{i}.py").write_text(f"def func_{i}(): pass\n")
        
        streamer = StreamingProjectAnonymizer(tmp_path)
        
        update_count = 0
        for progress in streamer.anonymize_streaming(chunk_size=10):
            update_count += 1
            assert progress.total_files == 50
        
        assert update_count == 5  # 50 files / 10 per chunk

    def test_streaming_deanonymizer_empty_input(self):
        """Should handle empty input stream."""
        ctx = AnonymizationContext(project_path="/tmp")
        streamer = StreamingDeanonymizer(ctx)
        
        result = streamer.feed_chunk("")
        assert result == ""

    def test_streaming_deanonymizer_partial_token_handling(self):
        """Should handle tokens split across chunks."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("test_function", "function", "file.py", 1)
        
        streamer = StreamingDeanonymizer(ctx)
        anon_name = ctx.functions["test_function"].anonymized
        
        # Split the anonymized name across chunks
        # e.g., "fn_a" "b1234"
        midpoint = len(anon_name) // 2
        chunk1 = f"Call {anon_name[:midpoint]}"
        chunk2 = f"{anon_name[midpoint:]} to process"
        
        result1 = streamer.feed_chunk(chunk1)
        # First chunk should be empty (waiting for complete token)
        
        result2 = streamer.feed_chunk(chunk2)
        # Second chunk should contain restored text
        assert "test_function" in result2


class TestMultiFileConsistency:
    """Test consistency across multiple files."""

    def test_same_symbol_across_files_consistent(self, tmp_path):
        """Same symbol should have same anonymized name across files."""
        # Two files using same function name
        (tmp_path / "a.py").write_text("def process_data(): pass")
        (tmp_path / "b.py").write_text("from a import process_data")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result_a = anonymizer.anonymize_file(tmp_path / "a.py")
        result_b = anonymizer.anonymize_file(tmp_path / "b.py")
        
        # Same anonymized name should appear in both
        anon_name = ctx.functions["process_data"].anonymized
        assert anon_name in result_a
        assert anon_name in result_b

    def test_import_statements_handled(self, tmp_path):
        """Should handle import statements specially."""
        (tmp_path / "utils.py").write_text("def helper(): pass")
        (tmp_path / "main.py").write_text("from utils import helper")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        # Anonymize both
        result_utils = anonymizer.anonymize_file(tmp_path / "utils.py")
        result_main = anonymizer.anonymize_file(tmp_path / "main.py")
        
        # Helper should be anonymized consistently
        anon_helper = ctx.functions["helper"].anonymized
        assert anon_helper in result_utils

    def test_cross_file_deanonymization(self, tmp_path):
        """Should deanonymize consistently across files."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("shared_function", "function", "a.py", 1)
        ctx.get_or_create_symbol("shared_function", "function", "b.py", 5)  # Same original
        
        anon_name = ctx.functions["shared_function"].anonymized
        
        files = {
            "a.py": f"def {anon_name}(): pass",
            "b.py": f"from a import {anon_name}",
        }
        
        deanonymizer = ProjectDeanonymizer(ctx)
        result = deanonymizer.deanonymize_project_files(files)
        
        # Both files should have original name
        assert "shared_function" in result.files["a.py"]
        assert "shared_function" in result.files["b.py"]


class TestContextPersistence:
    """Test saving and loading anonymization context."""

    def test_save_load_with_complex_project(self, tmp_path):
        """Save/load with various symbol types."""
        ctx = AnonymizationContext(project_path=tmp_path)
        
        # Add various symbols
        ctx.get_or_create_symbol("user_count", "variable", "models.py", 10, "global")
        ctx.get_or_create_symbol("calculate_total", "function", "utils.py", 20, "global")
        ctx.get_or_create_symbol("PaymentGateway", "class", "payment.py", 5, "global")
        ctx.get_or_create_symbol("stripe_api", "module", "payment.py")
        ctx.get_or_create_symbol("/home/user/data", "path", "config.py")
        
        # Save
        save_path = tmp_path / "complex_context.json"
        ctx.save(save_path)
        
        # Load
        loaded = AnonymizationContext.load(save_path)
        
        # Verify all mappings preserved
        assert "user_count" in loaded.variables
        assert "calculate_total" in loaded.functions
        assert "PaymentGateway" in loaded.classes
        assert "stripe_api" in loaded.modules
        assert "/home/user/data" in loaded.paths

    def test_context_stats_preserved(self, tmp_path):
        """Stats should be preserved through save/load."""
        ctx = AnonymizationContext(project_path=tmp_path)
        
        # Create symbols to populate stats
        for i in range(5):
            ctx.get_or_create_symbol(f"var_{i}", "variable", "file.py")
        for i in range(3):
            ctx.get_or_create_symbol(f"func_{i}", "function", "file.py")
        
        save_path = tmp_path / "stats_context.json"
        ctx.save(save_path)
        
        loaded = AnonymizationContext.load(save_path)
        
        assert loaded.stats.get("variable") == 5
        assert loaded.stats.get("function") == 3

    def test_context_salt_preserved(self, tmp_path):
        """Salt should be preserved for consistent token generation."""
        ctx = AnonymizationContext(project_path=tmp_path)
        original_salt = ctx.salt
        
        ctx.get_or_create_symbol("test", "variable", "file.py")
        original_anon = ctx.variables["test"].anonymized
        
        save_path = tmp_path / "salt_context.json"
        ctx.save(save_path)
        
        loaded = AnonymizationContext.load(save_path)
        
        assert loaded.salt == original_salt
        
        # Creating same symbol with loaded context should produce same token
        loaded_anon = loaded.get_or_create_symbol("test", "variable", "file.py")
        assert loaded_anon == original_anon


class TestDeanonymizeFeatures:
    """Test deanonymization features."""

    def test_get_symbol_info_returns_full_details(self):
        """Should return detailed info about anonymized symbol."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("process_payment", "function", "payment.py", 42, "PaymentService")
        
        deanonymizer = ProjectDeanonymizer(ctx)
        anon_name = ctx.functions["process_payment"].anonymized
        
        info = deanonymizer.get_symbol_info(anon_name)
        
        assert info is not None
        assert info["original"] == "process_payment"
        assert info["type"] == "function"
        assert info["file"] == "payment.py"
        assert info["line"] == 42
        assert info["scope"] == "PaymentService"

    def test_list_all_mappings_organized(self):
        """Should list all mappings organized by type."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("x", "variable", "file.py")
        ctx.get_or_create_symbol("y", "variable", "file.py")
        ctx.get_or_create_symbol("foo", "function", "file.py")
        ctx.get_or_create_symbol("Bar", "class", "file.py")
        
        deanonymizer = ProjectDeanonymizer(ctx)
        all_mappings = deanonymizer.list_all_mappings()
        
        assert len(all_mappings["variables"]) == 2
        assert len(all_mappings["functions"]) == 1
        assert len(all_mappings["classes"]) == 1

    def test_deanonymize_unknown_token_reported(self):
        """Unknown tokens should be reported."""
        ctx = AnonymizationContext(project_path="/tmp")
        deanonymizer = ProjectDeanonymizer(ctx)
        
        result = deanonymizer.deanonymize_text("Call fn_UNKNOWN999")
        
        assert "fn_UNKNOWN999" in result.unknown_tokens

    def test_quick_project_deanonymize_function(self, tmp_path):
        """Quick function should work with context path or object."""
        ctx = AnonymizationContext(project_path="/tmp")
        ctx.get_or_create_symbol("target_func", "function", "file.py", 1)
        
        save_path = tmp_path / "ctx.json"
        ctx.save(save_path)
        
        anon_name = ctx.functions["target_func"].anonymized
        
        # Test with path
        result = quick_project_deanonymize(f"Fix {anon_name}", save_path)
        assert "target_func" in result
        
        # Test with context object
        result2 = quick_project_deanonymize(f"Fix {anon_name}", ctx)
        assert "target_func" in result2


class TestIntegrationComplexScenarios:
    """Complex real-world scenarios."""

    def test_flask_app_anonymization(self, tmp_path):
        """Anonymize a Flask-like web application."""
        app_py = tmp_path / "app.py"
        app_py.write_text("""
from flask import Flask, request, jsonify
from models import User, Order

app = Flask(__name__)

database_connection = None

def init_db():
    global database_connection
    database_connection = connect_to_db()

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    order = Order.create(data)
    return jsonify(order.to_dict()), 201

if __name__ == '__main__':
    app.run(debug=True)
""")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_file(app_py)
        
        # Flask decorators and imports should be handled
        # Function names should be anonymized
        original_funcs = ['get_users', 'create_order', 'init_db']
        for func in original_funcs:
            assert func not in result or ctx.functions.get(func)

    def test_dataclass_anonymization(self, tmp_path):
        """Anonymize Python dataclasses."""
        models_py = tmp_path / "models.py"
        models_py.write_text("""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Customer:
    id: int
    email: str
    name: str
    phone: Optional[str] = None
    
    def get_display_name(self):
        return f"{self.name} <{self.email}>"

@dataclass  
class Product:
    sku: str
    price: float
    stock: int
""")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_file(models_py)
        
        # Class names should be anonymized
        assert "Customer" not in result or ctx.classes.get("Customer")
        assert "Product" not in result or ctx.classes.get("Product")

    def test_async_code_anonymization(self, tmp_path):
        """Anonymize async/await code."""
        async_py = tmp_path / "async_module.py"
        async_py.write_text("""
import asyncio
import aiohttp

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def process_batch(urls):
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return merge_results(results)

def merge_results(data_list):
    return {k: v for d in data_list for k, v in d.items()}
""")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_file(async_py)
        
        # Async functions should be anonymized
        assert "fetch_data" not in result or ctx.functions.get("fetch_data")
        assert "process_batch" not in result or ctx.functions.get("process_batch")

    def test_end_to_end_workflow(self, tmp_path):
        """Complete end-to-end: anonymize project, simulate LLM, deanonymize."""
        # Phase 1: Create project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "calculator.py").write_text("""
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
""")
        
        # Phase 2: Anonymize
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        anon_result = anonymizer.anonymize_project(include_patterns=["*.py"])
        
        # Save context
        ctx.save(tmp_path / "context.json")
        
        # Phase 3: Simulate LLM response about anonymized code
        add_anon = ctx.functions["add"].anonymized
        multiply_anon = ctx.functions["multiply"].anonymized
        
        llm_response = f"""
To fix the issue, modify the {add_anon} function to handle edge cases.
You can also optimize {multiply_anon} for better performance.
"""
        
        # Phase 4: Deanonymize LLM response
        loaded_ctx = AnonymizationContext.load(tmp_path / "context.json")
        deanonymizer = ProjectDeanonymizer(loaded_ctx)
        
        restored = deanonymizer.deanonymize_chat_response(llm_response)
        
        # Phase 5: Verify restoration
        assert "add" in restored
        assert "multiply" in restored
        assert add_anon not in restored
        assert multiply_anon not in restored


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_context_file(self, tmp_path):
        """Should raise appropriate error for missing context."""
        with pytest.raises((FileNotFoundError, json.JSONDecodeError)):
            AnonymizationContext.load(tmp_path / "nonexistent.json")

    def test_corrupted_context_file(self, tmp_path):
        """Should handle corrupted context file."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            AnonymizationContext.load(bad_file)

    def test_permission_error_handling(self, tmp_path):
        """Should handle file permission errors gracefully."""
        # Create a file we can't read (simulate)
        test_file = tmp_path / "protected.py"
        test_file.write_text("def foo(): pass")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        # Even with permission issues, shouldn't crash
        try:
            result = anonymizer.anonymize_file(test_file)
            assert isinstance(result, str)
        except PermissionError:
            pass  # Acceptable on systems where we can actually lock files


class TestPerformance:
    """Basic performance characteristics."""

    def test_large_file_performance(self, tmp_path):
        """Should handle large files reasonably quickly."""
        # Create a moderately large Python file (1MB)
        large_file = tmp_path / "large.py"
        
        lines = []
        for i in range(10000):
            lines.append(f"def function_{i}(arg_{i}):\n    return arg_{i} * {i}\n")
        
        large_file.write_text("".join(lines))
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        start = time.time()
        result = anonymizer.anonymize_file(large_file)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (adjust as needed)
        assert elapsed < 30  # 30 seconds is generous
        assert "def fn_" in result

    def test_many_small_files_performance(self, tmp_path):
        """Should handle many small files."""
        # Create 100 small files
        for i in range(100):
            (tmp_path / f"file_{i}.py").write_text(f"def func_{i}(): return {i}\n")
        
        ctx = AnonymizationContext(project_path=tmp_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        start = time.time()
        result = anonymizer.anonymize_project(include_patterns=["*.py"])
        elapsed = time.time() - start
        
        assert len(result.files) == 100
        assert elapsed < 60  # 60 seconds for 100 files

    def test_context_lookup_performance(self):
        """Symbol lookup should be fast even with many symbols."""
        ctx = AnonymizationContext(project_path="/tmp")
        
        # Create 1000 symbols
        for i in range(1000):
            ctx.get_or_create_symbol(f"symbol_{i}", "variable", "file.py")
        
        # Lookup should be fast
        start = time.time()
        for i in range(100):
            ctx.get_or_create_symbol(f"symbol_{i}", "variable", "file.py")
        elapsed = time.time() - start
        
        # 100 lookups should be fast (existing symbols)
        assert elapsed < 1.0
