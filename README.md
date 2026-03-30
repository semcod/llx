![img.png](img.png)

# llx

**Intelligent LLM model router driven by real code metrics.**

[![PyPI](https://img.shields.io/pypi/v/llx)](https://pypi.org/project/llx/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.46-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$6.15-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-11.9h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $6.1500 (41 commits)
- 👤 **Human dev:** ~$1192 (11.9h @ $100/h, 30min dedup)

Generated on 2026-03-29 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---



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

## MCP Server Integration (NEW)

llx now provides a complete **MCP (Model Context Protocol) server** that exposes all wronai tools as MCP endpoints:

By default, the MCP server runs over **stdio** for Claude Desktop. If you need to connect from a web client or another process, start the SSE server explicitly and use the `/sse` and `/messages/` endpoints.

```bash
# Start MCP server for Claude Desktop (stdio)
llx mcp start

# Start MCP server over SSE for web/remote clients
llx mcp start --mode sse --port 8000

# SSE endpoint: http://localhost:8000/sse
# Message endpoint: http://localhost:8000/messages/

# Generate Claude Desktop config
llx mcp config

# List available MCP tools
llx mcp tools
```

### SSE / HTTP clients

For clients like `pyqual` that expect an HTTP SSE endpoint, start llx in SSE mode:

```bash
llx mcp start --mode sse --port 8000
# or
python -m llx.mcp --sse --port 8000
```

Then point the client at:

```text
http://localhost:8000/sse
```

### MCP Tools Available

| Tool | Description | Wraps |
|------|-------------|-------|
| `llx_analyze` | Analyze project and recommend model | `llx analyze` |
| `llx_select` | Quick model selection | `llx select` |
| `llx_chat` | Analyze + select model + send prompt | `llx chat` |
| `code2llm_analyze` | Run code2llm static analysis | `code2llm` CLI |
| `redup_scan` | Run duplication detection | `redup` CLI |
| `vallm_validate` | Validate code quality | `vallm` API/CLI |
| `llx_proxy_status` | Check LiteLLM proxy status | `llx proxy status` |
| `aider` | AI pair programming tool | `aider` CLI |

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
pip install llx[all]        # Everything + MCP
pip install llx[mcp]       # MCP server only
pip install llx[litellm]    # LiteLLM proxy
pip install llx[code2llm]   # Code analysis
pip install llx[redup]      # Duplication detection
pip install llx[vallm]      # Code validation
```

## Quick Start

```bash
# Analyze project and get model recommendation
llx analyze ./my-project

# Quick model selection
llx select .

# With task hint
llx select . --task refactor

# Point to pre-existing .toon files
llx analyze . --toon-dir ./analysis/

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
llx proxy start      # Start proxy on :4000
llx proxy status     # Check if running
```

Configure IDE tools to point at `http://localhost:4000`:

| Tool | Config |
|------|--------|
| Roo Code / Cline | `"apiBase": "http://localhost:4000/v1"` |
| Continue.dev | `"apiBase": "http://localhost:4000/v1"` |
| Aider | `OPENAI_API_BASE=http://localhost:4000` |
| Claude Code | `ANTHROPIC_BASE_URL=http://localhost:4000` |
| Cursor / Windsurf | OpenAI-compatible endpoint |

## Configuration

```bash
llx init  # Creates llx.toml with defaults
```

Environment variables: `LLX_LITELLM_URL`, `LLX_DEFAULT_TIER`, `LLX_PROXY_PORT`, `LLX_VERBOSE`.

## Python API

```python
from llx import analyze_project, select_model, LlxConfig

metrics = analyze_project("./my-project")
result = select_model(metrics)
print(result.model_id)   # "claude-opus-4-20250514"
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
├── __init__.py              # Public API (30L)
├── config.py                # Config loader (160L)
├── mcp/                     # MCP server (NEW)
│   ├── __init__.py          # Module init
│   ├── server.py            # MCP server dispatcher (40L)
│   ├── tools.py             # 7 MCP tool definitions (250L)
│   └── __main__.py          # python -m llx.mcp
├── analysis/
│   ├── collector.py         # Metrics from .toon, filesystem (280L)
│   └── runner.py            # Tool invocation (80L)
├── routing/
│   ├── selector.py          # Metric → tier mapping (200L)
│   └── client.py            # LiteLLM client wrapper (150L)
├── integrations/
│   ├── context_builder.py   # .toon → LLM context (130L)
│   └── proxy.py             # LiteLLM proxy management (100L)
└── cli/
    ├── app.py               # Commands (300L, max CC ≤ 8)
    └── formatters.py        # Output formatting (340L, max CC ≤ 10)
```

**Total**: ~1,600 lines across 12 modules. No file exceeds 350L. Max CC ≤ 10.

Compare: preLLM had 8,900 lines with 3 god modules (cli.py: 999L, core.py: 893L, trace.py: 509L).

## Architecture Improvements (v0.1.7)

- **✅ Refactored 6 high-CC functions** to meet targets (CC̄ ≤ 2.5, max CC ≤ 16)
- **✅ Added complete MCP server** with 7 tools for Claude Desktop integration
- **✅ Fixed import resolution issues** reported by vallm
- **✅ Enhanced test coverage** for MCP functionality
- **✅ Modular design** with single-responsibility functions

## License

Licensed under Apache-2.0.
## Author

Tom Sapletta
