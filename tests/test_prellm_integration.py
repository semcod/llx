"""Tests for preLLM integration into llx.

Validates that preLLM modules are importable, functional,
and properly wired into the llx package.
"""

import pytest
from pathlib import Path


class TestPreLLMImports:
    """Verify all preLLM public symbols are importable from llx.prellm."""

    def test_top_level_import(self):
        import llx.prellm
        assert hasattr(llx.prellm, "__version__")
        assert hasattr(llx.prellm, "__all__")
        assert len(llx.prellm.__all__) >= 40

    def test_core_imports(self):
        from llx.prellm.core import preprocess_and_execute, PreLLM
        assert callable(preprocess_and_execute)

    def test_models_imports(self):
        from llx.prellm.models import (
            PreLLMResponse, DecompositionStrategy, LLMProviderConfig,
            ShellContext, ContextSchema, FilterReport,
        )
        assert DecompositionStrategy.CLASSIFY.value == "classify"

    def test_pipeline_imports(self):
        from llx.prellm.pipeline import PromptPipeline, PipelineConfig, PipelineResult

    def test_agents_imports(self):
        from llx.prellm.agents import PreprocessorAgent, ExecutorAgent

    def test_context_imports(self):
        from llx.prellm.context import (
            UserMemory, CodebaseIndexer, ShellContextCollector,
            SensitiveDataFilter, FolderCompressor, ContextSchemaGenerator,
        )

    def test_utils_imports(self):
        from llx.prellm.utils import LazyLoader, lazy_import_global


class TestPreLLMFunctional:
    """Functional tests for preLLM components (no LLM calls)."""

    def test_sensitive_filter_masks_keys(self):
        from llx.prellm.context.sensitive_filter import SensitiveDataFilter
        sf = SensitiveDataFilter()
        data = {"OPENAI_API_KEY": "sk-abc123", "USER": "tom"}
        filtered = sf.filter_dict(data)
        assert "OPENAI_API_KEY" not in filtered or filtered.get("OPENAI_API_KEY") != "sk-abc123"
        assert filtered.get("USER") == "tom"

    def test_shell_collector_gathers_context(self):
        from llx.prellm.context.shell_collector import ShellContextCollector
        ctx = ShellContextCollector().collect_all()
        assert ctx.process.pid > 0
        assert len(ctx.env_vars) > 0

    def test_budget_tracker_enforces_limit(self, tmp_path):
        from llx.prellm.budget import BudgetTracker, BudgetExceededError
        bt = BudgetTracker(monthly_limit=0.001, persist_path=tmp_path / "budget.json")
        bt.record(model="test", cost=0.002)
        with pytest.raises(BudgetExceededError):
            bt.check(model="test")

    def test_decomposition_strategy_enum(self):
        from llx.prellm.models import DecompositionStrategy
        assert DecompositionStrategy.AUTO.value == "auto"
        assert DecompositionStrategy.CLASSIFY.value == "classify"
        assert DecompositionStrategy.STRUCTURE.value == "structure"
        assert DecompositionStrategy.SPLIT.value == "split"
        assert DecompositionStrategy.ENRICH.value == "enrich"
        assert DecompositionStrategy.PASSTHROUGH.value == "passthrough"

    def test_prellm_response_creation(self):
        from llx.prellm.models import PreLLMResponse
        resp = PreLLMResponse(
            content="test output",
            model_used="gpt-4o-mini",
            small_model_used="ollama/qwen2.5:3b",
        )
        assert resp.content == "test output"
        assert resp.model_used == "gpt-4o-mini"
        assert resp.retries == 0

    def test_llm_provider_config_defaults(self):
        from llx.prellm.models import LLMProviderConfig
        cfg = LLMProviderConfig(model="ollama/qwen2.5:3b")
        assert cfg.max_tokens == 2048
        assert cfg.temperature == 0.0
        assert cfg.max_retries == 3

    def test_env_config_loads(self):
        from llx.prellm.env_config import get_env_config
        cfg = get_env_config()
        assert cfg.small_model is not None
        assert cfg.large_model is not None

    def test_model_catalog(self):
        from llx.prellm.model_catalog import list_model_pairs
        pairs = list_model_pairs()
        assert len(pairs) > 0

    def test_trace_recorder_lifecycle(self):
        from llx.prellm.trace import TraceRecorder
        trace = TraceRecorder()
        trace.start(query="test_pipeline")
        trace.step("step1", step_type="classify", inputs={"query": "test"})
        trace.set_result(intent="deploy")
        trace.stop()
        md = trace.to_markdown()
        assert "test_pipeline" in md
        assert "step1" in md


class TestPreLLMConfigPaths:
    """Verify config files are accessible at expected paths."""

    def test_configs_directory_exists(self):
        configs_dir = Path(__file__).parent.parent / "llx" / "configs"
        assert configs_dir.exists(), f"configs dir not found at {configs_dir}"

    def test_pipelines_yaml_exists(self):
        path = Path(__file__).parent.parent / "llx" / "configs" / "pipelines.yaml"
        assert path.exists()

    def test_prompts_yaml_exists(self):
        path = Path(__file__).parent.parent / "llx" / "configs" / "prompts.yaml"
        assert path.exists()

    def test_response_schemas_yaml_exists(self):
        path = Path(__file__).parent.parent / "llx" / "configs" / "response_schemas.yaml"
        assert path.exists()

    def test_sensitive_rules_yaml_exists(self):
        path = Path(__file__).parent.parent / "llx" / "configs" / "sensitive_rules.yaml"
        assert path.exists()
