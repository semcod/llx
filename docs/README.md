<!-- code2docs:start --># llx

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-1373-green)
> **1373** functions | **226** classes | **214** files | CC̄ = 3.8

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/llx](https://github.com/semcod/llx)

## Installation

### From PyPI

```bash
pip install llx
```

### From Source

```bash
git clone https://github.com/semcod/llx
cd llx
pip install -e .
```

### Optional Extras

```bash
pip install llx[mcp]    # mcp features
pip install llx[litellm]    # litellm features
pip install llx[code2llm]    # code2llm features
pip install llx[redup]    # redup features
pip install llx[vallm]    # vallm features
pip install llx[ollama]    # ollama features
pip install llx[prellm]    # prellm features
pip install llx[prellm-full]    # prellm-full features
pip install llx[all]    # all optional features
pip install llx[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
llx ./my-project

# Only regenerate README
llx ./my-project --readme-only

# Preview what would be generated (no file writes)
llx ./my-project --dry-run

# Check documentation health
llx check ./my-project

# Sync — regenerate only changed modules
llx sync ./my-project
```

### Python API

```python
from llx import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `llx`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `llx.yaml` in your project root (or run `llx init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

llx can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- llx:start -->
# Project Title
... auto-generated content ...
<!-- llx:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
llx/
├── docker-manage├── generate├── project├── ai-tools-manage├── my-api/    ├── monitoring├── trace    ├── cleanup    ├── run    ├── pyqual-llx-demo├── simple_generate            ├── 01_entropy_ml_detection            ├── 04_behavioral_learning            ├── 03_contextual_passwords            ├── 02_hybrid_system            ├── 01_streaming_anonymization            ├── 02_deanonymize_project            ├── 01_anonymize_project            ├── 03_cicd_integration            ├── 02_multi_stage            ├── 01_text_anonymization            ├── 02_custom_patterns        ├── run        ├── run        ├── run        ├── run        ├── docker        ├── run        ├── run        ├── generate_simple        ├── run        ├── run        ├── run        ├── run        ├── filtering            ├── 01_api_integration        ├── run        ├── setup-aliases        ├── run        ├── run        ├── run        ├── hybrid        ├── run        ├── entrypoint        ├── install-extensions        ├── entrypoint        ├── install-tools    ├── pyqual_auto    ├── config    ├── llm├── llx/    ├── __main__        ├── _patch_apply    ├── commands/        ├── fix        ├── deanonymize_results    ├── litellm_config        ├── streaming        ├── project    ├── privacy/        ├── _streaming_impl        ├── _project_ast        ├── _project_anonymizer        ├── deanonymize        ├── deanonymize_engine        ├── _project_context        ├── _streaming_chunking        ├── deanonymize_utils        ├── type_check        ├── detect_secrets    ├── pyqual_plugins/        ├── bump_version        ├── publish        ├── lint        ├── verify_push_publish        ├── security_audit        ├── utils        ├── env_config        ├── cli_config        ├── cli        ├── trace        ├── __core        ├── cli_context        ├── model_catalog    ├── models    ├── main    ├── prellm/        ├── server        ├── context_ops        ├── pipeline_ops        ├── query_decomposer        ├── cli_query        ├── prompt_registry        ├── validators        ├── core        ├── models        ├── llm_provider        ├── cli_commands        ├── pipeline/        ├── _nfo_compat        ├── chains/            ├── process_chain        ├── utils/            ├── lazy_imports            ├── lazy_loader            ├── folder_compressor            ├── shell_collector            ├── user_memory            ├── sensitive_filter        ├── context/        ├── budget            ├── schema_generator            ├── codebase_indexer            ├── config            ├── loader            ├── algo_handlers            ├── engine        ├── analyzers/            ├── preprocessor        ├── agents/            ├── context_engine            ├── executor    ├── analysis/        ├── extractors        ├── collector        ├── runner        ├── ai_tools_manager        ├── cli        ├── _utils        ├── docker_manager    ├── tools/        ├── vscode_manager        ├── config_manager        ├── health_checker        ├── _docker            ├── _cmd_uninstall_extension        ├── health_runner    ├── cli/        ├── model_manager        ├── strategy_commands        ├── formatters            ├── planner        ├── app        ├── config            ├── analyze        ├── examples        ├── runner    ├── planfile/        ├── executor_simple        ├── models        ├── detector    ├── detection/        ├── model_selector        ├── _utils    ├── orchestration/        ├── cli        ├── cli_utils            ├── cli        ├── session/            ├── manager            ├── cli            ├── manager            ├── ports        ├── instances/            ├── models            ├── cli            ├── ports        ├── vscode/            ├── defaults            ├── config_io            ├── orchestrator            ├── models            ├── cli        ├── llm/            ├── health            ├── models            ├── executors            ├── orchestrator            ├── models            ├── cli        ├── queue/            ├── models            ├── _cmd_cleanup            ├── _cmd_remove            ├── _cmd_status            ├── manager            ├── cli            ├── _persistence            ├── limiter            ├── _crud        ├── ratelimit/            ├── models            ├── cli        ├── routing/            ├── models            ├── engine        ├── cli_main        ├── issues        ├── server    ├── mcp/        ├── client        ├── __main__        ├── workflows        ├── tools        ├── proxy    ├── integrations/        ├── service    ├── routing/        ├── client        ├── proxym        ├── selector        ├── logging_setup        ├── generate_strategy```

## API Overview

### Classes

- **`CustomMetrics`** — —
- **`HealthChecks`** — —
- **`PrometheusMetrics`** — —
- **`AlertingRules`** — —
- **`EntropyResult`** — Result of entropy analysis.
- **`EntropyAnalyzer`** — Analyzes text entropy to detect random/pseudorandom strings.
- **`MLBasedAnonymizer`** — Anonymizer using ML/NLP techniques beyond simple regex.
- **`LearnedPattern`** — A pattern learned from user code.
- **`FalsePositiveRecord`** — Record of a false positive for learning.
- **`BehavioralPasswordDetector`** — Learns and adapts to user coding patterns.
- **`PasswordCandidate`** — Candidate password detection result.
- **`ContextualPasswordDetector`** — Detects passwords based on code context and NLP patterns.
- **`DetectionResult`** — Result from hybrid detection.
- **`HybridAnonymizer`** — Combines regex and ML detection for maximum coverage.
- **`SecurityScanResult`** — Result of security scan.
- **`CICDPrivacyPipeline`** — Privacy pipeline for CI/CD integration.
- **`AnonymizationLevel`** — Configuration for a specific anonymization level.
- **`MultiStageAnonymizer`** — Manages multiple anonymization levels for different use cases.
- **`SimulatedLLMResponse`** — Simulated LLM API response.
- **`SimulatedLLMAPI`** — Simulates external LLM API (like OpenAI, Anthropic, etc.).
- **`ModelConfig`** — Configuration for a single model tier.
- **`TierThresholds`** — Thresholds that determine which model tier to use.
- **`ProxyConfig`** — LiteLLM proxy settings.
- **`LlxConfig`** — Root configuration for llx.
- **`LLMResponse`** — Response from an LLM call.
- **`LLM`** — Synchronous LiteLLM wrapper with .env configuration.
- **`DeanonymizationResult`** — Result of deanonymization operation.
- **`ProjectDeanonymizationResult`** — Result of project-level deanonymization.
- **`LiteLLMModelConfig`** — Configuration for a single LiteLLM model.
- **`LiteLLMConfig`** — Complete LiteLLM configuration.
- **`StreamingProjectAnonymizer`** — Stream-process large projects with progress tracking.
- **`StreamingProjectDeanonymizer`** — Stream-process large deanonymization operations.
- **`ParallelProjectProcessor`** — Process multiple files in parallel for speed.
- **`ASTAnonymizer`** — AST transformer that anonymizes code symbols while preserving structure.
- **`ProjectAnonymizationResult`** — —
- **`ProjectAnonymizer`** — —
- **`DeanonymizationResult`** — Result of deanonymization operation.
- **`ProjectDeanonymizationResult`** — Result of project-level deanonymization.
- **`ProjectDeanonymizer`** — Restores original values from anonymized project content.
- **`StreamingDeanonymizer`** — Deanonymizer for streaming/chunked LLM responses.
- **`ProjectDeanonymizer`** — Restores original values from anonymized project content.
- **`SymbolMapping`** — Mapping between original and anonymized symbols.
- **`AnonymizationContext`** — Context for project-wide anonymization with persistent mapping.
- **`ProgressInfo`** — Progress information for streaming operations.
- **`ProgressCallback`** — Protocol for progress callbacks.
- **`ChunkResult`** — Result of processing a single chunk.
- **`ChunkedProcessor`** — Process large files in chunks to manage memory usage.
- **`ExampleHelper`** — Helper class for common example operations.
- **`TaskQueue`** — Simple task queue for batch processing.
- **`WorkflowRunner`** — Run predefined workflows.
- **`TraceStep`** — A single recorded step in the execution trace.
- **`TraceRecorder`** — Records execution trace and generates markdown documentation.
- **`AnonymizationPattern`** — Definition of a sensitive data pattern.
- **`AnonymizationResult`** — Result of anonymization operation with mapping for deanonymization.
- **`Anonymizer`** — Reversible anonymization engine for sensitive data.
- **`SmoketestRequest`** — —
- **`SmoketestResponse`** — —
- **`SmoketestDBSchema`** — —
- **`SmoketestDBSchemaRequest`** — —
- **`SmoketestDBSchemaResponse`** — —
- **`User`** — —
- **`Product`** — —
- **`ChatMessage`** — —
- **`PreLLMExtras`** — preLLM-specific extensions in the request body.
- **`ChatCompletionRequest`** — —
- **`ChatCompletionChoice`** — —
- **`UsageInfo`** — —
- **`PreLLMMeta`** — preLLM metadata in the response.
- **`ChatCompletionResponse`** — —
- **`BatchItem`** — —
- **`HealthResponse`** — —
- **`AuthMiddleware`** — Bearer token auth using LITELLM_MASTER_KEY. Skips auth if key is not set.
- **`QueryDecomposer`** — Decomposes user queries using a small LLM before routing to a large model.
- **`PromptNotFoundError`** — Raised when a prompt name is not found in the registry.
- **`PromptRenderError`** — Raised when a prompt template fails to render.
- **`PromptEntry`** — Single prompt entry with template, max_tokens, and temperature.
- **`PromptRegistry`** — Loads prompts from YAML, caches, validates placeholders.
- **`ValidationResult`** — Result of validating data against a schema.
- **`SchemaDefinition`** — Parsed schema definition from YAML.
- **`ResponseValidator`** — Validates LLM responses against YAML-defined schemas.
- **`PreLLM`** — preLLM v0.2/v0.3 — small LLM decomposition before large LLM routing.
- **`SensitivityLevel`** — —
- **`ProcessInfo`** — —
- **`LocaleInfo`** — —
- **`ShellInfo`** — —
- **`NetworkContext`** — —
- **`ShellContext`** — —
- **`ContextSchema`** — —
- **`FilterReport`** — —
- **`CompressedFolder`** — —
- **`RuntimeContext`** — Full runtime snapshot — env, process, locale, network, git, system.
- **`SessionSnapshot`** — Exportable session snapshot — enables persistent context across restarts.
- **`Policy`** — —
- **`ApprovalMode`** — —
- **`StepStatus`** — —
- **`DecompositionStrategy`** — Strategy for how the small LLM preprocesses a query.
- **`BiasPattern`** — —
- **`ModelConfig`** — —
- **`GuardConfig`** — Top-level YAML config model (v0.1 compat).
- **`AnalysisResult`** — Result of query analysis (v0.1 compat).
- **`GuardResponse`** — Response from Prellm (v0.1 compat).
- **`DomainRule`** — Configurable domain rule — keywords, intent, required fields, enrich template.
- **`LLMProviderConfig`** — Configuration for a single LLM provider (small or large).
- **`DecompositionPrompts`** — System prompts for each decomposition step — all configurable via YAML.
- **`PreLLMConfig`** — Top-level config for preLLM v0.2 — fully YAML-driven.
- **`ClassificationResult`** — Output of the CLASSIFY step.
- **`StructureResult`** — Output of the STRUCTURE step.
- **`DecompositionResult`** — Full result of the small LLM decomposition pipeline.
- **`PreLLMResponse`** — Response from preLLM v0.2 — includes decomposition + large LLM output.
- **`ProcessStep`** — —
- **`ProcessConfig`** — —
- **`StepResult`** — Result of a single process chain step.
- **`ProcessResult`** — Result of a full process chain execution.
- **`AuditEntry`** — Single audit log entry for traceability.
- **`LLMProvider`** — LiteLLM wrapper with retry and fallback support.
- **`PipelineStep`** — Configuration for a single pipeline step.
- **`PipelineConfig`** — Configuration for a complete pipeline.
- **`StepExecutionResult`** — Result of executing a single pipeline step.
- **`PipelineResult`** — Result of executing a full pipeline.
- **`PromptPipeline`** — Generic pipeline — executes a sequence of LLM + algorithmic steps.
- **`ProcessChain`** — Execute multi-step DevOps workflows with preLLM validation at each step.
- **`LazyLoader`** — Base class for components that need lazy loading of resources.
- **`FolderCompressor`** — Compresses a project folder into a lightweight representation for LLM context.
- **`ShellContextCollector`** — Collects full shell environment context for LLM prompt enrichment.
- **`UserMemory`** — Stores user query history and learned preferences.
- **`SensitiveDataFilter`** — Classifies and filters sensitive data from context before LLM calls.
- **`BudgetExceededError`** — Raised when the monthly budget limit has been reached.
- **`UsageEntry`** — Single API call cost record.
- **`BudgetTracker`** — Tracks LLM API spend against a monthly budget.
- **`ContextSchemaGenerator`** — Generates a structured context schema from available context sources.
- **`CodeSymbol`** — A code symbol extracted from source.
- **`FileIndex`** — Index of a single source file.
- **`CodebaseIndex`** — Full codebase index.
- **`CodebaseIndexer`** — Index a codebase using tree-sitter for AST-based symbol extraction.
- **`PipelineStep`** — Configuration for a single pipeline step.
- **`PipelineConfig`** — Configuration for a complete pipeline.
- **`StepExecutionResult`** — Result of executing a single pipeline step.
- **`PipelineResult`** — Result of executing a full pipeline.
- **`AlgoHandlersMixin`** — —
- **`PromptPipeline`** — Generic pipeline — executes a sequence of LLM + algorithmic steps.
- **`PreprocessResult`** — Output of the PreprocessorAgent — structured input for the ExecutorAgent.
- **`PreprocessorAgent`** — Agent preprocessing — small LLM (≤24B) analyzes and structures queries.
- **`ContextEngine`** — Collects context from environment, git, and system for prompt enrichment.
- **`ExecutorResult`** — Output of the ExecutorAgent.
- **`ExecutorAgent`** — Agent execution — large LLM (>24B) executes structured tasks.
- **`ProjectMetrics`** — Aggregated project metrics that drive model selection.
- **`ToolResult`** — —
- **`AIToolsManager`** — Manages AI tools container and operations.
- **`DockerManager`** — Manages Docker containers for llx ecosystem.
- **`VSCodeManager`** — Manages VS Code server with AI extensions.
- **`ConfigManager`** — Manages llx configuration files and settings.
- **`HealthChecker`** — Comprehensive health monitoring for llx ecosystem.
- **`HealthCheckRunner`** — Runs comprehensive health checks and generates reports.
- **`ModelManager`** — Manages local Ollama models and llx configurations.
- **`PlanfileConfig`** — Configuration for planfile generation and execution.
- **`TaskResult`** — Result of executing a task.
- **`TaskType`** — Type of task in the strategy.
- **`ModelTier`** — Model tier for different phases of work.
- **`ModelHints`** — AI model hints for different phases of task execution.
- **`TaskPattern`** — A pattern for generating tasks.
- **`Sprint`** — A sprint in the strategy.
- **`Goal`** — Project goal definition.
- **`QualityGate`** — Quality gate definition.
- **`Strategy`** — Main strategy configuration.
- **`ProjectTypeDetector`** — Detects project type from directory name and files.
- **`ModelProvider`** — Available model providers.
- **`ModelTier`** — Model pricing tiers.
- **`ModelFilter`** — Filter criteria for model selection.
- **`ModelSelector`** — Select models based on filters and preferences.
- **`SessionManager`** — Manages multiple sessions with intelligent scheduling and rate limiting.
- **`InstanceManager`** — Manages multiple Docker instances with intelligent allocation and monitoring.
- **`PortAllocator`** — Manages port allocation for instances.
- **`SessionType`** — Types of sessions.
- **`SessionStatus`** — Session status.
- **`SessionConfig`** — Configuration for a session.
- **`SessionState`** — Current state of a session.
- **`VSCodePortAllocator`** — Manages port allocation for VS Code instances.
- **`VSCodeOrchestrator`** — Orchestrates multiple VS Code instances with intelligent management.
- **`InstanceType`** — Types of instances.
- **`InstanceStatus`** — Instance status.
- **`InstanceConfig`** — Configuration for an instance.
- **`InstanceState`** — Current state of an instance.
- **`VSCodeAccountType`** — Types of VS Code accounts.
- **`VSCodeAccount`** — VS Code account configuration.
- **`VSCodeInstanceConfig`** — Configuration for a VS Code instance.
- **`VSCodeSession`** — Active VS Code session.
- **`LLMOrchestrator`** — Orchestrates multiple LLM providers and models with intelligent routing.
- **`LLMProviderType`** — Types of LLM providers.
- **`ModelCapability`** — Model capabilities.
- **`LLMModel`** — LLM model configuration.
- **`LLMProvider`** — LLM provider configuration.
- **`LLMRequest`** — LLM request.
- **`LLMResponse`** — LLM response.
- **`QueueStatus`** — Queue status.
- **`RequestPriority`** — Request priority levels.
- **`QueueRequest`** — A request in the queue.
- **`QueueConfig`** — Configuration for a queue.
- **`QueueState`** — Current state of a queue.
- **`QueueManager`** — Manages multiple request queues with intelligent prioritization.
- **`RateLimiter`** — Manages rate limiting for multiple providers and accounts.
- **`LimitType`** — Types of rate limits.
- **`RateLimitConfig`** — Configuration for rate limiting.
- **`RateLimitState`** — Current state of rate limiting.
- **`RoutingStrategy`** — Routing strategies.
- **`ResourceType`** — Types of resources to route to.
- **`RequestPriority`** — Request priority levels (mirrors queue.models).
- **`RoutingRequest`** — A request to be routed.
- **`RoutingDecision`** — A routing decision.
- **`RoutingMetrics`** — Metrics for routing performance.
- **`RoutingEngine`** — Intelligent routing engine for LLM and VS Code requests.
- **`LlxMcpClient`** — Thin MCP client for the llx SSE service.
- **`LlxMcpRunResult`** — Result of an llx MCP fix/refactor workflow.
- **`McpTool`** — —
- **`McpServiceState`** — Runtime state exposed via health and metrics endpoints.
- **`ChatMessage`** — A single chat message.
- **`ChatResponse`** — Response from LLM completion.
- **`LlxClient`** — LLM client that routes through LiteLLM proxy or calls directly.
- **`ProxymStatus`** — Status of the proxym proxy server.
- **`ProxymResponse`** — Response from proxym chat completion.
- **`ProxymClient`** — Client for proxym intelligent AI proxy.
- **`ModelTier`** — LLM model tiers ranked by capability and cost.
- **`SelectionResult`** — Result of model selection with explanation.

### Functions

- `print_header()` — —
- `print_status()` — —
- `print_warning()` — —
- `print_error()` — —
- `check_docker()` — —
- `check_compose()` — —
- `get_compose_cmd()` — —
- `print_header()` — —
- `print_status()` — —
- `print_error()` — —
- `print_warning()` — —
- `get_compose_cmd()` — —
- `is_running()` — —
- `start_ai_tools()` — —
- `stop_ai_tools()` — —
- `shell()` — —
- `status()` — —
- `test()` — —
- `logs()` — —
- `restart()` — —
- `quick_chat()` — —
- `help()` — —
- `main()` — —
- `test()` — —
- `show_help()` — —
- `list_examples()` — —
- `run_example()` — —
- `check_dependencies()` — —
- `generate_simple_strategy(project_path, output)` — Generate strategy with minimal configuration.
- `create_complex_project(base_path)` — Create project with complex sensitive data patterns.
- `main()` — —
- `create_sample_codebase(base_path)` — Create sample codebase for learning demonstration.
- `main()` — —
- `create_test_code_samples()` — Create various code samples with hidden passwords.
- `main()` — —
- `create_test_scenarios()` — Create test scenarios with various sensitive data.
- `main()` — —
- `create_large_project(base_path, num_files)` — Create a project with many files for streaming demo.
- `main()` — —
- `main()` — —
- `create_sample_project(base_path)` — Create a sample Python project for demonstration.
- `main()` — —
- `create_cicd_project(base_path)` — Create sample project for CI/CD demo.
- `main()` — —
- `create_business_logic_project(base_path)` — Create project with sensitive business logic.
- `main()` — —
- `main()` — —
- `main()` — —
- `show_help()` — —
- `build_docker_cmd()` — —
- `check_service_health()` — —
- `check_redis()` — —
- `check_postgres()` — —
- `docker_start()` — —
- `docker_stop()` — —
- `docker_status()` — —
- `docker_logs()` — —
- `docker_exec()` — —
- `docker_test()` — —
- `docker_clean()` — —
- `create_compose_file()` — —
- `main()` — —
- `print_error()` — —
- `print_success()` — —
- `print_status()` — —
- `show_help()` — —
- `get_app_prompt()` — —
- `main()` — —
- `show_help()` — —
- `select_model()` — —
- `demo_cost_filtering()` — —
- `demo_speed_priority()` — —
- `demo_provider_filter()` — —
- `interactive_demo()` — —
- `main()` — —
- `create_realistic_project(base_path)` — Create a realistic e-commerce project structure.
- `main()` — —
- `show_help()` — —
- `determine_task_type()` — —
- `build_llx_cmd()` — —
- `is_extension_installed()` — —
- `install_extension()` — —
- `hello_world()` — —
- `print()` — —
- `load_pyqual_config(path)` — Load pyqual.yaml configuration.
- `save_pyqual_config(path, config)` — Save pyqual.yaml configuration.
- `set_env_file(workdir, model)` — Set LLM_MODEL in .env file.
- `restore_env_file(workdir, old_model)` — Restore original LLM_MODEL in .env file.
- `backup_config(path)` — Create timestamped backup of config.
- `set_model(config, model)` — Set LLM_MODEL in pyqual config.
- `force_fix_stage(config)` — Modify quality gates to force fix stage.
- `restore_metrics(config, original)` — Restore original metric thresholds.
- `run_pyqual(workdir, dry_run, verbose)` — Run pyqual command.
- `main()` — —
- `normalize_litellm_base_url(base_url)` — Normalize an OpenAI-compatible base URL for llx clients.
- `get_llm_model()` — Get the default LLM model from environment or fallback settings.
- `get_api_key()` — Get the OpenRouter API key from environment.
- `get_llm(model)` — Get a configured LLM instance.
- `fix(workdir, errors, apply, model)` — Fix code issues using LLX-driven model selection.
- `apply_code_changes(workdir, content)` — Parse LLM response and apply changes to files.
- `load_litellm_config(project_path)` — Convenience function to load LiteLLM configuration.
- `anonymize_project_with_progress(project_path, output_dir, include, exclude)` — Anonymize project with progress tracking.
- `deanonymize_response_streaming(llm_response_stream, context_path, on_chunk)` — Deanonymize streaming LLM response.
- `quick_project_deanonymize(text, context_path)` — One-shot deanonymization using saved context.
- `build_reverse_lookup(context)` — Build reverse mapping from anonymized token to original name.
- `find_symbol_tokens(text)` — Find symbol tokens in anonymized text.
- `find_content_tokens(text)` — Find content anonymization tokens in text.
- `get_content_mapping(context)` — Safely access the last content anonymization mapping.
- `restore_imports(content, reverse_lookup)` — Restore module names in import statements.
- `restore_decorators(content, reverse_lookup)` — Restore decorator names.
- `run_mypy(output_dir)` — Run mypy type checker and save JSON output.
- `main()` — Main entry point for type check plugin.
- `run_detect_secrets(output_dir)` — Run detect-secrets scan and save JSON output.
- `main()` — Main entry point for detect secrets plugin.
- `check_version_on_pypi(version)` — Check if version already exists on PyPI.
- `parse_version(version)` — Parse version string into components.
- `bump_patch_version(version)` — Bump patch component of version.
- `update_version_file(version_path, new_version)` — Update VERSION file.
- `update_pyproject_toml(toml_path, old_version, new_version)` — Update version in pyproject.toml.
- `git_commit_version_bump(old_version, new_version)` — Commit version bump changes.
- `main()` — Main entry point for version bump plugin.
- `get_current_version()` — Read current version from VERSION file.
- `check_version_on_pypi(version)` — Check if version already exists on PyPI.
- `upload_to_pypi()` — Upload distribution to PyPI using twine.
- `main()` — Main entry point for publish plugin.
- `run_ruff_lint(output_dir)` — Run ruff linter and save JSON output.
- `run_ruff_format_check()` — Run ruff format check.
- `main()` — Main entry point for lint plugin.
- `get_current_version()` — Read current version from VERSION file.
- `verify_push()` — Verify current commit is on origin/main.
- `verify_publish(version, max_retries, delay)` — Verify version is on PyPI with retries.
- `main()` — Main entry point for verify plugin.
- `run_pip_audit(output_dir)` — Run pip-audit for CVE checks.
- `run_bandit(output_dir)` — Run bandit security scan.
- `main()` — Main entry point for security audit plugin.
- `get_env_config(env_path, small_model, large_model)` — Load preLLM configuration from environment.
- `config_set_cmd(key, value, global_)` — Set a config value persistently.
- `config_get_cmd(key, raw)` — Get a config value.
- `config_list_cmd(raw)` — List all configured values.
- `config_show_cmd()` — Show effective configuration (resolved from all sources).
- `config_init_env(global_, force)` — Generate a starter .env file with all available settings.
- `query(prompt, small, large, strategy)` — Preprocess a query with small LLM, then execute with large LLM.
- `context(json_output, schema, blocked, folder)` — Show collected environment context, schema, and blocked sensitive data.
- `process(config, guard_config, dry_run, json_output)` — Execute a DevOps process chain.
- `decompose(query, config, strategy, json_output)` — [v0.2] Decompose a query using small LLM without calling the large model.
- `init(output, devops)` — Generate a starter preLLM config file.
- `serve(host, port, small, large)` — Start the OpenAI-compatible API server.
- `doctor(env_file, live)` — Check configuration and provider connectivity.
- `budget(reset, json_output)` — Show LLM API spend tracking and budget status.
- `models(provider, search)` — List popular model pairs and provider examples.
- `session_list_cmd(memory)` — List recent interactions in the session.
- `session_export_cmd(output, memory, session_id)` — Export current session to JSON file.
- `session_import_cmd(input_file, memory)` — Import a session from JSON file.
- `session_clear_cmd(memory, force)` — Clear all session data.
- `get_current_trace()` — Get the active trace recorder for the current execution context.
- `set_current_trace(trace)` — Set the active trace recorder for the current execution context.
- `quick_anonymize(text, salt)` — One-shot anonymization with default settings.
- `quick_deanonymize(text, mapping)` — One-shot deanonymization.
- `context(json_output, schema, blocked, folder)` — Show collected environment context, schema, and blocked sensitive data.
- `context_show_cmd(json_output, schema, blocked, folder)` — Show collected runtime context.
- `list_model_pairs(provider, search)` — Filter model pairs by provider and/or search term. Pure function — no IO.
- `list_openrouter_models(provider, search)` — Filter OpenRouter models by provider and/or search term. Pure function — no IO.
- `health()` — —
- `read_users()` — —
- `read_user(user_id)` — —
- `create_user(user)` — —
- `update_user(user_id, user)` — —
- `delete_user(user_id)` — —
- `read_products()` — —
- `read_product(product_id)` — —
- `create_product(product)` — —
- `update_product(product_id, product)` — —
- `delete_product(product_id)` — —
- `health()` — —
- `list_models()` — List available model pairs.
- `chat_completions(req)` — OpenAI-compatible chat completions with preLLM preprocessing.
- `batch_process(items)` — Process multiple queries in parallel.
- `create_app(small_model, large_model, strategy, config_path)` — Factory function to create a configured preLLM API server.
- `collect_user_context(user_context)` — Process and normalize user context.
- `collect_environment_context(collect_env)` — Collect shell and runtime context if requested.
- `compress_codebase_folder(compress_folder, codebase_path)` — Compress codebase folder if requested.
- `generate_context_schema(collect_env, compress_folder, shell_ctx, compressed)` — Generate context schema if environment collection or compression is enabled.
- `build_sensitive_filter(sanitize, sensitive_rules, extra_context)` — Build and apply sensitive data filter if sanitization is enabled.
- `initialize_context_components(memory_path, codebase_path)` — Initialize optional context enrichment components.
- `prepare_context(user_context, domain_rules, collect_env, compress_folder)` — Gather all context: env, codebase, schema, sensitive filter, memory, indexer.
- `build_pipeline_context(extra_context)` — Build compact context for small LLM pipeline — strips raw blobs.
- `execute_v3_pipeline(query, small_llm, large_llm, pipeline)` — Two-agent execution path — PreprocessorAgent + ExecutorAgent + PromptPipeline.
- `run_preprocessing(preprocessor, query, extra_context, pipeline)` — Run the small-LLM preprocessing step. Returns (prep_result, duration_ms).
- `run_execution(executor, executor_input, system_prompt)` — Run the large-LLM execution step. Returns (exec_result, duration_ms).
- `persist_session(user_memory, query, exec_result)` — Persist interaction to UserMemory if available.
- `record_trace(trace, pipeline, small_llm, large_llm)` — Record preprocessing and execution steps to trace.
- `preprocess_and_execute(query, small_llm, large_llm, strategy)` — One function to preprocess and execute — like litellm.completion() but with small LLM decomposition.
- `preprocess_and_execute_sync(query, small_llm, large_llm, strategy)` — Synchronous version of preprocess_and_execute() — runs the async function in an event loop.
- `process(config, guard_config, dry_run, json_output)` — Execute a DevOps process chain.
- `decompose(query, config, strategy, json_output)` — [v0.2] Decompose a query using small LLM without calling the large model.
- `init(output, devops)` — Generate a starter preLLM config file.
- `serve(host, port, small, large)` — Start the OpenAI-compatible API server.
- `doctor(env_file, live)` — Check configuration and provider connectivity.
- `budget(reset, json_output)` — Show LLM API spend tracking and budget status.
- `models(provider, search)` — List popular model pairs and provider examples.
- `configure(name, level, sinks, bridge_stdlib)` — Configure logging.
- `log_call(func)` — Decorator that logs function calls.
- `lazy_import_global(name, import_path, globals_dict)` — Lazy import a global object.
- `get_budget_tracker(monthly_limit, persist_path)` — Get or create the global budget tracker singleton.
- `reset_budget_tracker()` — Reset the global tracker (for testing).
- `load_pipeline_config(pipelines_path, pipeline_name)` — —
- `build_pipeline(config, registry, small_llm, validators)` — —
- `extract_classification_from_state(state)` — Extract classification result from pipeline state.
- `extract_structure_from_state(state)` — Extract structure result from pipeline state.
- `extract_sub_queries_from_state(state)` — Extract sub-queries from pipeline state.
- `extract_missing_fields_from_state(state)` — Extract missing fields from pipeline state.
- `extract_matched_rule_from_state(state, current_missing_fields)` — Extract matched rule and missing fields from pipeline state.
- `build_decomposition_result(query, pipeline_name, prep_result)` — Build a backward-compatible DecompositionResult from pipeline state.
- `format_classification_context(prep_result)` — Extract and format classification context from preprocessing result.
- `format_context_schema(extra_context)` — Extract and format context schema information.
- `format_runtime_context(extra_context)` — Extract and format runtime context information.
- `format_user_context(extra_context)` — Extract and format user context information.
- `build_executor_system_prompt(prep_result, extra_context)` — Build a system prompt for the large LLM from preprocessing results and context.
- `analyze_project(project_path)` — Collect all available metrics for a project.
- `check_tool(name)` — Check if a CLI tool is available on PATH.
- `run_code2llm(project_path, output_dir, fmt)` — —
- `run_redup(project_path, output_dir, fmt)` — —
- `run_vallm(project_path, output_dir)` — —
- `run_all_tools(project_path, output_dir, on_progress)` — —
- `main()` — CLI entry point for AI tools manager.
- `main()` — —
- `main()` — CLI entry point for Docker manager.
- `main()` — CLI entry point for VS Code manager.
- `main()` — CLI entry point for config manager.
- `main()` — CLI entry point for health checker.
- `is_container_running(container_name)` — Check if a Docker container is running by name.
- `docker_exec(container, cmd, timeout, interactive)` — Run a command inside a Docker container.
- `docker_cp(src, dest, timeout)` — Copy files between host and container via ``docker cp``.
- `create_simple_handler(arg_name, arg_label, manager_method)` — Create a simple command handler that validates one argument and calls a manager method.
- `main()` — CLI entry point for model manager.
- `create_strategy(output, model, local)` — Create a new strategy interactively with LLM.
- `validate_strategy(strategy_file)` — Validate a strategy YAML file.
- `run_strategy_command(strategy_file, project_path, backend, dry_run)` — Run strategy to create tickets.
- `verify_strategy(strategy_file, project_path, backend)` — Verify strategy execution.
- `add_strategy_commands(main_app)` — Add strategy commands to main typer app.
- `output_rich(metrics, result, verbose)` — Rich terminal output for analysis results.
- `output_json(metrics, result)` — JSON output for machine consumption.
- `print_models_table(config, tag, provider, tier)` — Print models table with optional filtering.
- `print_info_tables(config)` — Print tools and models info tables.
- `analyze(path, toon_dir, task, local)` — Analyze a project and recommend the optimal LLM model.
- `select(path, toon_dir, task, local)` — Quick model selection from existing analysis files.
- `chat(path, prompt, toon_dir, task)` — Analyze project, select model, and send a prompt.
- `proxy_start(config_path, port, background)` — Start LiteLLM proxy server with llx configuration.
- `proxy_config(output)` — Generate LiteLLM proxy config.
- `proxy_status()` — Check if proxy is running.
- `mcp_start(mode, port)` — Start the llx MCP server.
- `plan_generate(strategy, output_dir, model, profile)` — Generate code from strategy.
- `plan_review(strategy, project_path)` — Review strategy against project.
- `plan_execute(strategy, project_path, backend, dry_run)` — Execute strategy to create tickets.
- `models(tag, provider, tier)` — Show available models with optional filtering by tags, provider, or tier.
- `info()` — Show available tools, models, and configuration.
- `fix(workdir, errors, apply, model)` — Fix code issues using LLX-driven model selection (pyqual integration).
- `init(path)` — Initialize llx.toml configuration file.
- `analyze(path, toon_dir, task, local)` — —
- `example_create_strategy()` — Create a strategy using LLX with local LLM.
- `example_validate_strategy()` — Load and validate an existing strategy.
- `example_run_strategy()` — Run strategy to create tickets (dry run).
- `example_verify_strategy()` — Verify strategy execution.
- `example_programmatic_strategy()` — Create strategy programmatically without LLM.
- `load_valid_strategy(path)` — Load and validate strategy from YAML file.
- `verify_strategy_post_execution(strategy, project_path, backend)` — Verify strategy after execution.
- `analyze_project_metrics(project_path)` — Analyze project metrics using available tools.
- `apply_strategy_to_tickets(strategy, project_path, backend, dry_run)` — Apply strategy to create tickets in PM system.
- `run_strategy(strategy_path, project_path, backend, dry_run)` — Run strategy: load, validate, and apply.
- `execute_strategy(strategy_path, project_path)` — Execute strategy with simplified format support.
- `load_json(path, label)` — Load JSON from *path*, returning None on missing file or error.
- `save_json(path, data, label)` — Save *data* as JSON to *path*, creating parent dirs as needed.
- `main()` — —
- `cmd_remove_wrapper(args, id_attr, id_label, remove_func)` — Generic wrapper for remove commands.
- `cmd_remove_pair_wrapper(args, first_attr, second_attr, first_label)` — Generic wrapper for remove commands keyed by two arguments.
- `cmd_status_wrapper(args, id_attr, id_label, status_func)` — Generic wrapper for status commands.
- `cmd_list_wrapper(items, title, formatter)` — Generic wrapper for list commands.
- `cmd_cleanup_wrapper(cleanup_func, item_label)` — Generic wrapper for cleanup commands.
- `main()` — —
- `main()` — —
- `main()` — —
- `create_default_vscode_config(orchestrator)` — Populate an orchestrator with default VS Code configuration.
- `load_vscode_config(orchestrator)` — Load VS Code orchestration configuration into an orchestrator instance.
- `save_vscode_config(orchestrator)` — Save VS Code orchestration configuration from an orchestrator instance.
- `main()` — CLI entry point.  CC ≤ 3.
- `perform_health_checks(providers)` — Perform health checks on all providers.
- `health_check_worker(orchestrator)` — Background worker for health checks.
- `execute_request(request, provider, model)` — Execute LLM request, dispatching to the correct provider executor.
- `execute_ollama(request, provider, model)` — Execute Ollama request.
- `execute_openai(request, provider, model)` — Execute OpenAI-compatible request.
- `execute_anthropic(request, provider, model)` — Execute Anthropic request.
- `messages_to_prompt(messages)` — Convert messages to prompt for non-chat models.
- `main()` — —
- `create_cleanup_handler(save_func)` — Create a cleanup command handler that saves state and prints completion.
- `create_remove_handler(id_attr, id_label, remove_func, save_func)` — Create a remove command handler function.
- `create_status_handler(id_attr, entity_label, get_status_func, print_summary_func)` — Create a status command handler that shows specific status or summary.
- `main()` — —
- `load_limits_from_file(self)` — Load rate limits from configuration file.
- `save_limits_to_file(self)` — Save rate limits to configuration file.
- `create_default_limits(self)` — Create default rate limits for common providers.
- `add_limit(self, config)` — Add or update a rate limit configuration.
- `remove_limit(self, provider, account)` — Remove a rate limit configuration.
- `main()` — —
- `cli_main(build_parser, dispatch, factory, cleanup)` — Generic CLI entry point.
- `load_issue_source(issues_path)` — Load issues from a JSON error file or a markdown checklist.
- `load_todo_markdown(issues_path)` — Load unchecked TODO checklist items from prefact-generated markdown.
- `resolve_issue_source(workdir, issues_path, fallback_name)` — Resolve issues, falling back to a markdown file when the primary source is empty.
- `issue_text(issue)` — Render one issue entry as a compact string.
- `task_prompt_label(task)` — Map llx task hints to prompt wording.
- `build_fix_prompt(project_path, issues, analysis, prompt_limit)` — Build a concise prompt for llx/aider from gate failures.
- `list_tools()` — —
- `call_tool(name, arguments)` — —
- `run_stdio_server()` — Run the MCP server over stdio for desktop clients.
- `create_app()` — Create an ASGI app that exposes the MCP server over SSE.
- `run_sse_server(host, port)` — Run the MCP server over SSE for web clients.
- `build_parser()` — Build the CLI parser for the MCP server.
- `main(argv)` — CLI entry point for the llx MCP server.
- `main_sync(argv)` — Synchronous entry point for CLI.
- `run_llx_fix_workflow(workdir, project_path, issues_path, output_path)` — Run the analysis + fix/refactor workflow and save a JSON report.
- `run_llx_refactor_workflow(workdir, project_path, issues_path, output_path)` — Run the llx refactor workflow and save a JSON report.
- `generate_proxy_config(config, output_path)` — Generate a LiteLLM proxy config YAML.
- `start_proxy(config)` — Start LiteLLM proxy server.
- `check_proxy(base_url)` — Check if LiteLLM proxy is running.
- `create_service_app(state, llx_server)` — Create an ASGI app that exposes the llx MCP server over SSE with health/metrics.
- `run_service(host, port, state)` — Run the persistent MCP service with uvicorn.
- `build_parser()` — Build the CLI parser for the MCP service.
- `main(argv)` — CLI entry point for the llx MCP service.
- `select_model(metrics, config)` — Select the best model tier based on project metrics.
- `check_context_fit(metrics, model)` — Check if the project context fits within the model's context window.
- `select_with_context_check(metrics, config)` — Select model and verify context window fit.
- `setup_logging(level, markdown_file, terminal_format)` — Initialize nfo logging for the entire preLLM project.
- `get_logger(name)` — Get or create the nfo logger.
- `generate_strategy_with_fix(project_path, model, sprints, focus)` — Generate strategy using llx.planfile.
- `save_fixed_strategy(data, output_path)` — Save the fixed strategy to YAML file.
- `main()` — Generate a complete strategy using the fixed generator.


## Project Structure

📄 `ai-tools-manage` (15 functions)
📄 `docker-manage` (7 functions)
📄 `docker.ai-tools.entrypoint` (3 functions)
📄 `docker.ai-tools.install-tools`
📄 `docker.ollama.entrypoint`
📄 `docker.vscode.install-extensions` (2 functions)
📄 `examples.ai-tools.run`
📄 `examples.aider.run`
📄 `examples.basic.run`
📄 `examples.cleanup`
📄 `examples.cli-tools.run`
📄 `examples.cloud-local.run`
📄 `examples.docker.docker` (14 functions)
📄 `examples.docker.run`
📄 `examples.filtering.filtering` (7 functions)
📄 `examples.filtering.run`
📄 `examples.fullstack.generate_simple` (6 functions)
📄 `examples.fullstack.run`
📄 `examples.hybrid.hybrid` (3 functions)
📄 `examples.hybrid.run`
📄 `examples.local.run`
📄 `examples.multi-provider.run`
📄 `examples.planfile.run`
📄 `examples.privacy.advanced.01_api_integration` (4 functions, 2 classes)
📄 `examples.privacy.advanced.02_multi_stage` (5 functions, 2 classes)
📄 `examples.privacy.advanced.03_cicd_integration` (8 functions, 2 classes)
📄 `examples.privacy.basic.01_text_anonymization` (1 functions)
📄 `examples.privacy.basic.02_custom_patterns` (1 functions)
📄 `examples.privacy.ml.01_entropy_ml_detection` (12 functions, 3 classes)
📄 `examples.privacy.ml.02_hybrid_system` (11 functions, 2 classes)
📄 `examples.privacy.ml.03_contextual_passwords` (10 functions, 2 classes)
📄 `examples.privacy.ml.04_behavioral_learning` (14 functions, 3 classes)
📄 `examples.privacy.project.01_anonymize_project` (2 functions)
📄 `examples.privacy.project.02_deanonymize_project` (1 functions)
📄 `examples.privacy.streaming.01_streaming_anonymization` (2 functions)
📄 `examples.proxy.run`
📄 `examples.pyqual-llx-demo`
📄 `examples.python-api.run`
📄 `examples.python-api.setup-aliases`
📄 `examples.run` (4 functions)
📄 `examples.vscode-roocode.run`
📄 `generate`
📦 `llx`
📄 `llx.__main__`
📦 `llx.analysis`
📄 `llx.analysis.collector` (21 functions, 1 classes)
📄 `llx.analysis.runner` (6 functions, 1 classes)
📦 `llx.cli`
📄 `llx.cli.app` (19 functions)
📄 `llx.cli.commands.analyze` (1 functions)
📄 `llx.cli.commands.planner` (1 functions)
📄 `llx.cli.formatters` (12 functions)
📄 `llx.cli.strategy_commands` (5 functions)
📦 `llx.commands`
📄 `llx.commands._patch_apply` (4 functions)
📄 `llx.commands.fix` (12 functions)
📄 `llx.config` (9 functions, 4 classes)
📦 `llx.detection`
📄 `llx.detection.detector` (7 functions, 1 classes)
📄 `llx.examples.utils` (13 functions, 3 classes)
📦 `llx.integrations`
📄 `llx.integrations.proxy` (3 functions)
📄 `llx.integrations.proxym` (12 functions, 3 classes)
📄 `llx.litellm_config` (10 functions, 2 classes)
📄 `llx.llm` (8 functions, 2 classes)
📦 `llx.mcp`
📄 `llx.mcp.__main__`
📄 `llx.mcp.client` (6 functions, 1 classes)
📄 `llx.mcp.server` (8 functions)
📄 `llx.mcp.service` (14 functions, 1 classes)
📄 `llx.mcp.tools` (17 functions, 1 classes)
📄 `llx.mcp.workflows` (3 functions, 1 classes)
📦 `llx.orchestration`
📄 `llx.orchestration._utils` (2 functions)
📄 `llx.orchestration.cli` (6 functions)
📄 `llx.orchestration.cli_utils` (5 functions)
📦 `llx.orchestration.instances`
📄 `llx.orchestration.instances.cli` (9 functions)
📄 `llx.orchestration.instances.manager` (18 functions, 1 classes)
📄 `llx.orchestration.instances.models` (4 classes)
📄 `llx.orchestration.instances.ports` (5 functions, 1 classes)
📦 `llx.orchestration.llm`
📄 `llx.orchestration.llm.cli` (11 functions)
📄 `llx.orchestration.llm.executors` (6 functions)
📄 `llx.orchestration.llm.health` (2 functions)
📄 `llx.orchestration.llm.models` (6 classes)
📄 `llx.orchestration.llm.orchestrator` (28 functions, 1 classes)
📦 `llx.orchestration.queue`
📄 `llx.orchestration.queue.cli` (9 functions)
📄 `llx.orchestration.queue.manager` (21 functions, 1 classes)
📄 `llx.orchestration.queue.models` (1 functions, 5 classes)
📦 `llx.orchestration.ratelimit`
📄 `llx.orchestration.ratelimit._crud` (3 functions)
📄 `llx.orchestration.ratelimit._persistence` (2 functions)
📄 `llx.orchestration.ratelimit.cli` (11 functions)
📄 `llx.orchestration.ratelimit.limiter` (17 functions, 1 classes)
📄 `llx.orchestration.ratelimit.models` (3 classes)
📦 `llx.orchestration.routing`
📄 `llx.orchestration.routing.cli` (7 functions)
📄 `llx.orchestration.routing.engine` (38 functions, 1 classes)
📄 `llx.orchestration.routing.models` (6 classes)
📦 `llx.orchestration.session`
📄 `llx.orchestration.session.cli` (7 functions)
📄 `llx.orchestration.session.manager` (20 functions, 1 classes)
📄 `llx.orchestration.session.models` (4 classes)
📄 `llx.orchestration.utils._cmd_cleanup` (1 functions)
📄 `llx.orchestration.utils._cmd_remove` (1 functions)
📄 `llx.orchestration.utils._cmd_status` (1 functions)
📦 `llx.orchestration.vscode`
📄 `llx.orchestration.vscode.cli` (10 functions)
📄 `llx.orchestration.vscode.config_io` (2 functions)
📄 `llx.orchestration.vscode.defaults` (1 functions)
📄 `llx.orchestration.vscode.models` (4 classes)
📄 `llx.orchestration.vscode.orchestrator` (27 functions, 1 classes)
📄 `llx.orchestration.vscode.ports` (4 functions, 1 classes)
📦 `llx.planfile`
📄 `llx.planfile.config` (5 functions, 1 classes)
📄 `llx.planfile.examples` (5 functions)
📄 `llx.planfile.executor_simple` (7 functions, 1 classes)
📄 `llx.planfile.generate_strategy` (19 functions)
📄 `llx.planfile.model_selector` (12 functions, 4 classes)
📄 `llx.planfile.models` (5 functions, 8 classes)
📄 `llx.planfile.runner` (5 functions)
📦 `llx.prellm` (1 functions)
📄 `llx.prellm._nfo_compat` (11 functions, 3 classes)
📦 `llx.prellm.agents`
📄 `llx.prellm.agents.executor` (3 functions, 2 classes)
📄 `llx.prellm.agents.preprocessor` (6 functions, 2 classes)
📦 `llx.prellm.analyzers`
📄 `llx.prellm.analyzers.context_engine` (13 functions, 1 classes)
📄 `llx.prellm.budget` (11 functions, 3 classes)
📦 `llx.prellm.chains`
📄 `llx.prellm.chains.process_chain` (10 functions, 1 classes)
📄 `llx.prellm.cli` (13 functions)
📄 `llx.prellm.cli_commands` (10 functions)
📄 `llx.prellm.cli_config` (6 functions)
📄 `llx.prellm.cli_context` (2 functions)
📄 `llx.prellm.cli_query` (5 functions)
📦 `llx.prellm.context`
📄 `llx.prellm.context.codebase_indexer` (14 functions, 4 classes)
📄 `llx.prellm.context.folder_compressor` (10 functions, 1 classes)
📄 `llx.prellm.context.schema_generator` (9 functions, 1 classes)
📄 `llx.prellm.context.sensitive_filter` (14 functions, 1 classes)
📄 `llx.prellm.context.shell_collector` (8 functions, 1 classes)
📄 `llx.prellm.context.user_memory` (15 functions, 1 classes)
📄 `llx.prellm.context_ops` (8 functions)
📄 `llx.prellm.core` (11 functions, 1 classes)
📄 `llx.prellm.env_config` (2 functions)
📄 `llx.prellm.extractors` (11 functions)
📄 `llx.prellm.llm_provider` (4 functions, 1 classes)
📄 `llx.prellm.logging_setup` (3 functions)
📄 `llx.prellm.model_catalog` (2 functions)
📄 `llx.prellm.models` (2 functions, 33 classes)
📦 `llx.prellm.pipeline`
📄 `llx.prellm.pipeline.algo_handlers` (12 functions, 1 classes)
📄 `llx.prellm.pipeline.config` (4 classes)
📄 `llx.prellm.pipeline.engine` (5 functions, 1 classes)
📄 `llx.prellm.pipeline.loader` (2 functions)
📄 `llx.prellm.pipeline_ops` (5 functions)
📄 `llx.prellm.prompt_registry` (11 functions, 5 classes)
📄 `llx.prellm.query_decomposer` (10 functions, 1 classes)
📄 `llx.prellm.server` (9 functions, 10 classes)
📄 `llx.prellm.trace` (29 functions, 2 classes)
📦 `llx.prellm.utils`
📄 `llx.prellm.utils.lazy_imports` (1 functions)
📄 `llx.prellm.utils.lazy_loader` (3 functions, 1 classes)
📄 `llx.prellm.validators` (7 functions, 3 classes)
📦 `llx.privacy`
📄 `llx.privacy.__core` (13 functions, 3 classes)
📄 `llx.privacy._project_anonymizer` (8 functions, 2 classes)
📄 `llx.privacy._project_ast` (10 functions, 1 classes)
📄 `llx.privacy._project_context` (13 functions, 2 classes)
📄 `llx.privacy._streaming_chunking` (5 functions, 4 classes)
📄 `llx.privacy._streaming_impl` (18 functions, 3 classes)
📄 `llx.privacy.deanonymize` (16 functions, 4 classes)
📄 `llx.privacy.deanonymize_engine` (4 functions, 1 classes)
📄 `llx.privacy.deanonymize_results` (2 classes)
📄 `llx.privacy.deanonymize_utils` (6 functions)
📄 `llx.privacy.project`
📄 `llx.privacy.streaming`
📦 `llx.pyqual_plugins`
📄 `llx.pyqual_plugins.bump_version` (7 functions)
📄 `llx.pyqual_plugins.detect_secrets` (2 functions)
📄 `llx.pyqual_plugins.lint` (3 functions)
📄 `llx.pyqual_plugins.publish` (4 functions)
📄 `llx.pyqual_plugins.security_audit` (3 functions)
📄 `llx.pyqual_plugins.type_check` (2 functions)
📄 `llx.pyqual_plugins.verify_push_publish` (4 functions)
📦 `llx.routing`
📄 `llx.routing.client` (11 functions, 3 classes)
📄 `llx.routing.selector` (9 functions, 2 classes)
📦 `llx.tools`
📄 `llx.tools._docker` (3 functions)
📄 `llx.tools._utils`
📄 `llx.tools.ai_tools_manager` (29 functions, 1 classes)
📄 `llx.tools.cli` (6 functions)
📄 `llx.tools.config_manager` (45 functions, 1 classes)
📄 `llx.tools.docker_manager` (24 functions, 1 classes)
📄 `llx.tools.health_checker` (27 functions, 1 classes)
📄 `llx.tools.health_runner` (10 functions, 1 classes)
📄 `llx.tools.model_manager` (36 functions, 1 classes)
📄 `llx.tools.utils._cmd_uninstall_extension` (1 functions)
📄 `llx.tools.vscode_manager` (38 functions, 1 classes)
📄 `llx.utils.cli_main` (1 functions)
📄 `llx.utils.issues` (7 functions)
📦 `my-api`
📄 `my-api.main` (11 functions, 2 classes)
📄 `my-api.models` (5 classes)
📄 `my-api.monitoring` (14 functions, 4 classes)
📄 `project`
📄 `scripts.pyqual_auto` (10 functions)
📄 `simple_generate` (1 functions)
📄 `trace` (1 functions)

## Requirements

- Python >= >=3.10
- typer >=0.24- rich >=13.0- pydantic >=2.0- pydantic-settings >=2.0- pydantic-yaml >=1.0- tomli >=2.0; python_version<'3.11'- httpx >=0.27- pyyaml >=6.0- requests >=2.31- docker >=6.0- psutil >=5.9- planfile >=0.1.30

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/llx
cd llx

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/llx/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/llx/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/llx/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/llx/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->