# LLX Examples

A collection of examples demonstrating the unified, strategy-driven development lifecycle with LLX.

## The Unified Flow

All examples now follow a standardized **1-command workflow**. Whether you are building an API, a CLI tool, or a full-stack app, the process is the same:

```bash
# In any example directory:
bash run.sh "Your project description"
```

This single command triggers the **LLX Project Wizard**, which guides you through:
1.  **Architecture & Strategy**: Generating a robust `strategy.yaml`.
2.  **Implementation**: Coding exactly 8 sprints (Spec, Impl, Test, Deploy, Monitor).
3.  **Run & Monitor**: Instructions for starting and health-checking your app.

### Manual One-Liners

If you prefer using the CLI directly:
```bash
llx plan wizard --description "Build a notes API"
```

## Available Examples

| Example | Description | Run Command |
|---------|-------------|-------------|
| **[python-api](./python-api)** | **Recommended.** Full prompt-to-API workflow. | `bash run.sh` |
| **[planfile](./planfile)** | Focus on strategy generation and dry-runs. | `bash run.sh` |
| **[basic](./basic)** | Basic `analyze` and `select` commands. | `bash run.sh` |

## Master Launcher

You can run any example from this directory using the master launcher:

```bash
bash run.sh python-api
bash run.sh planfile
bash run.sh basic
```

## Requirements

- `OPENROUTER_API_KEY` in your `.env` or environment.
- Python 3.10+
