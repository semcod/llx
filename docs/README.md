<!-- code2docs:start --># llx

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-834-green)
> **834** functions | **148** classes | **88** files | CC̄ = 4.8

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
    ├── __main__├── llx/        ├── env_config        ├── cli        ├── model_catalog    ├── config        ├── trace    ├── prellm/    ├── litellm_config        ├── prompt_registry        ├── validators        ├── models        ├── query_decomposer        ├── server        ├── llm_provider        ├── core        ├── pipeline    ├── analysis/        ├── runner        ├── budget        ├── collector        ├── ai_tools_manager        ├── cli        ├── vscode_manager    ├── tools/        ├── config_manager        ├── model_manager        ├── app    ├── cli/        ├── docker_manager        ├── llm_orchestrator        ├── health_checker        ├── formatters    ├── orchestration/        ├── routing_engine        ├── rate_limiter        ├── orchestrator_cli        ├── instance_manager        ├── queue_manager        ├── tools        ├── server    ├── mcp/        ├── __main__        ├── session_manager    ├── integrations/        ├── proxy    ├── routing/        ├── vscode_orchestrator        ├── client        ├── chains/        ├── proxym        ├── utils/            ├── lazy_imports            ├── lazy_loader        ├── selector            ├── process_chain            ├── shell_collector            ├── folder_compressor        ├── context/            ├── sensitive_filter            ├── user_memory        ├── analyzers/            ├── codebase_indexer            ├── preprocessor        ├── agents/            ├── context_engine            ├── schema_generator            ├── executor        ├── main        ├── main        ├── main        ├── main        ├── demo├── ai-tools-manage├── docker-manage├── project        ├── entrypoint        ├── main        ├── main        ├── install-extensions        ├── run        ├── entrypoint        ├── run        ├── run        ├── install-tools        ├── run        ├── run        ├── logging_setup```

## API Overview

### Classes

- **`EnvConfig`** — Resolved environment configuration.
- **`ModelConfig`** — Configuration for a single model tier.
- **`TierThresholds`** — Thresholds that determine which model tier to use.
- **`ProxyConfig`** — LiteLLM proxy settings.
- **`LlxConfig`** — Root configuration for llx.
- **`TraceStep`** — A single recorded step in the execution trace.
- **`TraceRecorder`** — Records execution trace and generates markdown documentation.
- **`LiteLLMModelConfig`** — Configuration for a single LiteLLM model.
- **`LiteLLMConfig`** — Complete LiteLLM configuration.
- **`PromptNotFoundError`** — Raised when a prompt name is not found in the registry.
- **`PromptRenderError`** — Raised when a prompt template fails to render.
- **`PromptEntry`** — Single prompt entry with template, max_tokens, and temperature.
- **`PromptRegistry`** — Loads prompts from YAML, caches, validates placeholders.
- **`ValidationResult`** — Result of validating data against a schema.
- **`SchemaDefinition`** — Parsed schema definition from YAML.
- **`ResponseValidator`** — Validates LLM responses against YAML-defined schemas.
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
- **`LLMProvider`** — Unified LLM caller with retry and fallback support.
- **`PreLLM`** — preLLM v0.2/v0.3 — small LLM decomposition before large LLM routing.
- **`PipelineStep`** — Configuration for a single pipeline step.
- **`PipelineConfig`** — Configuration for a complete pipeline.
- **`StepExecutionResult`** — Result of executing a single pipeline step.
- **`PipelineResult`** — Result of executing a full pipeline.
- **`PromptPipeline`** — Generic pipeline — executes a sequence of LLM + algorithmic steps.
- **`ToolResult`** — —
- **`BudgetExceededError`** — Raised when the monthly budget limit has been reached.
- **`UsageEntry`** — Single API call cost record.
- **`BudgetTracker`** — Tracks LLM API spend against a monthly budget.
- **`ProjectMetrics`** — Aggregated project metrics that drive model selection.
- **`AIToolsManager`** — Manages AI tools container and operations.
- **`LLXToolsCLI`** — Unified CLI for llx ecosystem management.
- **`VSCodeManager`** — Manages VS Code server with AI extensions.
- **`ConfigManager`** — Manages llx configuration files and settings.
- **`ModelManager`** — Manages local Ollama models and llx configurations.
- **`DockerManager`** — Manages Docker containers for llx ecosystem.
- **`LLMProviderType`** — Types of LLM providers.
- **`ModelCapability`** — Model capabilities.
- **`LLMModel`** — LLM model configuration.
- **`LLMProvider`** — LLM provider configuration.
- **`LLMRequest`** — LLM request.
- **`LLMResponse`** — LLM response.
- **`LLMOrchestrator`** — Orchestrates multiple LLM providers and models with intelligent routing.
- **`HealthChecker`** — Comprehensive health monitoring for llx ecosystem.
- **`RoutingStrategy`** — Routing strategies.
- **`ResourceType`** — Types of resources to route to.
- **`RoutingRequest`** — A request to be routed.
- **`RoutingDecision`** — A routing decision.
- **`RoutingMetrics`** — Metrics for routing performance.
- **`RoutingEngine`** — Intelligent routing engine for LLM and VS Code requests.
- **`LimitType`** — Types of rate limits.
- **`RateLimitConfig`** — Configuration for rate limiting.
- **`RateLimitState`** — Current state of rate limiting.
- **`RateLimiter`** — Manages rate limiting for multiple providers and accounts.
- **`OrchestratorCLI`** — Unified CLI for llx orchestration system.
- **`InstanceType`** — Types of instances.
- **`InstanceStatus`** — Instance status.
- **`InstanceConfig`** — Configuration for an instance.
- **`InstanceState`** — Current state of an instance.
- **`InstanceManager`** — Manages multiple Docker instances with intelligent allocation and monitoring.
- **`PortAllocator`** — Manages port allocation for instances.
- **`QueueStatus`** — Queue status.
- **`RequestPriority`** — Request priority levels.
- **`QueueRequest`** — A request in the queue.
- **`QueueConfig`** — Configuration for a queue.
- **`QueueState`** — Current state of a queue.
- **`QueueManager`** — Manages multiple request queues with intelligent prioritization.
- **`McpTool`** — —
- **`SessionType`** — Types of sessions.
- **`SessionStatus`** — Session status.
- **`SessionConfig`** — Configuration for a session.
- **`SessionState`** — Current state of a session.
- **`SessionManager`** — Manages multiple LLM and VS Code sessions with intelligent routing.
- **`VSCodeAccountType`** — Types of VS Code accounts.
- **`VSCodeAccount`** — VS Code account configuration.
- **`VSCodeInstanceConfig`** — Configuration for a VS Code instance.
- **`VSCodeSession`** — Active VS Code session.
- **`VSCodeOrchestrator`** — Orchestrates multiple VS Code instances with intelligent management.
- **`VSCodePortAllocator`** — Manages port allocation for VS Code instances.
- **`ChatMessage`** — A single chat message.
- **`ChatResponse`** — Response from LLM completion.
- **`LlxClient`** — LLM client that routes through LiteLLM proxy or calls directly.
- **`ProxymStatus`** — Status of the proxym proxy server.
- **`ProxymResponse`** — Response from proxym chat completion.
- **`ProxymClient`** — Client for proxym intelligent AI proxy.
- **`LazyLoader`** — Base class for components that need lazy loading of resources.
- **`ModelTier`** — LLM model tiers ranked by capability and cost.
- **`SelectionResult`** — Result of model selection with explanation.
- **`ProcessChain`** — Execute multi-step DevOps workflows with preLLM validation at each step.
- **`ShellContextCollector`** — Collects full shell environment context for LLM prompt enrichment.
- **`FolderCompressor`** — Compresses a project folder into a lightweight representation for LLM context.
- **`SensitiveDataFilter`** — Classifies and filters sensitive data from context before LLM calls.
- **`UserMemory`** — Stores user query history and learned preferences.
- **`CodeSymbol`** — A code symbol extracted from source.
- **`FileIndex`** — Index of a single source file.
- **`CodebaseIndex`** — Full codebase index.
- **`CodebaseIndexer`** — Index a codebase using tree-sitter for AST-based symbol extraction.
- **`PreprocessResult`** — Output of the PreprocessorAgent — structured input for the ExecutorAgent.
- **`PreprocessorAgent`** — Agent preprocessing — small LLM (≤24B) analyzes and structures queries.
- **`ContextEngine`** — Collects context from environment, git, and system for prompt enrichment.
- **`ContextSchemaGenerator`** — Generates a structured context schema from available context sources.
- **`ExecutorResult`** — Output of the ExecutorAgent.
- **`ExecutorAgent`** — Agent execution — large LLM (>24B) executes structured tasks.
- **`ProxyExample`** — —
- **`RooCodeDemo`** — Demo class for RooCode AI assistant capabilities.

### Functions

- `load_dotenv_if_available(path)` — Load .env file if it exists. No dependency on python-dotenv — just basic parsing.
- `get_env_config(dotenv_path)` — Read all config from environment variables (LiteLLM-compatible).
- `check_providers(env)` — Check which providers are configured and reachable.
- `resolve_alias(key)` — Resolve a user-friendly alias to an env var name.
- `mask_value(key, value)` — Mask secret values for display.
- `config_set(key, value, global_)` — Set a config value persistently in .env file.
- `config_get(key, global_)` — Get a config value. Checks: env var → project .env → global .env → None.
- `config_list(global_, show_secrets)` — List all config values from .env files and environment.
- `check_providers_live(env)` — Check providers with live connectivity tests.
- `query(prompt, small, large, strategy)` — Preprocess a query with small LLM, then execute with large LLM.
- `context(json_output, schema, blocked, folder)` — Show collected environment context, schema, and blocked sensitive data.
- `process(config, guard_config, dry_run, json_output)` — Execute a DevOps process chain.
- `decompose(query, config, strategy, json_output)` — [v0.2] Decompose a query using small LLM without calling the large model.
- `init(output, devops)` — Generate a starter preLLM config file.
- `serve(host, port, small, large)` — Start the OpenAI-compatible API server.
- `doctor(env_file, live)` — Check configuration and provider connectivity.
- `config_set_cmd(key, value, global_)` — Set a config value persistently.
- `config_get_cmd(key, raw)` — Get a config value.
- `config_list_cmd(raw)` — List all configured values.
- `config_show_cmd()` — Show effective configuration (resolved from all sources).
- `config_init_env(global_, force)` — Generate a starter .env file with all available settings.
- `budget(reset, json_output)` — Show LLM API spend tracking and budget status.
- `models(provider, search)` — List popular model pairs and provider examples.
- `context_show_cmd(json_output, blocked, codebase)` — Show collected runtime context.
- `session_list_cmd(memory)` — List recent interactions in the session.
- `session_export_cmd(output, memory, session_id)` — Export current session to JSON file.
- `session_import_cmd(input_file, memory)` — Import a session from JSON file.
- `session_clear_cmd(memory, force)` — Clear all session data.
- `list_model_pairs(provider, search)` — Filter model pairs by provider and/or search term. Pure function — no IO.
- `list_openrouter_models(provider, search)` — Filter OpenRouter models by provider and/or search term. Pure function — no IO.
- `get_current_trace()` — Get the active trace recorder for the current execution context.
- `set_current_trace(trace)` — Set the active trace recorder for the current execution context.
- `load_litellm_config(project_path)` — Convenience function to load LiteLLM configuration.
- `health()` — —
- `list_models()` — List available model pairs.
- `chat_completions(req)` — OpenAI-compatible chat completions with preLLM preprocessing.
- `batch_process(items)` — Process multiple queries in parallel.
- `create_app(small_model, large_model, strategy, config_path)` — Factory function to create a configured preLLM API server.
- `preprocess_and_execute(query, small_llm, large_llm, strategy)` — One function to preprocess and execute — like litellm.completion() but with small LLM decomposition.
- `preprocess_and_execute_sync(query, small_llm, large_llm, strategy)` — Synchronous version of preprocess_and_execute() — runs the async function in an event loop.
- `check_tool(name)` — Check if a CLI tool is available on PATH.
- `run_code2llm(project_path, output_dir, fmt)` — —
- `run_redup(project_path, output_dir, fmt)` — —
- `run_vallm(project_path, output_dir)` — —
- `run_all_tools(project_path, output_dir, on_progress)` — —
- `get_budget_tracker(monthly_limit, persist_path)` — Get or create the global budget tracker singleton.
- `reset_budget_tracker()` — Reset the global tracker (for testing).
- `analyze_project(project_path)` — Collect all available metrics for a project.
- `main()` — CLI interface for AI tools manager.
- `main()` — Main CLI entry point.
- `main()` — CLI interface for VS Code manager.
- `main()` — CLI interface for config manager.
- `main()` — CLI interface for model manager.
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
- `main()` — —
- `main()` — CLI interface for Docker manager.
- `main()` — CLI interface for LLM orchestrator.
- `main()` — CLI interface for health checker.
- `output_rich(metrics, result, verbose)` — Rich terminal output for analysis results.
- `output_json(metrics, result)` — JSON output for machine consumption.
- `print_models_table(config, tag, provider, tier)` — Print models table with optional filtering.
- `print_info_tables(config)` — Print tools and models info tables.
- `main()` — CLI interface for routing engine.
- `main()` — CLI interface for rate limiter.
- `main()` — Main CLI entry point.
- `main()` — CLI interface for instance manager.
- `main()` — CLI interface for queue manager.
- `list_tools()` — —
- `call_tool(name, arguments)` — —
- `main()` — —
- `main_sync()` — Synchronous entry point for CLI.
- `main()` — CLI interface for session manager.
- `generate_proxy_config(config, output_path)` — Generate a LiteLLM proxy config YAML.
- `start_proxy(config)` — Start LiteLLM proxy server.
- `check_proxy(base_url)` — Check if LiteLLM proxy is running.
- `main()` — CLI interface for VS Code orchestrator.
- `lazy_import_global(name, import_path, globals_dict)` — Lazy import a global object.
- `select_model(metrics, config)` — Select the best model tier based on project metrics.
- `check_context_fit(metrics, model)` — Check if the project context fits within the model's context window.
- `select_with_context_check(metrics, config)` — Select model and verify context window fit.
- `signal_handler(signum, frame)` — Handle shutdown signals
- `main()` — Main proxy example execution
- `check_provider_keys()` — Check which provider API keys are available
- `compare_provider_costs()` — Compare costs across available providers
- `demonstrate_fallback_strategy()` — Demonstrate provider fallback strategy
- `simulate_multi_provider_selection()` — Simulate model selection across different providers
- `main()` — Main multi-provider example execution
- `check_service_health(service_name, url, timeout)` — Check if a service is healthy
- `check_redis_connection()` — Check Redis connection
- `check_ollama_connection()` — Check Ollama connection
- `demonstrate_docker_integration()` — Demonstrate llx integration with Docker services
- `demonstrate_redis_usage(redis_client)` — Demonstrate Redis caching with llx
- `demonstrate_ollama_integration(ollama_models)` — Demonstrate Ollama integration with llx
- `demonstrate_container_metrics()` — Demonstrate collecting container metrics
- `demonstrate_service_discovery()` — Demonstrate service discovery in Docker network
- `main()` — Main Docker integration example
- `check_ollama_installation()` — Check if Ollama is installed and running
- `check_ollama_service()` — Check if Ollama service is running
- `list_recommended_local_models()` — List recommended local models for different use cases
- `demonstrate_local_model_selection()` — Demonstrate model selection with local models
- `show_ollama_setup_instructions()` — Show instructions for setting up Ollama
- `estimate_resource_requirements()` — Estimate resource requirements for local models
- `main()` — Main local models example execution
- `main()` — Main demonstration function.
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
- `check_docker_services()` — Check if Docker services are running
- `get_available_models()` — Get available models from Ollama
- `test_ai_tools_container()` — Test AI tools container functionality
- `demonstrate_aider()` — Demonstrate Aider usage
- `demonstrate_claude_code()` — Demonstrate Claude Code usage
- `demonstrate_cursor()` — Demonstrate Cursor usage
- `test_chat_completion()` — Test chat completion through AI tools
- `show_usage_examples()` — Show usage examples for AI tools
- `main()` — —
- `main()` — Main example execution
- `is_extension_installed()` — —
- `install_extension()` — —
- `hello_world()` — —
- `print()` — —
- `setup_logging(level, markdown_file, terminal_format)` — Initialize nfo logging for the entire preLLM project.
- `get_logger(name)` — Get or create the nfo logger.


## Project Structure

📄 `ai-tools-manage` (15 functions)
📄 `docker-manage` (7 functions)
📄 `docker.ai-tools.entrypoint` (3 functions)
📄 `docker.ai-tools.install-tools`
📄 `docker.ollama.entrypoint`
📄 `docker.vscode.install-extensions` (2 functions)
📄 `examples.ai-tools.main` (9 functions)
📄 `examples.basic.main` (1 functions)
📄 `examples.basic.run`
📄 `examples.docker.main` (9 functions)
📄 `examples.docker.run`
📄 `examples.local.main` (7 functions)
📄 `examples.local.run`
📄 `examples.multi-provider.main` (5 functions)
📄 `examples.multi-provider.run`
📄 `examples.proxy.main` (8 functions, 1 classes)
📄 `examples.proxy.run`
📄 `examples.vscode-roocode.demo` (11 functions, 1 classes)
📦 `llx`
📄 `llx.__main__`
📦 `llx.analysis`
📄 `llx.analysis.collector` (21 functions, 1 classes)
📄 `llx.analysis.runner` (6 functions, 1 classes)
📦 `llx.cli`
📄 `llx.cli.app` (14 functions)
📄 `llx.cli.formatters` (12 functions)
📄 `llx.config` (7 functions, 4 classes)
📦 `llx.integrations`
📄 `llx.integrations.proxy` (3 functions)
📄 `llx.integrations.proxym` (12 functions, 3 classes)
📄 `llx.litellm_config` (10 functions, 2 classes)
📦 `llx.mcp`
📄 `llx.mcp.__main__`
📄 `llx.mcp.server` (4 functions)
📄 `llx.mcp.tools` (11 functions, 1 classes)
📦 `llx.orchestration`
📄 `llx.orchestration.instance_manager` (24 functions, 6 classes)
📄 `llx.orchestration.llm_orchestrator` (33 functions, 7 classes)
📄 `llx.orchestration.orchestrator_cli` (22 functions, 1 classes)
📄 `llx.orchestration.queue_manager` (23 functions, 6 classes)
📄 `llx.orchestration.rate_limiter` (18 functions, 4 classes)
📄 `llx.orchestration.routing_engine` (39 functions, 6 classes)
📄 `llx.orchestration.session_manager` (21 functions, 5 classes)
📄 `llx.orchestration.vscode_orchestrator` (32 functions, 6 classes)
📦 `llx.prellm` (1 functions)
📦 `llx.prellm.agents`
📄 `llx.prellm.agents.executor` (3 functions, 2 classes)
📄 `llx.prellm.agents.preprocessor` (6 functions, 2 classes)
📦 `llx.prellm.analyzers`
📄 `llx.prellm.analyzers.context_engine` (13 functions, 1 classes)
📄 `llx.prellm.budget` (11 functions, 3 classes)
📦 `llx.prellm.chains`
📄 `llx.prellm.chains.process_chain` (10 functions, 1 classes)
📄 `llx.prellm.cli` (28 functions)
📦 `llx.prellm.context`
📄 `llx.prellm.context.codebase_indexer` (14 functions, 4 classes)
📄 `llx.prellm.context.folder_compressor` (10 functions, 1 classes)
📄 `llx.prellm.context.schema_generator` (9 functions, 1 classes)
📄 `llx.prellm.context.sensitive_filter` (14 functions, 1 classes)
📄 `llx.prellm.context.shell_collector` (8 functions, 1 classes)
📄 `llx.prellm.context.user_memory` (15 functions, 1 classes)
📄 `llx.prellm.core` (32 functions, 1 classes)
📄 `llx.prellm.env_config` (17 functions, 1 classes)
📄 `llx.prellm.llm_provider` (6 functions, 1 classes)
📄 `llx.prellm.logging_setup` (3 functions)
📄 `llx.prellm.model_catalog` (2 functions)
📄 `llx.prellm.models` (2 functions, 33 classes)
📄 `llx.prellm.pipeline` (18 functions, 5 classes)
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
📄 `llx.tools.ai_tools_manager` (20 functions, 1 classes)
📄 `llx.tools.cli` (15 functions, 1 classes)
📄 `llx.tools.config_manager` (25 functions, 1 classes)
📄 `llx.tools.docker_manager` (19 functions, 1 classes)
📄 `llx.tools.health_checker` (13 functions, 1 classes)
📄 `llx.tools.model_manager` (20 functions, 1 classes)
📄 `llx.tools.vscode_manager` (23 functions, 1 classes)
📄 `project`

## Requirements

- Python >= >=3.10
- typer >=0.12- rich >=13.0- pydantic >=2.0- pydantic-settings >=2.0- tomli >=2.0; python_version<'3.11'- httpx >=0.27- pyyaml >=6.0- requests >=2.31- docker >=6.0- psutil >=5.9

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