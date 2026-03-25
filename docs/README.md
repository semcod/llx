<!-- code2docs:start --># llx

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-104-green)
> **104** functions | **14** classes | **28** files | CC̄ = 4.7

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
├── llx/    ├── __main__    ├── analysis/    ├── config        ├── collector    ├── cli/        ├── runner        ├── formatters    ├── integrations/        ├── proxy    ├── routing/        ├── client        ├── main        ├── main        ├── main        ├── main        ├── main├── docker-manage├── project        ├── entrypoint        ├── run        ├── run        ├── run        ├── run        ├── run    ├── litellm_config        ├── app        ├── selector```

## API Overview

### Classes

- **`ModelConfig`** — Configuration for a single model tier.
- **`TierThresholds`** — Thresholds that determine which model tier to use.
- **`ProxyConfig`** — LiteLLM proxy settings.
- **`LlxConfig`** — Root configuration for llx.
- **`ProjectMetrics`** — Aggregated project metrics that drive model selection.
- **`ToolResult`** — —
- **`ChatMessage`** — A single chat message.
- **`ChatResponse`** — Response from LLM completion.
- **`LlxClient`** — LLM client that routes through LiteLLM proxy or calls directly.
- **`ProxyExample`** — —
- **`LiteLLMModelConfig`** — Configuration for a single LiteLLM model.
- **`LiteLLMConfig`** — Complete LiteLLM configuration.
- **`ModelTier`** — LLM model tiers ranked by capability and cost.
- **`SelectionResult`** — Result of model selection with explanation.

### Functions

- `analyze_project(project_path)` — Collect all available metrics for a project.
- `check_tool(name)` — Check if a CLI tool is available on PATH.
- `run_code2llm(project_path, output_dir, fmt)` — —
- `run_redup(project_path, output_dir, fmt)` — —
- `run_vallm(project_path, output_dir)` — —
- `run_all_tools(project_path, output_dir, on_progress)` — —
- `output_rich(metrics, result, verbose)` — Rich terminal output for analysis results.
- `output_json(metrics, result)` — JSON output for machine consumption.
- `print_models_table(config, tag, provider, tier)` — Print models table with optional filtering.
- `print_info_tables(config)` — Print tools and models info tables.
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
- `print_warning()` — —
- `print_error()` — —
- `check_docker()` — —
- `check_compose()` — —
- `get_compose_cmd()` — —
- `load_litellm_config(project_path)` — Convenience function to load LiteLLM configuration.
- `analyze(path, toon_dir, task, local)` — Analyze a project and recommend the optimal LLM model.
- `select(path, toon_dir, task, local)` — Quick model selection from existing analysis files.
- `chat(path, prompt, toon_dir, task)` — Analyze project, select model, and send a prompt.
- `proxy_start(config_path, port, background)` — Start LiteLLM proxy server with llx configuration.
- `proxy_config(output)` — Generate LiteLLM proxy config.
- `proxy_status()` — Check if proxy is running.
- `models(tag, provider, tier)` — Show available models with optional filtering by tags, provider, or tier.
- `info()` — Show available tools, models, and configuration.
- `init(path)` — Initialize llx.toml configuration file.
- `main()` — —
- `select_model(metrics, config)` — Select the best model tier based on project metrics.
- `check_context_fit(metrics, model)` — Check if the project context fits within the model's context window.
- `select_with_context_check(metrics, config)` — Select model and verify context window fit.


## Project Structure

📄 `docker-manage` (7 functions)
📄 `docker.ollama.entrypoint`
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
📦 `llx`
📄 `llx.__main__`
📦 `llx.analysis`
📄 `llx.analysis.collector` (14 functions, 1 classes)
📄 `llx.analysis.runner` (6 functions, 1 classes)
📦 `llx.cli`
📄 `llx.cli.app` (11 functions)
📄 `llx.cli.formatters` (4 functions)
📄 `llx.config` (4 functions, 4 classes)
📦 `llx.integrations`
📄 `llx.integrations.proxy` (3 functions)
📄 `llx.litellm_config` (10 functions, 2 classes)
📦 `llx.routing`
📄 `llx.routing.client` (9 functions, 3 classes)
📄 `llx.routing.selector` (6 functions, 2 classes)
📄 `project`

## Requirements

- Python >= >=3.10
- typer >=0.12- rich >=13.0- pydantic >=2.0- pydantic-settings >=2.0- tomli >=2.0; python_version<'3.11'- httpx >=0.27- pyyaml >=6.0

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