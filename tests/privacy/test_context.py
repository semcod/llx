import pytest
from pathlib import Path
from llx.privacy.project import AnonymizationContext

class TestAnonymizationContext:
    def test_context_creation(self):
        ctx = AnonymizationContext(project_path="/tmp/test")
        assert ctx.project_path == Path("/tmp/test")
        assert ctx.salt is not None
        assert ctx.content_anonymizer is not None

    def test_get_or_create_symbol_consistency(self):
        ctx = AnonymizationContext(project_path="/tmp/test")
        anon1 = ctx.get_or_create_symbol("my_function", "function", "file.py", 10)
        anon2 = ctx.get_or_create_symbol("my_function", "function", "file.py", 10)
        assert anon1 == anon2
        assert anon1.startswith("fn_")

    def test_different_types_get_different_prefixes(self):
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
        ctx = AnonymizationContext(project_path="/tmp/test")
        ctx.get_or_create_symbol("test_func", "function", "file.py", 1, "global")
        data = ctx.to_dict()
        ctx2 = AnonymizationContext.from_dict(data)
        assert ctx2.project_path == ctx.project_path
        assert "test_func" in ctx2.functions
        assert ctx2.functions["test_func"].anonymized == ctx.functions["test_func"].anonymized

    def test_context_save_load(self, tmp_path):
        ctx = AnonymizationContext(project_path="/tmp/test")
        ctx.get_or_create_symbol("my_var", "variable", "file.py", 5)
        save_path = tmp_path / "context.json"
        ctx.save(save_path)
        assert save_path.exists()
        loaded = AnonymizationContext.load(save_path)
        assert "my_var" in loaded.variables