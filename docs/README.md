<!-- code2docs:start --># llx

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-482-green)
> **482** functions | **57** classes | **55** files | CC̄ = 4.9

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
    ├── __main__├── llx/    ├── analysis/        ├── collector    ├── config        ├── ai_tools_manager        ├── cli        ├── runner    ├── tools/        ├── vscode_manager        ├── config_manager        ├── health_checker    ├── cli/        ├── model_manager        ├── formatters    ├── litellm_config    ├── orchestration/        ├── rate_limiter        ├── orchestrator_cli        ├── app        ├── vscode_orchestrator        ├── routing_engine        ├── llm_orchestrator        ├── tools    ├── mcp/        ├── server        ├── __main__    ├── integrations/    ├── routing/        ├── proxy        ├── client        ├── main        ├── main        ├── queue_manager        ├── selector        ├── main        ├── main        ├── main├── ai-tools-manage├── docker-manage├── project        ├── entrypoint        ├── install-extensions        ├── entrypoint        ├── main        ├── install-tools        ├── run        ├── run        ├── run        ├── run        ├── run        ├── demo        ├── session_manager```

## API Overview

### Classes

- **`ProjectMetrics`** — Aggregated project metrics that drive model selection.
- **`ModelConfig`** — Configuration for a single model tier.
- **`TierThresholds`** — Thresholds that determine which model tier to use.
- **`ProxyConfig`** — LiteLLM proxy settings.
- **`LlxConfig`** — Root configuration for llx.
- **`AIToolsManager`** — Manages AI tools container and operations.
- **`LLXToolsCLI`** — Unified CLI for llx ecosystem management.
- **`ToolResult`** — —
- **`VSCodeManager`** — Manages VS Code server with AI extensions.
- **`ConfigManager`** — Manages llx configuration files and settings.
- **`HealthChecker`** — Comprehensive health monitoring for llx ecosystem.
- **`ModelManager`** — Manages local Ollama models and llx configurations.
- **`LiteLLMModelConfig`** — Configuration for a single LiteLLM model.
- **`LiteLLMConfig`** — Complete LiteLLM configuration.
- **`LimitType`** — Types of rate limits.
- **`RateLimitConfig`** — Configuration for rate limiting.
- **`RateLimitState`** — Current state of rate limiting.
- **`RateLimiter`** — Manages rate limiting for multiple providers and accounts.
- **`OrchestratorCLI`** — Unified CLI for llx orchestration system.
- **`VSCodeAccountType`** — Types of VS Code accounts.
- **`VSCodeAccount`** — VS Code account configuration.
- **`VSCodeInstanceConfig`** — Configuration for a VS Code instance.
- **`VSCodeSession`** — Active VS Code session.
- **`VSCodeOrchestrator`** — Orchestrates multiple VS Code instances with intelligent management.
- **`VSCodePortAllocator`** — Manages port allocation for VS Code instances.
- **`RoutingStrategy`** — Routing strategies.
- **`ResourceType`** — Types of resources to route to.
- **`RoutingRequest`** — A request to be routed.
- **`RoutingDecision`** — A routing decision.
- **`RoutingMetrics`** — Metrics for routing performance.
- **`RoutingEngine`** — Intelligent routing engine for LLM and VS Code requests.
- **`LLMProviderType`** — Types of LLM providers.
- **`ModelCapability`** — Model capabilities.
- **`LLMModel`** — LLM model configuration.
- **`LLMProvider`** — LLM provider configuration.
- **`LLMRequest`** — LLM request.
- **`LLMResponse`** — LLM response.
- **`LLMOrchestrator`** — Orchestrates multiple LLM providers and models with intelligent routing.
- **`McpTool`** — —
- **`ChatMessage`** — A single chat message.
- **`ChatResponse`** — Response from LLM completion.
- **`LlxClient`** — LLM client that routes through LiteLLM proxy or calls directly.
- **`ProxyExample`** — —
- **`QueueStatus`** — Queue status.
- **`RequestPriority`** — Request priority levels.
- **`QueueRequest`** — A request in the queue.
- **`QueueConfig`** — Configuration for a queue.
- **`QueueState`** — Current state of a queue.
- **`QueueManager`** — Manages multiple request queues with intelligent prioritization.
- **`ModelTier`** — LLM model tiers ranked by capability and cost.
- **`SelectionResult`** — Result of model selection with explanation.
- **`RooCodeDemo`** — Demo class for RooCode AI assistant capabilities.
- **`SessionType`** — Types of sessions.
- **`SessionStatus`** — Session status.
- **`SessionConfig`** — Configuration for a session.
- **`SessionState`** — Current state of a session.
- **`SessionManager`** — Manages multiple LLM and VS Code sessions with intelligent routing.

### Functions

- `analyze_project(project_path)` — Collect all available metrics for a project.
- `main()` — CLI interface for AI tools manager.
- `main()` — Main CLI entry point.
- `check_tool(name)` — Check if a CLI tool is available on PATH.
- `run_code2llm(project_path, output_dir, fmt)` — —
- `run_redup(project_path, output_dir, fmt)` — —
- `run_vallm(project_path, output_dir)` — —
- `run_all_tools(project_path, output_dir, on_progress)` — —
- `main()` — CLI interface for VS Code manager.
- `main()` — CLI interface for config manager.
- `main()` — CLI interface for health checker.
- `main()` — CLI interface for model manager.
- `output_rich(metrics, result, verbose)` — Rich terminal output for analysis results.
- `output_json(metrics, result)` — JSON output for machine consumption.
- `print_models_table(config, tag, provider, tier)` — Print models table with optional filtering.
- `print_info_tables(config)` — Print tools and models info tables.
- `load_litellm_config(project_path)` — Convenience function to load LiteLLM configuration.
- `main()` — CLI interface for rate limiter.
- `main()` — Main CLI entry point.
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
- `main()` — CLI interface for VS Code orchestrator.
- `main()` — CLI interface for routing engine.
- `main()` — CLI interface for LLM orchestrator.
- `list_tools()` — —
- `call_tool(name, arguments)` — —
- `main()` — —
- `main_sync()` — Synchronous entry point for CLI.
- `generate_proxy_config(config, output_path)` — Generate a LiteLLM proxy config YAML.
- `start_proxy(config)` — Start LiteLLM proxy server.
- `check_proxy(base_url)` — Check if LiteLLM proxy is running.
- `signal_handler(signum, frame)` — Handle shutdown signals
- `main()` — Main proxy example execution
- `check_service_health(service_name, url, timeout)` — Check if a service is healthy
- `check_redis_connection()` — Check Redis connection
- `check_ollama_connection()` — Check Ollama connection
- `demonstrate_docker_integration()` — Demonstrate llx integration with Docker services
- `demonstrate_redis_usage(redis_client)` — Demonstrate Redis caching with llx
- `demonstrate_ollama_integration(ollama_models)` — Demonstrate Ollama integration with llx
- `demonstrate_container_metrics()` — Demonstrate collecting container metrics
- `demonstrate_service_discovery()` — Demonstrate service discovery in Docker network
- `main()` — Main Docker integration example
- `main()` — CLI interface for queue manager.
- `select_model(metrics, config)` — Select the best model tier based on project metrics.
- `check_context_fit(metrics, model)` — Check if the project context fits within the model's context window.
- `select_with_context_check(metrics, config)` — Select model and verify context window fit.
- `check_provider_keys()` — Check which provider API keys are available
- `compare_provider_costs()` — Compare costs across available providers
- `demonstrate_fallback_strategy()` — Demonstrate provider fallback strategy
- `simulate_multi_provider_selection()` — Simulate model selection across different providers
- `main()` — Main multi-provider example execution
- `check_ollama_installation()` — Check if Ollama is installed and running
- `check_ollama_service()` — Check if Ollama service is running
- `list_recommended_local_models()` — List recommended local models for different use cases
- `demonstrate_local_model_selection()` — Demonstrate model selection with local models
- `show_ollama_setup_instructions()` — Show instructions for setting up Ollama
- `estimate_resource_requirements()` — Estimate resource requirements for local models
- `main()` — Main local models example execution
- `main()` — Main example execution
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
- `is_extension_installed()` — —
- `install_extension()` — —
- `hello_world()` — —
- `print()` — —
- `check_docker_services()` — Check if Docker services are running
- `get_available_models()` — Get available models from Ollama
- `test_ai_tools_container()` — Test AI tools container functionality
- `demonstrate_aider()` — Demonstrate Aider usage
- `demonstrate_claude_code()` — Demonstrate Claude Code usage
- `demonstrate_cursor()` — Demonstrate Cursor usage
- `test_chat_completion()` — Test chat completion through AI tools
- `show_usage_examples()` — Show usage examples for AI tools
- `main()` — —
- `main()` — Main demonstration function.
- `main()` — CLI interface for session manager.


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
📄 `llx.litellm_config` (10 functions, 2 classes)
📦 `llx.mcp`
📄 `llx.mcp.__main__`
📄 `llx.mcp.server` (4 functions)
📄 `llx.mcp.tools` (7 functions, 1 classes)
📦 `llx.orchestration`
📄 `llx.orchestration.llm_orchestrator` (33 functions, 7 classes)
📄 `llx.orchestration.orchestrator_cli` (22 functions, 1 classes)
📄 `llx.orchestration.queue_manager` (23 functions, 6 classes)
📄 `llx.orchestration.rate_limiter` (18 functions, 4 classes)
📄 `llx.orchestration.routing_engine` (39 functions, 6 classes)
📄 `llx.orchestration.session_manager` (21 functions, 5 classes)
📄 `llx.orchestration.vscode_orchestrator` (32 functions, 6 classes)
📦 `llx.routing`
📄 `llx.routing.client` (9 functions, 3 classes)
📄 `llx.routing.selector` (9 functions, 2 classes)
📦 `llx.tools`
📄 `llx.tools.ai_tools_manager` (20 functions, 1 classes)
📄 `llx.tools.cli` (15 functions, 1 classes)
📄 `llx.tools.config_manager` (25 functions, 1 classes)
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