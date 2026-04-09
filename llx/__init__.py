"""llx — Intelligent LLM model router driven by real code metrics.

Successor to preLLM. Integrates code2llm (analysis), redup (duplication),
vallm (validation) with LiteLLM for metric-aware model selection.

Key difference from preLLM: modular architecture (no god modules),
metric-driven routing instead of hardcoded model selection,
and clean separation of analysis/routing/client layers.

Usage:
    from llx import analyze_project, select_model, LlxConfig

    metrics = analyze_project("./my-repo")
    model = select_model(metrics)
"""

__version__ = "0.1.56"

from llx.analysis.collector import ProjectMetrics, analyze_project
from llx.llm import DEFAULT_MAX_TOKENS, LLM, LLMResponse, get_api_key, get_llm, get_llm_model
from llx.routing.selector import ModelTier, select_model
from llx.config import LlxConfig

__all__ = [
    "analyze_project",
    "select_model",
    "ProjectMetrics",
    "ModelTier",
    "LlxConfig",
    "DEFAULT_MAX_TOKENS",
    "LLM",
    "LLMResponse",
    "get_api_key",
    "get_llm",
    "get_llm_model",
]
