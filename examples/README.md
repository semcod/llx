# LLX Examples

Simplified workflow for project analysis, strategy generation, and code implementation.

## Main Workflow

The recommended way to use LLX is the 4-step strategy-driven workflow:

1. **Generate Strategy**: Create a `strategy.yaml` based on a prompt or project analysis.
2. **Generate Code**: Implement the strategy sprint-by-sprint.
3. **Run App**: Launch the generated application with automatic dependency check.
4. **Monitor**: Check health and quality gates.

### 4-Step One-Liners

```bash
# 1. Generate (uses free NVIDIA models by default)
llx plan generate . --profile free --focus api -o strategy.yaml

# 2. Code
llx plan code strategy.yaml ./my-project --profile free

# 3. Run
llx plan run ./my-project

# 4. Monitor
llx plan monitor strategy.yaml --url http://localhost:8000
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
