# llx


**Intelligent LLM model router driven by real code metrics.**

[![PyPI](https://img.shields.io/pypi/v/llx)](https://pypi.org/project/llx/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

**Successor to [preLLM](https://github.com/wronai/prellm)** — rebuilt with modular architecture, no god modules, and metric-driven routing.

llx analyzes your codebase with **code2llm**, **redup**, and **vallm**, then selects the optimal LLM model based on actual project metrics — file count, complexity, coupling, duplication — not abstract scores.

**Principle**: larger + more coupled + more complex → stronger (and more expensive) model.

## Why llx? (Lessons from preLLM)

preLLM proved the concept but had architectural issues that llx resolves:

| Problem in preLLM | llx Solution |
|---|---|
| `cli.py`: 999 lines, CC=30 (`main`), CC=27 (`query`) | CLI split into `app.py` + `formatters.py`, max CC ≤ 8 |
| `core.py`: 893 lines god module | Config, analysis, routing in separate modules (≤250L each) |
| `trace.py`: 509 lines, CC=28 (`to_stdout`) | Output formatting as dedicated functions |
| Hardcoded model selection | Metric-driven thresholds from code2llm .toon data |
| No duplication/validation awareness | Integrates redup + vallm for richer metrics |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IDE / Agent Layer                        │
│  Roo Code │ Cline │ Continue.dev │ Aider │ Claude Code      │
│  (point at localhost:4000 as OpenAI-compatible API)         │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              LiteLLM Proxy (localhost:4000)                 │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ Router   │  │ Semantic     │  │ Cost Tracking      │     │
│  │ (metrics)│  │ Cache (Redis)│  │ + Budget Limits    │     │
│  └────┬─────┘  └──────────────┘  └────────────────────┘     │
└───────┼─────────────────────────────────────────────────────┘
        │
   ┌────┼────────────────────────────────────────┐
   │    │           Model Tiers                   │
   │    ├── premium:  Claude Opus 4               │
   │    ├── balanced: Claude Sonnet 4 / GPT-5     │
   │    ├── cheap:    Claude Haiku 4.5            │
   │    ├── free:     Gemini 2.5 Pro              │
   │    ├── openrouter: 300+ models (fallback)    │
   │    └── local:    Ollama (Qwen2.5-Coder)      │
   └──────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│            Code Analysis Pipeline                           │
│  code2llm → redup → vallm → llx                             │
│  (metrics → duplication → validation → model selection)     │
└─────────────────────────────────────────────────────────────┘
```

## MCP Server Integration

llx provides a complete **MCP (Model Context Protocol) server** that exposes analysis, preprocessing, and proxy-routing tools as MCP endpoints:

```bash
# Start MCP server for Claude Desktop
llx mcp start

# Generate Claude Desktop config
llx mcp config

# List available MCP tools
llx mcp tools
```

### MCP Tools Available

| Tool | Description |
|------|-------------|
| `llx_analyze` | Analyze a project and recommend the optimal model tier |
| `llx_select` | Quick model selection from existing analysis output |
| `llx_chat` | Analyze, select, and send a prompt with project context |
| `llx_preprocess` | Run the merged preLLM two-agent preprocessing pipeline |
| `llx_context` | Build shell, codebase, and sensitive-data context bundles |
| `code2llm_analyze` | Run code2llm static analysis and generate `.toon` files |
| `redup_scan` | Run duplication detection and emit a refactoring map |
| `vallm_validate` | Validate code or generated output with vallm |
| `llx_proxy_status` | Check LiteLLM proxy status |
| `llx_proxym_status` | Check Proxym routing status |
| `llx_proxym_chat` | Send a metrics-aware chat request through Proxym |

### Claude Desktop Setup

```json
{
  "mcpServers": {
    "llx": {
      "command": "python3",
      "args": ["-m", "llx.mcp.server"]
    }
  }
}
```

## Installation

```bash
pip install llx

# With integrations
pip install llx[all]         # Core integrations + MCP + Ollama
pip install llx[mcp]         # MCP server only
pip install llx[litellm]     # LiteLLM proxy
pip install llx[code2llm]    # Code analysis
pip install llx[redup]       # Duplication detection
pip install llx[vallm]       # Code validation
pip install llx[ollama]      # Local Ollama integration
pip install llx[prellm]      # Merged preLLM stack
pip install llx[prellm-full] # preLLM + optional context tooling
```

## Quick Start

```bash
# Analyze project and get model recommendation
llx analyze ./my-project

# Run code2llm/redup/vallm before selection
llx analyze . --run

# Quick model selection
llx select .

# With task hint
llx select . --task refactor

# Point to pre-existing .toon files
llx analyze . --toon-dir ./project/

# JSON output for CI/CD
llx analyze . --json

# Chat with auto-selected model
llx chat . --prompt "Refactor the god modules"

# Force local model
llx select . --local
```

## Model Selection Logic

| Metric | Premium (≥) | Balanced (≥) | Cheap (≥) | Free |
|--------|-------------|--------------|-----------|------|
| Files | 50 | 10 | 3 | <3 |
| Lines | 20,000 | 5,000 | 500 | <500 |
| Avg CC | 6.0 | 4.0 | 2.0 | <2.0 |
| Max fan-out | 30 | 10 | — | — |
| Max CC | 25 | 15 | — | — |
| Dup groups | 15 | 5 | — | — |
| Dep cycles | any | — | — | — |

## Real-World Selection Examples

| Project | Files | Lines | CC̄ | Max CC | Fan-out | Tier |
|---------|-------|-------|-----|--------|---------|------|
| Single script | 1 | 80 | 2.0 | 4 | 0 | **free** |
| Small CLI | 5 | 600 | 3.0 | 8 | 3 | **cheap** |
| **preLLM** | **31** | **8,900** | **5.0** | **28** | **30** | **premium** |
| vallm | 56 | 8,604 | 3.5 | 42 | — | **balanced** |
| code2llm | 113 | 21,128 | 4.6 | 65 | 45 | **premium** |
| Monorepo | 500+ | 100K+ | 5.0+ | 30+ | 50+ | **premium** |

## LiteLLM Proxy

```bash
llx proxy config     # Generate litellm_config.yaml
llx proxy start      # Start proxy (default :4000; override with --port or LLX_PROXY_PORT)
llx proxy status     # Check if running
```

Configure IDE tools to point at `http://localhost:4000`:

| Tool | Config |
|------|--------|
| Roo Code / Cline | `"apiBaseUrl": "http://localhost:4000/v1"` |
| Continue.dev | `"apiBaseUrl": "http://localhost:4000/v1"` |
| Aider | `OPENAI_API_BASE=http://localhost:4000` |
| Claude Code | `ANTHROPIC_BASE_URL=http://localhost:4000` |
| Cursor / Windsurf | OpenAI-compatible endpoint |

## Configuration

```bash
llx init  # Creates llx.toml with defaults
```

Environment variables: `LLX_LITELLM_URL`, `LLX_DEFAULT_TIER`, `LLX_PROXY_HOST`, `LLX_PROXY_PORT`, `LLX_PROXY_MASTER_KEY`, `LLX_VERBOSE`.

## Python API

```python
from llx import analyze_project, select_model, LlxConfig

metrics = analyze_project("./my-project")
result = select_model(metrics)
print(result.model_id)   # Selected model ID
print(result.explain())   # Human-readable reasoning
```

## Integration with wronai Toolchain

| Tool | Role | llx Uses |
|------|------|----------|
| [code2llm](https://github.com/wronai/code2llm) | Static analysis | CC, fan-out, cycles, hotspots |
| [redup](https://github.com/semcod/redup) | Duplication detection | Groups, recoverable lines |
| [vallm](https://github.com/semcod/vallm) | Code validation | Pass rate, issue count |
| **llx** | **Model routing + MCP server** | **Consumes all above** |

## Package Structure

```
llx/
├── __init__.py              # Public API
├── __main__.py              # `python -m llx`
├── analysis/                # Metrics collection and external tool runners
├── cli/                     # Typer CLI and output formatters
├── config.py                # Configuration loading and env overrides
├── integrations/            # Context builder, LiteLLM proxy, Proxym client
├── mcp/                     # MCP server and tool definitions
├── orchestration/           # Instances, routing, sessions, queues, VS Code
├── prellm/                  # Merged preLLM preprocessing pipeline
├── routing/                 # Model selection and LLM client wrappers
├── tools/                   # Utility CLIs and helper commands
└── litellm_config.py        # LiteLLM config helpers
```

The library stays split into small, composable modules. The merged preLLM code now lives under `llx/prellm/`, and orchestration / VS Code / instance-management code lives under `llx/orchestration/`.

## Architecture Improvements (v0.1.7)

- **✅ Refactored 6 high-CC functions** to meet targets (CC̄ ≤ 2.5, max CC ≤ 16)
- **✅ Added complete MCP server** with 11 tools for Claude Desktop integration
- **✅ Added Proxym integration** for metrics-aware routing and proxy status checks
- **✅ Fixed import resolution issues** reported by vallm
- **✅ Enhanced test coverage** for MCP functionality
- **✅ Modular design** with single-responsibility functions

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
