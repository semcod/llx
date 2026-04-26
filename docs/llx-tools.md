# llx-tools - Unified CLI for llx Ecosystem Management

`llx-tools` is a comprehensive command-line interface for managing the entire llx ecosystem, including Docker containers, AI tools, VS Code, models, and configurations.

## 🚀 Installation

```bash
# Install llx with tools
pip install -e .

# Or install tools only
pip install llx[tools]
```

## 📋 Quick Start

```bash
# Start entire development environment
llx-tools start

# Check system status
llx-tools status

# Run health check
llx-tools health check

# Access AI tools
llx-tools ai-tools shell

# Start VS Code
llx-tools vscode start

# --- Plan & Workflow (new) ---

# Run planfile strategy with pre-flight validation
llx plan run .

# Check ticket freshness before running
llx plan validate .

# Clean resolved / canceled tickets
llx plan clean .

# Run a workflow pipeline defined in llx.yaml
llx run
```

## 🛠️ Available Commands

### Environment Management

#### Start Environment
```bash
# Start development environment
llx-tools start

# Start specific environment
llx-tools start --env prod

# Start specific services
llx-tools start --services llx-api redis
```

#### Stop Environment
```bash
# Stop development environment
llx-tools stop

# Stop specific environment
llx-tools stop --env prod

# Stop specific services
llx-tools stop --services vscode ai-tools
```

```bash
# Restart specific service
llx-tools restart --service llx-api
```

```bash
# Detailed status
llx-tools status --detailed

# Specific environment
llx-tools status --env prod
```

```bash
# Comprehensive health check
llx-tools health check

# Quick health check
llx-tools health quick

# Monitor services over time
llx-tools health monitor --interval 30 --duration 300
```

### Docker Management

```bash
# Docker status
llx-tools docker status

# View logs
llx-tools docker logs

# Build images
llx-tools docker build

# Clean up resources
llx-tools docker cleanup

# Backup volumes
llx-tools docker backup --backup-dir ./backups/docker

# Restore volumes
llx-tools docker restore --backup-dir ./backups/docker
```

### AI Tools Management

```bash
# Start AI tools
llx-tools ai-tools start

# Access AI tools shell
llx-tools ai-tools shell

# Check AI tools status
llx-tools ai-tools status

# Test AI tools connectivity
llx-tools ai-tools test --model qwen2.5-coder:7b --message "Hello world"

# Stop AI tools
llx-tools ai-tools stop
```

### VS Code Management

```bash
# Start VS Code
llx-tools vscode start

# Check VS Code status
llx-tools vscode status

# Install extensions
llx-tools vscode install-extensions

# Configure RooCode
llx-tools vscode configure-roocode

# Quick start guide
llx-tools vscode quick-start

# Stop VS Code
llx-tools vscode stop
```

### Model Management

```bash
# List available models
llx-tools models list

# Pull model
llx-tools models pull qwen2.5-coder:7b

# Test model
llx-tools models test qwen2.5-coder:7b --prompt "Write a Python function"

# Remove model
llx-tools models remove phi3:3.8b

# Model summary
llx-tools models summary
```

### Configuration Management

```bash
# Configuration summary
llx-tools config summary

# Create default .env file
llx-tools config create-env

# Update environment variable
llx-tools config update-env VSCODE_PASSWORD mypassword

# Get environment variable
llx-tools config get-env VSCODE_PASSWORD

# Validate configuration
llx-tools config validate

# Backup configuration
llx-tools config backup --backup-dir ./backups/config

# Restore configuration
llx-tools config restore --backup-dir ./backups/config
```

### Utilities

```bash
# System diagnostics
llx-tools utils doctor

# Version information
llx-tools utils version

# Install tools
llx-tools utils install

# Update tools
llx-tools utils update
```

## 🎯 Use Cases

### 1. Daily Development Workflow

```bash
# Start day
llx-tools start

# Check everything is healthy
llx-tools health quick

# Work with AI tools
llx-tools ai-tools shell

# Check available models
llx-tools models list

# Pull recommended coding model
llx-tools models pull qwen2.5-coder:7b

# Test model
llx-tools models test qwen2.5-coder:7b

# Clean up unused models
ollama rm unused-model
```

```bash
# Start VS Code with AI extensions
llx-tools vscode start
llx-tools vscode install-extensions
llx-tools vscode configure-roocode
```

```bash
# Comprehensive health check
llx-tools health check
```

```bash
# Check specific service
llx-tools docker status

# View logs
llx-tools docker logs

# System diagnostics
llx-tools utils doctor
```

```bash
# Create configuration
llx-tools config create-env

# Validate setup
llx-tools config validate

# Verify health
llx-tools health check
```

### Environment Variables

Key environment variables managed by `llx-tools`:

```bash
# llx API
LITELLM_PROXY_HOST=0.0.0.0
LITELLM_PROXY_PORT=4000
LITELLM_PROXY_MASTER_KEY=sk-proxy-local-dev

# Local Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434

# VS Code
VSCODE_PORT=8080
VSCODE_PASSWORD=proxym-vscode

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Configuration Files

- `.env` - Environment variables
- `pyproject.toml` - Project configuration
- `docker-compose-dev.yml` - Development Docker setup
- `litellm-config.yaml` - LiteLLM proxy configuration

## 🏥 Health Monitoring

The health checker monitors:

### Services
- **llx API** (port 4000) - Model routing proxy
- **Ollama** (port 11434) - Local LLM server
- **Redis** (port 6379) - Cache and session storage
- **VS Code** (port 8080) - Web-based IDE

### Containers
- **llx-api-dev** - llx API server
- **llx-redis-dev** - Redis cache
- **llx-vscode-dev** - VS Code server
- **llx-ai-tools-dev** - AI tools environment

### System Resources
- CPU usage and cores
- Memory usage and availability
- Disk space usage
- Network connectivity

### Filesystem
- Project directory permissions
- Configuration file existence
- Important file accessibility

### Supported AI Tools

1. **Aider** - AI pair programming tool
2. **Claude Code** - Claude-based coding assistant
3. **Cursor** - AI-powered code editor

```bash
# Access AI tools shell
llx-tools ai-tools shell

# In shell, use:
aider-llx              # Aider with llx API
aider-local            # Aider with local Ollama
claude-llx             # Claude Code with llx API
claude-local           # Claude Code with local Ollama
cursor-llx             # Cursor with llx API
cursor-local           # Cursor with local Ollama
```

### AI Tools Features

- **Code Generation** - Generate code from natural language
- **Refactoring** - Automated code improvement
- **Documentation** - Generate comprehensive docs
- **Testing** - Create unit tests automatically
- **Debugging** - Identify and fix bugs

### RooCode Extension

RooCode provides advanced AI assistance directly in VS Code:

#### Features
- **Chat Interface** - AI conversation panel
- **Inline Suggestions** - Real-time code suggestions
- **Code Actions** - Right-click AI operations
- **Context Awareness** - Project-wide understanding

#### Shortcuts
- `Ctrl+Shift+R` - Open RooCode chat
- `Ctrl+Shift+I` - Toggle inline suggestions
- `Ctrl+Shift+E` - Explain code
- `Ctrl+Shift+F` - Refactor code
- `Ctrl+Shift+G` - Generate code

#### Configuration
```json
{
  "roocode.enable": true,
  "roocode.defaultProvider": "openai-compatible",
  "roocode.apiBaseUrl": "http://localhost:4000/v1",
  "roocode.model": "qwen2.5-coder:7b",
  "roocode.fallbackProvider": "ollama",
  "roocode.fallbackBaseUrl": "http://localhost:11434"
}
```

### VS Code Tasks

Integrated VS Code tasks for common operations:

- **Start llx API** - Start the proxy server
- **Test llx API** - Test API connectivity
- **Check Ollama Models** - List available models
- **Start AI Tools** - Launch AI tools environment

## 📦 Model Management

### Recommended Models

#### For Coding
- **qwen2.5-coder:7b** - Code specialist (6GB)
- **deepseek-coder:1.3b** - Lightweight coding (776MB)

#### For General Use
- **phi3:3.8b** - Fast general model (2.2GB)
- **llama3.2:3b** - Balanced model (2.0GB)

#### Model Operations

```bash
# Pull model
llx-tools models pull qwen2.5-coder:7b

# Test model
llx-tools models test qwen2.5-coder:7b

# List models
llx-tools models list

# Remove model
llx-tools models remove unused-model
```

### Model Profiles

Create and manage model profiles:

```bash
# Create model profile
llx-tools models profile qwen2.5-coder:7b

# Load model profile
llx-tools models load-profile coding
```

## 🗂️ Plan & Workflow Management

### `llx plan run` — Execute Strategy Tickets

Runs tickets from a `planfile.yaml` strategy, with optional pre-flight freshness validation and stale-ticket pruning.

```bash
# Default run (markdown output, pre-flight ON, cancel stale ON)
llx plan run .

# Dry-run with YAML output
llx plan run . --dry-run --format yaml

# Skip pre-flight validation
llx plan run . --no-validate

# Mark stale as canceled but do not delete them
llx plan run . --cancel-stale --no-prune-stale

# Physically delete stale tickets before execution
llx plan run . --prune-stale --backup

# Limit tickets processed
llx plan run . --max-tasks 10
```

**Pre-flight behaviour** (default `--validate`):
1. `prefact` scans the codebase.
2. Tickets whose anchored file/line no longer match are flagged `stale`.
3. By default `--cancel-stale` marks them `canceled` in `planfile.yaml`.
4. If `--prune-stale` is passed, they are physically removed (with `.bak.<ts>` backup).
5. Stale tickets are skipped from LLM execution.

**Output formats:**
- `markdown` (default) — human-readable summary + compact YAML payload in fenced code block. Long fields such as `response` are truncated to ~240 chars; use `--format yaml` for full data.
- `yaml` — raw structured payload on STDOUT.

### `llx plan validate` — Ticket Freshness Check

Standalone pre-flight without executing LLM tasks.

```bash
# Markdown report
llx plan validate .

# YAML report, fail if stale tickets found
llx plan validate . --format yaml --fail-on-stale

# Also prune stale and unknown tickets
llx plan validate . --prune-stale --prune-unknown --backup
```

### `llx plan clean` — Remove Resolved Tickets

Physically deletes tickets with selected statuses from `planfile.yaml` and strips corresponding lines from `TODO.md`.

```bash
# Remove canceled tickets (default)
llx plan clean .

# Also remove done tickets
llx plan clean . --include-done

# Dry-run to preview changes
llx plan clean . --dry-run

# Skip TODO.md sync
llx plan clean . --no-todo-sync
```

### `llx plan testql` — TestQL Scenario Bridge

Validates a TestQL scenario, generates tickets for failures, and syncs them to TODO.md and configured integrations.

```bash
llx plan testql testql-scenarios/api-smoke.testql.toon.yaml
```

See [TESTQL_INTEGRATION.md](TESTQL_INTEGRATION.md) for full details.

### `llx run [WORKFLOW]` — Workflow Engine

Executes ordered step pipelines defined in `llx.yaml`.

```bash
# Run default workflow
llx run

# List available workflows
llx run --list

# Run a specific workflow with YAML report
llx run ci-pipeline --format yaml

# Fail fast (stop on first failed step)
llx run deploy --fail-fast
```

**Built-in step kinds:**
- `prefact-scan` — source-code scan.
- `plan-validate` — ticket freshness check (supports `cancel_stale`, `fail_on_stale`).
- `plan-run` — execute strategy (auto-inherits stale IDs from previous validate step).
- `testql` — run TestQL validation and ticket sync.
- `shell` — arbitrary subprocess.
- `python` — dynamic import + function call (`module:function` + kwargs).

**Env substitution:** step parameters support `${VAR}` and `${VAR:-default}`.

---

## 🔄 Status & Integration Mapping

### TaskResult → TicketStatus

When an LLM task finishes, its execution result is mapped to a planfile ticket lifecycle status:

| TaskResult | TicketStatus | Meaning |
|------------|--------------|---------|
| `success` | `done` | Code changes applied and validated |
| `no_changes` | `canceled` | Issue not found or already fixed; ticket obsolete |
| `failed` | `blocked` | LLM or tool error; requires human review |
| `already_fixed` | `done` | Detected pre-existing fix |
| `not_found` | `canceled` | Target file/function missing |
| `invalid` / `dry_run` / `skipped` | `open` | Retained for next iteration |

### Priority Mapping

Generic planfile priorities are translated per backend:

| planfile | GitHub label | GitLab label | Jira |
|----------|--------------|--------------|------|
| `critical` | `priority-critical` | `priority::critical` | `Highest` |
| `high` | `priority-high` | `priority::high` | `High` |
| `normal` | `priority-normal` | `priority::normal` | `Medium` |
| `low` | `priority-low` | `priority::low` | `Low` |

### Ticket Sources

Every ticket carries a `TicketSource` block showing its origin:

| `tool` | Description |
|--------|-------------|
| `code2llm` | Auto-generated from codebase analysis |
| `vallm` | Generated by validation LLM |
| `llx` | Generated by `llx plan` execution or workflows |
| `human` | Manually created |

---

## 🔗 External Integrations

Tickets can be bidirectionally synced with GitHub Issues, GitLab Issues, and Jira.

### GitHub

```bash
# planfile.yaml snippet
integration: ["github"]
sync:
  github:
    issue: 142
    url: "https://github.com/owner/repo/issues/142"
```

- Status `open`/`closed` maps directly to GitHub issue state.
- Intermediate states (`review`, `blocked`, `canceled`) use labels (`status:review`, etc.).
- Priority becomes `priority-{value}` label.
- Auto-created labels: `planfile`, `managed`.

### GitLab

```bash
# planfile.yaml snippet
integration: ["gitlab"]
sync:
  gitlab:
    iid: 45
    url: "https://gitlab.com/owner/project/-/issues/45"
```

- Uses GitLab-native labels; priority mapped to `priority::{value}`.
- Metadata appended as Markdown section in issue description.

### Jira

```bash
# planfile.yaml snippet
integration: ["jira"]
sync:
  jira:
    key: "PROJ-123"
    url: "https://jira.example.com/browse/PROJ-123"
```

- Jira transitions mapped from planfile status.
- Priority mapped to Jira standard levels (`Highest` … `Lowest`).

### Identity-Aware Sync

When syncing, the system attempts **update-first** by integration reference (`id`, URL, or key) before creating a new remote ticket. Resolved references are written back into `ticket.sync` and `ticket.external_refs` to prevent duplicates.

---

## 🔍 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check health
llx-tools health check

# Check logs
llx-tools docker logs

# Restart services
llx-tools restart
```

#### VS Code Not Accessible
```bash
# Check VS Code status
llx-tools vscode status

# Restart VS Code
llx-tools vscode restart

# Check password
llx-tools config get-env VSCODE_PASSWORD
```

#### AI Tools Not Working
```bash
# Check AI tools status
llx-tools ai-tools status

# Test connectivity
llx-tools ai-tools test

# Access shell for debugging
llx-tools ai-tools shell
```

#### Model Issues
```bash
# Check Ollama status
ollama list

# Test model
llx-tools models test model-name

# Pull new model
llx-tools models pull model-name
```

### Health Check Results

The health checker provides detailed diagnostics:

- ✅ **Healthy** - Service is running and responsive
- ❌ **Unhealthy** - Service has issues
- ⚠️ **Warnings** - Non-critical issues
- 💡 **Recommendations** - Suggested fixes

### Log Analysis

```bash
# View all logs
llx-tools docker logs

# View specific service logs
docker logs llx-api-dev
docker logs llx-vscode-dev
docker logs llx-ai-tools-dev
```

## 🚀 Advanced Usage

### Custom Environments

```bash
# Create custom environment
llx-tools config create-profile custom

# Use custom environment
llx-tools start --env custom
```

### Automation Scripts

Create automation scripts using llx-tools:

```bash
#!/bin/bash
# daily-start.sh

echo "🚀 Starting daily development environment..."

# Health check
llx-tools health quick

# Start VS Code
llx-tools vscode start

# Show access info
echo "📝 VS Code: http://localhost:8080"
echo "🔑 Password: $(llx-tools config get-env VSCODE_PASSWORD)"
echo "🤖 AI Tools: llx-tools ai-tools shell"
```

### Integration with IDEs

Use llx-tools with various IDEs:

#### VS Code
```bash
# Integrated tasks
Ctrl+Shift+P → Tasks: Start llx API
Ctrl+Shift+P → Tasks: Test llx API
```

#### Terminal
```bash
# Quick commands
alias llx-start="llx-tools start"
alias llx-status="llx-tools status"
alias llx-health="llx-tools health quick"
```

### Backup and Restore

```bash
# Backup entire setup
llx-tools config backup --backup-dir ./backups/$(date +%Y%m%d)
llx-tools docker backup --backup-dir ./backups/$(date +%Y%m%d)

# Restore setup
llx-tools config restore --backup-dir ./backups/20240325
llx-tools docker restore --backup-dir ./backups/20240325
```

### Documentation
- [llx Main Documentation](../README.md)
- [TestQL Integration](TESTQL_INTEGRATION.md)
- [Docker Integration](../examples/docker/README.md)
- [AI Tools Examples](../examples/ai-tools/README.md)
- [VS Code + RooCode](../examples/vscode-roocode/README.md)

### Configuration Files
- [pyproject.toml](../pyproject.toml) - Project configuration
- [docker-compose-dev.yml](../docker-compose-dev.yml) - Development setup
- [litellm-config.yaml](../litellm-config.yaml) - Model configuration

### Examples and Demos
- [Docker Examples](../examples/docker/)
- [AI Tools Examples](../examples/ai-tools/)
- [VS Code Examples](../examples/vscode-roocode/)

---

**🎉 Enjoy managing your llx ecosystem with llx-tools!**
