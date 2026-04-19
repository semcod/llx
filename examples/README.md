# LLX Examples

A collection of examples demonstrating the unified, strategy-driven development lifecycle with LLX.

## Quick Start

All examples use **pure bash scripts** - no Python code required:

```bash
# From any example directory:
cd examples/basic
./run.sh "Your project description"

# Or use the master launcher from examples/:
cd examples
./run.sh basic "Your project description"
```

## How It Works

Each example is a simple bash script (`run.sh`) that:
1. Sets up PYTHONPATH to use llx from source
2. Calls `python3 -m llx` with appropriate commands
3. Uses `--profile free` for cost-effective LLM usage

### Example Structure

```
examples/basic/
├── run.sh          # Simple bash script using llx CLI
└── (no Python files - all logic in llx library)
```

## Available Examples

| Example | Description | Profile |
|---------|-------------|---------|
| **[basic](./basic)** | Simple project generation | `free` |
| **[python-api](./python-api)** | FastAPI project wizard | `free` |
| **[local](./local)** | Local-only development | `local` |
| **[cli-tools](./cli-tools)** | CLI tool generator | `free` |
| **[fullstack](./fullstack)** | Full-stack applications | `balanced` |
| **[planfile](./planfile)** | Strategy-driven development | `balanced` |
| **[hybrid](./hybrid)** | Cloud-local hybrid | `balanced` |
| **[docker](./docker)** | Containerized apps | `balanced` |
| **[proxy](./proxy)** | Proxy configuration | `balanced` |
| **[multi-provider](./multi-provider)** | Multiple LLM providers | `balanced` |
| **[filtering](./filtering)** | Advanced filtering | `free` |
| **[aider](./aider)** | Aider integration | `balanced` |
| **[vscode-roocode](./vscode-roocode)** | VS Code extension | `free` |

### Basic Usage
```bash
cd examples/basic
./run.sh "Simple REST API with user authentication"
```

### Using Master Launcher
```bash
cd examples
./run.sh basic "Simple REST API"
./run.sh python-api "FastAPI service"
./run.sh local "Offline analytics tool"
```

# From repo root:
PYTHONPATH=. python3 -m llx plan wizard --description "Build a notes API" --profile free
```

## Model Profiles

- **`free`** - Uses free-tier models (e.g., OpenRouter free endpoints)
- **`local`** - Uses local Ollama models (privacy/offline)
- **`balanced`** - Mix of local and cloud models
- **`cheap`** - Cost-optimized cloud models
- **`premium`** - Best quality models

## Requirements

- Python 3.10+
- LLX dependencies (see main repo `pyproject.toml`)
- For cloud models: `OPENROUTER_API_KEY` in `.env`
- For local models: Ollama installed

## No Installation Needed

These examples work directly from source without installing llx:
```bash
# Just clone and run:
git clone <repo>
cd llx/examples/basic
./run.sh "Your project"
```

The bash scripts automatically set PYTHONPATH to use llx from the repo root.
