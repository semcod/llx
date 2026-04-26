# llx

**Intelligent LLM model router driven by real code metrics.**

[![PyPI](https://img.shields.io/pypi/v/llx)](https://pypi.org/project/llx/)
[![Version](https://img.shields.io/badge/version-0.1.79-blue)](https://pypi.org/project/llx/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.79-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$7.50-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-36.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $7.5000 (104 commits)
- 👤 **Human dev:** ~$3597 (36.0h @ $100/h, 30min dedup)

Generated on 2026-04-26 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## Documentation map

- `README.md` — project overview, install, and quickstart
- `docs/README.md` — generated API inventory from source analysis
- `docs/llx-tools.md` — ecosystem CLI reference
- `docs/PLANFILE_CLEANUP.md` — ticket lifecycle, freshness, `llx plan clean`, prune flags
- `docs/PRIVACY.md` — anonymization and sensitive-data handling

**Successor to [preLLM](https://github.com/wronai/prellm)** — rebuilt with modular architecture, no god modules, and metric-driven routing.

llx analyzes your codebase with **code2llm**, **redup**, and **vallm**, then selects the optimal LLM model based on actual project metrics — file count, complexity, coupling, duplication — not abstract scores.

**Principle**: larger + more coupled + more complex → stronger (and more expensive) model.

## CLI surface

llx is organized around a small set of command groups:

- `llx analyze`, `llx select`, `llx chat` — metric-driven analysis and model routing
- `llx proxy` — LiteLLM proxy config, start, and status
- `llx mcp` — MCP server start, config, and tool listing
- `llx plan` — planfile generation, review, code generation, and execution
- `llx strategy` — interactive strategy creation, validation, run, and verification
- `llx info`, `llx models`, `llx init`, `llx fix` — inspection and utility commands

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
   │    ├── balanced: Qwen 2.5 Coder (OpenRouter) │
   │    ├── cheap:    Claude Haiku 4.5            │
   │    ├── free:     Nemotron 3 Super (OpenRouter)│
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

## MCP server

llx exposes its MCP tools through a shared registry in `llx.mcp.tools.MCP_TOOLS`.

By default, the MCP server runs over **stdio** for Claude Desktop. Use SSE only when you need a remote or web client.

```bash
# Start MCP server over SSE for web/remote clients
llx mcp start --mode sse --port 8000

# Direct module entrypoint
python -m llx.mcp --sse --port 8000
```

### Tool groups

- `llx_analyze`, `llx_select`, `llx_chat` — project metrics and model routing
- `llx_preprocess`, `llx_context` — query preprocessing and environment context
- `code2llm_analyze`, `redup_scan`, `vallm_validate` — code-quality analysis helpers
- `llx_proxy_status`, `llx_proxym_status`, `llx_proxym_chat` — proxy and proxym integration
- `aider`, `planfile_generate`, `planfile_apply` — workflow and refactoring helpers
- `llx_privacy_scan`, `llx_project_anonymize`, `llx_project_deanonymize` — privacy tooling

### Claude Desktop setup

```json
{
  "mcpServers": {
    "llx": {
      "command": "python3",
      "args": ["-m", "llx.mcp"]
    }
  }
}
```

## Installation

```bash
# Recommended: Use uv for 10-100x faster installation
pip install uv
uv pip install -e ".[dev]"

# Or with pip
pip install llx

# With integrations
pip install llx[all]        # Everything + MCP
pip install llx[mcp]       # MCP server only
pip install llx[litellm]    # LiteLLM proxy
pip install llx[code2llm]   # Code analysis
pip install llx[redup]      # Duplication detection
pip install llx[vallm]      # Code validation

# Development environments
pip install -e ".[dev]"      # Lightweight dev tools (pytest, ruff, mypy)
pip install -e ".[dev-full]" # Full dev with all tools (goal, costs, pfix)
```

**uv Installation (Recommended):**
```bash
pip install uv
uv pip install -e ".[dev]"  # 10-100x faster than pip
```

### Test profiles

```bash
# Default test profile (used by goal.yaml)
pytest tests/ -v

# Full test profile with MCP tests enabled
pip install -e ".[mcp]"
pytest tests/ -v
```

`tests/test_mcp.py` and `tests/test_aider_mcp.py` require the optional `mcp` package.
When `llx[mcp]` is not installed, those modules are skipped automatically instead of
breaking test collection.

**Configuration:**
Model tiers are configured in `llx.yaml`:
```yaml
selection:
  models:
    balanced:
      provider: openrouter
      model_id: openrouter/x-ai/grok-code-fast-1
      max_context: 200000
```

```bash
# Analyze project and get model recommendation
llx analyze ./my-project

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

## Privacy & Anonymization

LLX provides **reversible anonymization** to protect sensitive data when sending to LLMs:

### Features
- **Text anonymization**: Emails, API keys, passwords, PESEL, credit cards
- **Project-level**: AST-based code anonymization (variables, functions, classes)
- **Round-trip**: Anonymize → Send to LLM → Deanonymize response
- **Persistent mapping**: Save/restore context for later deanonymization

### Quick Usage

```python
from llx.privacy import quick_anonymize, quick_deanonymize

# Simple text anonymization
result = quick_anonymize("Email: user@example.com, API: sk-abc123")
print(result.text)  # "Email: [EMAIL_A1B2], API: [APIKEY_C3D4]"

# Later: restore original values
restored = quick_deanonymize(llm_response, result.mapping)
```

### Project-Level Anonymization

```python
from llx.privacy.project import AnonymizationContext, ProjectAnonymizer
from llx.privacy.deanonymize import ProjectDeanonymizer

# Anonymize entire project
ctx = AnonymizationContext(project_path="./my-project")
anonymizer = ProjectAnonymizer(ctx)
result = anonymizer.anonymize_project()

# Save context for later
ctx.save("./my-project.anon.json")

# Deanonymize LLM response
deanonymizer = ProjectDeanonymizer(ctx)
restored = deanonymizer.deanonymize_chat_response(llm_response)
```

### MCP Tools

```json
// Scan for sensitive data
{"tool": "llx_privacy_scan", "text": "Email: user@example.com"}

// Anonymize project
{"tool": "llx_project_anonymize", "path": "./my-project", "output_dir": "./anon"}

// Deanonymize response
{"tool": "llx_project_deanonymize", "context_path": "./anon/.anonymization_context.json", "text": "Fix fn_ABC123"}
```

See `docs/PRIVACY.md` and `examples/privacy/` for complete documentation.

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

## Planfile Integration

llx supports planfile.yaml format (redsl-generated) for sequential task execution:

```python
from llx.planfile import execute_strategy

# Execute planfile.yaml (supports V1, V2, and redsl formats)
results = execute_strategy(
    "planfile.yaml",
    project_path=".",
    dry_run=True
)

# Process results
for result in results:
    print(f"{result.task_name}: {result.status}")
```

**CLI usage:**
```bash
# Basic execution
llx plan run .                          # Run planfile.yaml
llx plan run . --tier free               # With specific model tier
llx plan run . --sprint 1                # Only sprint 1
llx plan run . --dry-run                 # Simulate without executing

# Concurrency and task limits
llx plan run . --max-concurrent 3        # Run 3 tasks in parallel
llx plan run . --max-tasks 10            # Process only 10 tasks total
llx plan run . -j 5 -n 20                # Short form: 5 concurrent, max 20 tasks

# Proxy management (automatic detection and startup)
llx plan run .                          # Auto-starts proxy if not running
llx plan run . --no-auto-start-proxy     # Disable automatic proxy start

# Code editing with automatic backend detection
llx plan run . --use-aider               # Auto-detect best backend (LOCAL > CURSOR > WINDSURF > CLAUDE_CODE > DOCKER > MCP > LLM_CHAT)
llx plan run . -a -j 3 -n 10             # Backend detection + concurrency + task limit

# Structured YAML output (always on stdout)
llx plan run . --sprint 1 --max-tasks 1 > run-results.yaml

# Also save a copy to file while keeping YAML on stdout
llx plan run . --output-yaml results.yaml
llx plan run . -o execution_results.yaml

# Optional: sync TODO.md checkboxes from planfile task status/results
# (configured in planfile.yaml)
# integrations:
#   markdown:
#     sync_on_plan_run: true
#     todo_file: TODO.md

# Generation and review
llx plan generate strategy.yaml --output generated/
llx plan review strategy.yaml --project .

# GitHub ticket creation (requires external planfile)
llx plan execute strategy.yaml --project . --dry-run
```

**Code Editing Backends:**
When using `--use-aider`, llx automatically detects and uses the best available backend:

- **LOCAL** - Local aider package (highest priority)
- **CURSOR** - Cursor AI
- **WINDSURF** - Windsurf AI
- **CLAUDE_CODE** - Claude Code
- **DOCKER** - Aider in Docker container
- **MCP** - MCP services
- **LLM_CHAT** - Fallback (always available)

The system automatically detects which backends are installed and selects the best one.

**Task validation:**
- `success` - Changes were made to code
- `no_changes` - Issue not found or already fixed; ticket obsolete (maps to `canceled`)
- `invalid` - No changes made (backend didn't modify files)
- `not_found` - Target file doesn't exist
- `already_fixed` - LLM reports issue not found or already fixed
- `failed` - Execution error

Use `--use-aider` for reliable code editing - the system automatically selects the best available backend.

**Supported formats:**
- **V1**: Tasks defined separately in `task_patterns`
- **V2**: Tasks embedded directly in sprints
- **planfile.yaml**: Redsl-generated format with flat tasks list and sprint task_patterns

See `llx/planfile/README_SIMPLIFIED.md` for details.

## Testql Integration

llx can execute tasks generated by testql audits:

```bash
# Generate planfile from testql audit
testql audit --output .testql/dom-audit-planfile.json

# Convert to planfile.yaml format (if needed)
# Then execute with llx
llx plan execute planfile.yaml --project . --dry-run
```

**Example workflow:**
```bash
# 1. Run testql audit
testql audit --path ./my-project

# 2. Generate planfile.yaml from audit results
# (use redsl or manual conversion)

# 3. Execute tasks with llx
from llx.planfile import execute_strategy
results = execute_strategy("planfile.yaml", project_path="./my-project")
```

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
| [planfile](https://github.com/semcod/planfile) | Strategy execution | Task execution, sprint management |
| [testql](https://github.com/semcod/testql) | Quality testing | Audit integration, ticket generation |
| **llx** | **Model routing + MCP server** | **Consumes all above** |

## Package structure

```
llx/
├── __init__.py
├── config.py
├── analysis/            # Project metrics and external tool runners
├── cli/                 # Typer commands and terminal formatters
├── commands/            # High-level command helpers
├── detection/           # Project type detection
├── integrations/        # Proxy, proxym, and context helpers
├── mcp/                 # MCP server, client, service, and tool registry
├── orchestration/       # Multi-instance coordination utilities
├── planfile/            # Strategy generation and execution helpers
├── prellm/              # Small→large LLM preprocessing pipeline
├── privacy/             # Anonymization and deanonymization helpers
├── routing/             # Model selection and LiteLLM client
└── tools/               # Docker, VS Code, models, config, health utilities
```

Full generated API inventory: `docs/README.md`.

## Architecture notes

- **Shared MCP registry**: `llx.mcp.tools.MCP_TOOLS` powers both `llx mcp tools` and the server dispatcher.
- **Single tier order**: `routing/selector.py` uses one `TIER_ORDER` constant for selection and context-window upgrades.
- **Version alignment**: the package exports now match `pyproject.toml` and `VERSION`.
- **Focused modules**: CLI, routing, analysis, integrations, and planfile code are split by responsibility.

## License

Licensed under Apache-2.0.
## Status

_Last updated by [taskill](https://github.com/oqlos/taskill) at 2026-04-25 18:22 UTC_

| Metric | Value |
|---|---|
| HEAD | `2c593db` |
| Coverage | — |
| Failing tests | — |
| Commits in last cycle | 0 |

> No commits or file changes since the last taskill run.

<!-- taskill:status:end -->
