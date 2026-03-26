"""preLLM — Small LLM preprocessing before large LLM execution. One function, like litellm.completion().

Usage:
    from llx.prellm import preprocess_and_execute

    result = await preprocess_and_execute(
        query="Deploy app to production",
        small_llm="ollama/qwen2.5:3b",
        large_llm="gpt-4o-mini",
    )
    print(result.content)
"""

__version__ = "0.1.32"

# 1-function API — the primary interface (always uses v0.3 pipeline internally)
from llx.prellm.core import preprocess_and_execute, preprocess_and_execute_sync

# Backward-compatible alias
from llx.prellm.core import preprocess_and_execute_v3
from llx.prellm.agents.preprocessor import PreprocessorAgent, PreprocessResult
from llx.prellm.agents.executor import ExecutorAgent, ExecutorResult
from llx.prellm.pipeline import PromptPipeline, PipelineConfig, PipelineStep, PipelineResult
from llx.prellm.prompt_registry import PromptRegistry
from llx.prellm.validators import ResponseValidator

# Class-based architecture
from llx.prellm.core import PreLLM
from llx.prellm.llm_provider import LLMProvider
from llx.prellm.query_decomposer import QueryDecomposer
from llx.prellm.models import (
    CompressedFolder,
    ContextSchema,
    DecompositionStrategy,
    DecompositionResult,
    DomainRule,
    FilterReport,
    LLMProviderConfig,
    PreLLMConfig,
    PreLLMResponse,
    RuntimeContext,
    SessionSnapshot,
    SensitivityLevel,
    ShellContext,
)

# Components
from llx.prellm.analyzers.context_engine import ContextEngine
from llx.prellm.context.user_memory import UserMemory
from llx.prellm.context.sensitive_filter import SensitiveDataFilter
from llx.prellm.context.shell_collector import ShellContextCollector
from llx.prellm.context.folder_compressor import FolderCompressor
from llx.prellm.context.schema_generator import ContextSchemaGenerator

# ProcessChain - lazy loaded to avoid circular dependency
def _get_process_chain():
    from llx.prellm.chains.process_chain import ProcessChain
    return ProcessChain

# Logging
from llx.prellm.logging_setup import setup_logging, get_logger

# Trace
from llx.prellm.trace import TraceRecorder, get_current_trace

# Budget
from llx.prellm.budget import BudgetTracker, BudgetExceededError, get_budget_tracker

__all__ = [
    # 1-function API (primary)
    "preprocess_and_execute",
    "preprocess_and_execute_sync",
    "preprocess_and_execute_v3",
    # Agents
    "PreprocessorAgent",
    "PreprocessResult",
    "ExecutorAgent",
    "ExecutorResult",
    # Pipeline
    "PromptPipeline",
    "PipelineConfig",
    "PipelineStep",
    "PipelineResult",
    "PromptRegistry",
    "ResponseValidator",
    # Class-based
    "PreLLM",
    "LLMProvider",
    "QueryDecomposer",
    # Models
    "CompressedFolder",
    "ContextSchema",
    "DecompositionStrategy",
    "DecompositionResult",
    "DomainRule",
    "FilterReport",
    "LLMProviderConfig",
    "PreLLMConfig",
    "PreLLMResponse",
    "RuntimeContext",
    "SessionSnapshot",
    "SensitivityLevel",
    "ShellContext",
    # Components
    "ContextEngine",
    "UserMemory",
    "SensitiveDataFilter",
    "ShellContextCollector",
    "FolderCompressor",
    "ContextSchemaGenerator",
    # Logging
    "setup_logging",
    "get_logger",
    # Trace
    "TraceRecorder",
    "get_current_trace",
    # Budget
    "BudgetTracker",
    "BudgetExceededError",
    "get_budget_tracker",
]
