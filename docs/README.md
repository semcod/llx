<!-- code2docs:start --># llx

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-1090-green)
> **1090** functions | **177** classes | **160** files | CC̄ = 3.8

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
├── trace├── simple_generate├── my-api/    ├── monitoring    ├── config├── llx/    ├── __main__        ├── utils        ├── env_config        ├── cli_config        ├── cli        ├── trace    ├── litellm_config        ├── cli_context        ├── model_catalog    ├── models    ├── main    ├── prellm/        ├── query_decomposer        ├── server        ├── context_ops        ├── pipeline_ops        ├── prompt_registry        ├── cli_query        ├── validators        ├── core        ├── extractors        ├── models        ├── llm_provider        ├── _nfo_compat        ├── pipeline        ├── runner    ├── analysis/        ├── cli_commands        ├── ai_tools_manager        ├── docker_manager        ├── cli        ├── collector        ├── _utils        ├── budget    ├── tools/        ├── vscode_manager        ├── config_manager        ├── _docker        ├── health_checker        ├── health_runner    ├── cli/        ├── model_manager        ├── strategy_commands        ├── formatters        ├── config        ├── examples        ├── runner        ├── executor_simple    ├── planfile/        ├── model_selector        ├── models        ├── detector    ├── detection/        ├── cli        ├── _utils    ├── orchestration/        ├── cli_utils        ├── cli_main        ├── tools        ├── server    ├── mcp/        ├── __main__        ├── proxy    ├── integrations/        ├── proxym    ├── routing/        ├── client        ├── selector            ├── cli            ├── manager        ├── session/            ├── models            ├── cli            ├── manager            ├── ports        ├── instances/            ├── models            ├── cli            ├── ports        ├── vscode/            ├── orchestrator            ├── models            ├── cli        ├── llm/            ├── health            ├── executors            ├── orchestrator            ├── models            ├── cli            ├── manager        ├── queue/            ├── models            ├── _cmd_cleanup            ├── _cmd_remove            ├── _cmd_status            ├── limiter            ├── cli        ├── ratelimit/            ├── models            ├── engine            ├── cli        ├── routing/            ├── models            ├── _cmd_uninstall_extension        ├── chains/            ├── process_chain        ├── utils/            ├── lazy_imports            ├── lazy_loader            ├── folder_compressor            ├── shell_collector            ├── user_memory            ├── sensitive_filter        ├── context/            ├── codebase_indexer            ├── schema_generator        ├── analyzers/            ├── context_engine            ├── preprocessor        ├── agents/            ├── executor├── ai-tools-manage├── docker-manage├── generate├── project    ├── cleanup    ├── run        ├── entrypoint        ├── install-extensions        ├── entrypoint        ├── install-tools        ├── run        ├── run        ├── run        ├── run        ├── docker        ├── run        ├── run        ├── generate_simple        ├── run        ├── run        ├── run        ├── run        ├── filtering        ├── run        ├── run        ├── setup-aliases        ├── run        ├── hybrid        ├── run        ├── run        ├── logging_setup        ├── app        ├── generate_strategy```

## API Overview

### Classes

- **`CustomMetrics`** — —
- **`HealthChecks`** — —
- **`PrometheusMetrics`** — —
- **`AlertingRules`** — —
- **`ModelConfig`** — Configuration for a single model tier.
- **`TierThresholds`** — Thresholds that determine which model tier to use.
- **`ProxyConfig`** — LiteLLM proxy settings.
- **`LlxConfig`** — Root configuration for llx.
- **`ExampleHelper`** — Helper class for common example operations.
- **`TaskQueue`** — Simple task queue for batch processing.
- **`WorkflowRunner`** — Run predefined workflows.
- **`TraceStep`** — A single recorded step in the execution trace.
- **`TraceRecorder`** — Records execution trace and generates markdown documentation.
- **`LiteLLMModelConfig`** — Configuration for a single LiteLLM model.
- **`LiteLLMConfig`** — Complete LiteLLM configuration.
- **`SmoketestRequest`** — —
- **`SmoketestResponse`** — —
- **`SmoketestDBSchema`** — —
- **`SmoketestDBSchemaRequest`** — —
- **`SmoketestDBSchemaResponse`** — —
- **`User`** — —
- **`Product`** — —
- **`QueryDecomposer`** — Decomposes user queries using a small LLM before routing to a large model.
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
- **`ToolResult`** — —
- **`AIToolsManager`** — Manages AI tools container and operations.
- **`DockerManager`** — Manages Docker containers for llx ecosystem.
- **`ProjectMetrics`** — Aggregated project metrics that drive model selection.
- **`BudgetExceededError`** — Raised when the monthly budget limit has been reached.
- **`UsageEntry`** — Single API call cost record.
- **`BudgetTracker`** — Tracks LLM API spend against a monthly budget.
- **`VSCodeManager`** — Manages VS Code server with AI extensions.
- **`ConfigManager`** — Manages llx configuration files and settings.
- **`HealthChecker`** — Comprehensive health monitoring for llx ecosystem.
- **`HealthCheckRunner`** — Runs comprehensive health checks and generates reports.
- **`ModelManager`** — Manages local Ollama models and llx configurations.
- **`PlanfileConfig`** — Configuration for planfile generation and execution.
- **`TaskResult`** — Result of executing a task.
- **`ModelProvider`** — Available model providers.
- **`ModelTier`** — Model pricing tiers.
- **`ModelFilter`** — Filter criteria for model selection.
- **`ModelSelector`** — Select models based on filters and preferences.
- **`TaskType`** — Type of task in the strategy.
- **`ModelTier`** — Model tier for different phases of work.
- **`ModelHints`** — AI model hints for different phases of task execution.
- **`TaskPattern`** — A pattern for generating tasks.
- **`Sprint`** — A sprint in the strategy.
- **`Goal`** — Project goal definition.
- **`QualityGate`** — Quality gate definition.
- **`Strategy`** — Main strategy configuration.
- **`ProjectTypeDetector`** — Detects project type from directory name and files.
- **`McpTool`** — —
- **`ProxymStatus`** — Status of the proxym proxy server.
- **`ProxymResponse`** — Response from proxym chat completion.
- **`ProxymClient`** — Client for proxym intelligent AI proxy.
- **`ChatMessage`** — A single chat message.
- **`ChatResponse`** — Response from LLM completion.
- **`LlxClient`** — LLM client that routes through LiteLLM proxy or calls directly.
- **`ModelTier`** — LLM model tiers ranked by capability and cost.
- **`SelectionResult`** — Result of model selection with explanation.
- **`SessionManager`** — Manages multiple sessions with intelligent scheduling and rate limiting.
- **`SessionType`** — Types of sessions.
- **`SessionStatus`** — Session status.
- **`SessionConfig`** — Configuration for a session.
- **`SessionState`** — Current state of a session.
- **`InstanceManager`** — Manages multiple Docker instances with intelligent allocation and monitoring.
- **`PortAllocator`** — Manages port allocation for instances.
- **`InstanceType`** — Types of instances.
- **`InstanceStatus`** — Instance status.
- **`InstanceConfig`** — Configuration for an instance.
- **`InstanceState`** — Current state of an instance.
- **`VSCodePortAllocator`** — Manages port allocation for VS Code instances.
- **`VSCodeOrchestrator`** — Orchestrates multiple VS Code instances with intelligent management.
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
- **`QueueManager`** — Manages multiple request queues with intelligent prioritization.
- **`QueueStatus`** — Queue status.
- **`RequestPriority`** — Request priority levels.
- **`QueueRequest`** — A request in the queue.
- **`QueueConfig`** — Configuration for a queue.
- **`QueueState`** — Current state of a queue.
- **`RateLimiter`** — Manages rate limiting for multiple providers and accounts.
- **`LimitType`** — Types of rate limits.
- **`RateLimitConfig`** — Configuration for rate limiting.
- **`RateLimitState`** — Current state of rate limiting.
- **`RoutingEngine`** — Intelligent routing engine for LLM and VS Code requests.
- **`RoutingStrategy`** — Routing strategies.
- **`ResourceType`** — Types of resources to route to.
- **`RequestPriority`** — Request priority levels (mirrors queue.models).
- **`RoutingRequest`** — A request to be routed.
- **`RoutingDecision`** — A routing decision.
- **`RoutingMetrics`** — Metrics for routing performance.
- **`ProcessChain`** — Execute multi-step DevOps workflows with preLLM validation at each step.
- **`LazyLoader`** — Base class for components that need lazy loading of resources.
- **`FolderCompressor`** — Compresses a project folder into a lightweight representation for LLM context.
- **`ShellContextCollector`** — Collects full shell environment context for LLM prompt enrichment.
- **`UserMemory`** — Stores user query history and learned preferences.
- **`SensitiveDataFilter`** — Classifies and filters sensitive data from context before LLM calls.
- **`CodeSymbol`** — A code symbol extracted from source.
- **`FileIndex`** — Index of a single source file.
- **`CodebaseIndex`** — Full codebase index.
- **`CodebaseIndexer`** — Index a codebase using tree-sitter for AST-based symbol extraction.
- **`ContextSchemaGenerator`** — Generates a structured context schema from available context sources.
- **`ContextEngine`** — Collects context from environment, git, and system for prompt enrichment.
- **`PreprocessResult`** — Output of the PreprocessorAgent — structured input for the ExecutorAgent.
- **`PreprocessorAgent`** — Agent preprocessing — small LLM (≤24B) analyzes and structures queries.
- **`ExecutorResult`** — Output of the ExecutorAgent.
- **`ExecutorAgent`** — Agent execution — large LLM (>24B) executes structured tasks.

### Functions

- `test()` — —
- `generate_simple_strategy(project_path, output)` — Generate strategy with minimal configuration.
- `main()` — —
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
- `load_litellm_config(project_path)` — Convenience function to load LiteLLM configuration.
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
- `configure(name, level, sinks, bridge_stdlib)` — Configure logging.
- `log_call(func)` — Decorator that logs function calls.
- `check_tool(name)` — Check if a CLI tool is available on PATH.
- `run_code2llm(project_path, output_dir, fmt)` — —
- `run_redup(project_path, output_dir, fmt)` — —
- `run_vallm(project_path, output_dir)` — —
- `run_all_tools(project_path, output_dir, on_progress)` — —
- `process(config, guard_config, dry_run, json_output)` — Execute a DevOps process chain.
- `decompose(query, config, strategy, json_output)` — [v0.2] Decompose a query using small LLM without calling the large model.
- `init(output, devops)` — Generate a starter preLLM config file.
- `serve(host, port, small, large)` — Start the OpenAI-compatible API server.
- `doctor(env_file, live)` — Check configuration and provider connectivity.
- `budget(reset, json_output)` — Show LLM API spend tracking and budget status.
- `models(provider, search)` — List popular model pairs and provider examples.
- `main()` — CLI entry point for AI tools manager.
- `main()` — CLI entry point for Docker manager.
- `main()` — —
- `analyze_project(project_path)` — Collect all available metrics for a project.
- `get_budget_tracker(monthly_limit, persist_path)` — Get or create the global budget tracker singleton.
- `reset_budget_tracker()` — Reset the global tracker (for testing).
- `main()` — CLI entry point for VS Code manager.
- `main()` — CLI entry point for config manager.
- `is_container_running(container_name)` — Check if a Docker container is running by name.
- `docker_exec(container, cmd, timeout, interactive)` — Run a command inside a Docker container.
- `docker_cp(src, dest, timeout)` — Copy files between host and container via ``docker cp``.
- `main()` — CLI entry point for health checker.
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
- `main()` — —
- `load_json(path, label)` — Load JSON from *path*, returning None on missing file or error.
- `save_json(path, data, label)` — Save *data* as JSON to *path*, creating parent dirs as needed.
- `cmd_remove_wrapper(args, id_attr, id_label, remove_func)` — Generic wrapper for remove commands.
- `cmd_remove_pair_wrapper(args, first_attr, second_attr, first_label)` — Generic wrapper for remove commands keyed by two arguments.
- `cmd_status_wrapper(args, id_attr, id_label, status_func)` — Generic wrapper for status commands.
- `cmd_list_wrapper(items, title, formatter)` — Generic wrapper for list commands.
- `cmd_cleanup_wrapper(cleanup_func, item_label)` — Generic wrapper for cleanup commands.
- `cli_main(build_parser, dispatch, factory, cleanup)` — Generic CLI entry point.
- `list_tools()` — —
- `call_tool(name, arguments)` — —
- `main()` — —
- `main_sync()` — Synchronous entry point for CLI.
- `generate_proxy_config(config, output_path)` — Generate a LiteLLM proxy config YAML.
- `start_proxy(config)` — Start LiteLLM proxy server.
- `check_proxy(base_url)` — Check if LiteLLM proxy is running.
- `select_model(metrics, config)` — Select the best model tier based on project metrics.
- `check_context_fit(metrics, model)` — Check if the project context fits within the model's context window.
- `select_with_context_check(metrics, config)` — Select model and verify context window fit.
- `main()` — —
- `main()` — —
- `main()` — —
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
- `main()` — —
- `create_simple_handler(arg_name, arg_label, manager_method)` — Create a simple command handler that validates one argument and calls a manager method.
- `lazy_import_global(name, import_path, globals_dict)` — Lazy import a global object.
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
- `print_header()` — —
- `print_status()` — —
- `print_warning()` — —
- `print_error()` — —
- `check_docker()` — —
- `check_compose()` — —
- `get_compose_cmd()` — —
- `show_help()` — —
- `list_examples()` — —
- `run_example()` — —
- `check_dependencies()` — —
- `is_extension_installed()` — —
- `install_extension()` — —
- `hello_world()` — —
- `print()` — —
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
- `show_help()` — —
- `determine_task_type()` — —
- `build_llx_cmd()` — —
- `setup_logging(level, markdown_file, terminal_format)` — Initialize nfo logging for the entire preLLM project.
- `get_logger(name)` — Get or create the nfo logger.
- `analyze(path, toon_dir, task, local)` — Analyze a project and recommend the optimal LLM model.
- `select(path, toon_dir, task, local)` — Quick model selection from existing analysis files.
- `chat(path, prompt, toon_dir, task)` — Analyze project, select model, and send a prompt.
- `proxy_start(config_path, port, background)` — Start LiteLLM proxy server with llx configuration.
- `proxy_config(output)` — Generate LiteLLM proxy config.
- `proxy_status()` — Check if proxy is running.
- `models(tag, provider, tier)` — Show available models with optional filtering by tags, provider, or tier.
- `info()` — Show available tools, models, and configuration.
- `init(path)` — Initialize llx.toml configuration file.
- `mcp_start(mode, port)` — Start the llx MCP server.
- `mcp_config()` — Print Claude Desktop config snippet.
- `mcp_tools()` — List available MCP tools.
- `plan_apply(strategy, path, sprint, dry_run)` — Apply a planfile strategy to the project.
- `plan_models(provider, tier, local_only, cloud_only)` — List available models.
- `plan_all(description, output_dir, profile, project_type)` — Complete workflow: generate strategy, code, and optionally run.
- `plan_detect(path)` — Detect project type and show configuration.
- `plan_types()` — List all available project types.
- `plan_generate(path, output, model, sprints)` — Generate strategy.yaml using planfile.
- `plan_review(strategy, path)` — Review progress against strategy quality gates.
- `plan_code(strategy, output_dir, model, profile)` — Implement the strategy sprint-by-sprint.
- `plan_run(project_dir, port, install)` — Start the generated application (detects command from strategy or uses uvicorn).
- `plan_monitor(strategy, url, interval)` — Monitor a running application: health check + quality gates summary.
- `plan_wizard(path, description, profile, output)` — Unified wizard: Generate strategy -> Implement code -> Run -> Monitor.
- `main()` — —
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
📄 `examples.proxy.run`
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
📄 `llx.cli.app` (28 functions)
📄 `llx.cli.formatters` (12 functions)
📄 `llx.cli.strategy_commands` (5 functions)
📄 `llx.config` (7 functions, 4 classes)
📦 `llx.detection`
📄 `llx.detection.detector` (7 functions, 1 classes)
📄 `llx.examples.utils` (13 functions, 3 classes)
📦 `llx.integrations`
📄 `llx.integrations.proxy` (3 functions)
📄 `llx.integrations.proxym` (12 functions, 3 classes)
📄 `llx.litellm_config` (10 functions, 2 classes)
📦 `llx.mcp`
📄 `llx.mcp.__main__`
📄 `llx.mcp.server` (4 functions)
📄 `llx.mcp.tools` (14 functions, 1 classes)
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
📄 `llx.prellm.pipeline` (18 functions, 5 classes)
📄 `llx.prellm.pipeline_ops` (5 functions)
📄 `llx.prellm.prompt_registry` (11 functions, 5 classes)
📄 `llx.prellm.query_decomposer` (10 functions, 1 classes)
📄 `llx.prellm.server` (9 functions, 10 classes)
📄 `llx.prellm.trace` (29 functions, 2 classes)
📦 `llx.prellm.utils`
📄 `llx.prellm.utils.lazy_imports` (1 functions)
📄 `llx.prellm.utils.lazy_loader` (3 functions, 1 classes)
📄 `llx.prellm.validators` (7 functions, 3 classes)
📦 `llx.routing`
📄 `llx.routing.client` (10 functions, 3 classes)
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
📦 `my-api`
📄 `my-api.main` (11 functions, 2 classes)
📄 `my-api.models` (5 classes)
📄 `my-api.monitoring` (14 functions, 4 classes)
📄 `project`
📄 `simple_generate` (1 functions)
📄 `trace` (1 functions)

## Requirements

- Python >= >=3.10
- typer >=0.12- rich >=13.0- pydantic >=2.0- pydantic-settings >=2.0- pydantic-yaml >=1.0- tomli >=2.0; python_version<'3.11'- httpx >=0.27- pyyaml >=6.0- requests >=2.31- docker >=6.0- psutil >=5.9- planfile >=0.1.30

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