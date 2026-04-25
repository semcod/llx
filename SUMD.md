# llx

Intelligent LLM model router driven by real code metrics — successor to preLLM

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `llx`
- **version**: `0.1.58`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements-dev.txt, requirements.txt, Taskfile.yml, Makefile, testql(3), app.doql.less, pyqual.yaml, goal.yaml, .env.example, Dockerfile, docker-compose.yml, src(3 mod), project/(2 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: llx;
  version: 0.1.58;
}

dependencies {
  runtime: "typer>=0.24, rich>=13.0, pydantic>=2.0, pydantic-settings>=2.0, pydantic-yaml>=1.0, tomli>=2.0; python_version<'3.11', httpx>=0.27, pyyaml>=6.0, requests>=2.31, docker>=6.0, psutil>=5.9, planfile>=0.1.30";
  dev: "pytest>=8.0, pytest-cov>=5.0, ruff>=0.5, mypy>=1.10, goal>=2.1.0, costs>=0.1.20, click<8.1.0, pfix>=0.1.60, pyqual>=0.1.36, starlette>=0.37, sse-starlette>=2.0, uvicorn>=0.29";
}

entity[name="ItemBase"] {
  title: string!;
  description: string;
}

entity[name="ProcessInfo"] {
  pid: int!;
  cwd: string!;
  user: string!;
  parent_pid: int | None;
  tty: string!;
}

entity[name="LocaleInfo"] {
  lang: string!;
  lc_all: string!;
  timezone: string!;
  encoding: string!;
}

entity[name="ShellInfo"] {
  shell: string!;
  term: string!;
  columns: int!;
  lines: int!;
}

entity[name="NetworkContext"] {
  hostname: string!;
  local_ip: string!;
  dns_suffix: string!;
}

entity[name="ShellContext"] {
  env_vars: dict[str, str]!;
  process: ProcessInfo!;
  locale: LocaleInfo!;
  shell: ShellInfo!;
  network: NetworkContext!;
  collected_at: datetime!;
  collection_duration_ms: float!;
}

entity[name="FilterReport"] {
  blocked_keys: list[str]!;
  masked_keys: list[str]!;
  safe_keys: list[str]!;
  total_processed: int!;
}

entity[name="CompressedFolder"] {
  root: string!;
  toon_output: string!;
  dependency_graph: dict[str, list[str]]!;
  module_summaries: dict[str, str]!;
  total_modules: int!;
  total_functions: int!;
  estimated_tokens: int!;
}

entity[name="RuntimeContext"] {
  env_safe: dict[str, str]!;
  process: dict[str, Any]!;
  locale: dict[str, str]!;
  network: dict[str, str]!;
  git: dict[str, str] | None;
  system: dict[str, str]!;
  collected_at: string!;
  sensitive_blocked_count: int!;
  token_estimate: int!;
}

entity[name="SessionSnapshot"] {
  session_id: string!;
  interactions: list[dict[str, Any]]!;
  preferences: dict[str, str]!;
  runtime_context: RuntimeContext | None;
  codebase_summary: str | None;
  created_at: string!;
  exported_at: string!;
}

entity[name="BiasPattern"] {
  regex: string!;
  action: string!;
  severity: string!;
  description: string!;
}

entity[name="ModelConfig"] {
  fallback: list[str]!;
  timeout: int!;
  max_tokens: int!;
}

entity[name="GuardConfig"] {
  bias_patterns: list[BiasPattern]!;
  clarify_template: string!;
  max_retries: int!;
  policy: Policy!;
  models: ModelConfig!;
  context_sources: list[dict[str, Any]]!;
}

entity[name="DomainRule"] {
  name: string!;
  keywords: list[str]!;
  intent: string!;
  required_fields: list[str]!;
  enrich_template: string!;
  severity: string!;
  strategy: DecompositionStrategy!;
}

entity[name="LLMProviderConfig"] {
  model: string!;
  fallback: list[str]!;
  max_retries: int!;
  timeout: int!;
  max_tokens: int!;
  temperature: float!;
}

entity[name="DecompositionPrompts"] {
  classify_prompt: string!;
  structure_prompt: string!;
  enrich_prompt: string!;
  compose_prompt: string!;
  split_prompt: string!;
}

entity[name="PreLLMConfig"] {
  small_model: LLMProviderConfig!;
  large_model: LLMProviderConfig!;
  domain_rules: list[DomainRule]!;
  prompts: DecompositionPrompts!;
  default_strategy: DecompositionStrategy!;
  context_sources: list[dict[str, Any]]!;
  max_retries: int!;
  policy: Policy!;
}

entity[name="ProcessStep"] {
  name: string!;
  prompt: string!;
  policy: Policy!;
  approval: ApprovalMode!;
  rollback: bool!;
  timeout: int!;
  depends_on: list[str]!;
  strategy: DecompositionStrategy | None;
}

entity[name="ProcessConfig"] {
  process: string!;
  description: string!;
  context_sources: list[dict[str, Any]]!;
  steps: list[ProcessStep]!;
}

entity[name="AuditEntry"] {
  timestamp: datetime!;
  action: string!;
  query: string!;
  response_summary: string!;
  model: string!;
  policy: Policy!;
  step_name: str | None;
  process_name: str | None;
  metadata: dict[str, Any]!;
}

entity[name="ModelHints"] {
  design: ModelTier;
  implementation: ModelTier;
  review: ModelTier;
  triage: ModelTier;
}

entity[name="TaskPattern"] {
  id: string!;
  type: TaskType!;
  title: string!;
  description: string!;
  priority: string;
  estimate: string;
  labels: List[str]!;
  model_hints: ModelHints!;
  metadata: Dict[str, Any]!;
}

entity[name="Sprint"] {
  id: int!;
  name: string!;
  length_days: int!;
  objectives: List[str]!;
  start_date: string;
  tasks: List[str]!;
}

entity[name="Goal"] {
  short: string!;
  quality: List[str]!;
  delivery: List[str]!;
  metrics: List[str]!;
}

entity[name="QualityGate"] {
  name: string!;
  description: string!;
  criteria: List[str]!;
  required: bool!;
}

entity[name="Strategy"] {
  name: string!;
  version: string!;
  project_type: string!;
  domain: string!;
  goal: Goal!;
  description: string;
  sprints: List[Sprint]!;
  tasks: Dict[str, List[TaskPattern]]!;
  quality_gates: List[QualityGate]!;
  metadata: Dict[str, Any]!;
}

database[name="redis"] {
  type: redis;
  url: env.REDIS_URL;
}

database[name="postgres"] {
  type: postgresql;
  url: env.DATABASE_URL;
}

database[name="backup"] {
  type: postgresql;
  url: env.DATABASE_URL;
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="llx"] {

}

integration[name="email"] {
  type: smtp;
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Installing llx...";
  step-2: run cmd=python -m venv .venv;
  step-3: run cmd=.venv/bin/pip install --upgrade pip;
  step-4: run cmd=.venv/bin/pip install -e .;
  step-5: run cmd=.venv/bin/pip install -r requirements-dev.txt;
  step-6: run cmd=echo "✅ Installation completed!";
  step-7: run cmd=echo "Run 'source .venv/bin/activate' to activate the virtual environment";
}

workflow[name="install-tools"] {
  trigger: manual;
  step-1: run cmd=echo "🔧 Installing local tools...";
  step-2: run cmd=if command -v ollama > /dev/null 2>&1; then \;
  step-3: run cmd=echo "✅ Ollama already installed"; \;
  step-4: run cmd=else \;
  step-5: run cmd=echo "📦 Installing Ollama..."; \;
  step-6: run cmd=curl -fsSL https://ollama.ai/install.sh | sh; \;
  step-7: run cmd=fi;
  step-8: run cmd=if command -v redis-cli > /dev/null 2>&1; then \;
  step-9: run cmd=echo "✅ Redis CLI already installed"; \;
  step-10: run cmd=else \;
  step-11: run cmd=echo "📦 Installing Redis CLI..."; \;
  step-12: run cmd=if command -v apt-get > /dev/null 2>&1; then \;
  step-13: run cmd=sudo apt-get update && sudo apt-get install -y redis-tools; \;
  step-14: run cmd=elif command -v brew > /dev/null 2>&1; then \;
  step-15: run cmd=brew install redis; \;
  step-16: run cmd=else \;
  step-17: run cmd=echo "Please install Redis CLI manually"; \;
  step-18: run cmd=fi; \;
  step-19: run cmd=fi;
  step-20: run cmd=echo "✅ Tools installation completed!";
}

workflow[name="dev"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Starting development environment...";
  step-2: run cmd=./docker-manage.sh dev;
}

workflow[name="prod"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Starting production environment...";
  step-2: run cmd=./docker-manage.sh prod;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=echo "🧪 Running tests...";
  step-2: run cmd=.venv/bin/python -m pytest tests/ -v --tb=short;
}

workflow[name="test-docker"] {
  trigger: manual;
  step-1: run cmd=echo "🐳 Running tests in Docker...";
  step-2: run cmd=docker build -t llx-test .;
  step-3: run cmd=docker run --rm llx-test .venv/bin/python -m pytest tests/ -v;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=echo "🔍 Running linting...";
  step-2: run cmd=.venv/bin/python -m flake8 llx/ --max-line-length=100 --ignore=E203,W503;
  step-3: run cmd=.venv/bin/python -m mypy llx/ --ignore-missing-imports;
  step-4: run cmd=.venv/bin/python -m black --check llx/;
}

workflow[name="format"] {
  trigger: manual;
  step-1: run cmd=echo "📝 Formatting code...";
  step-2: run cmd=.venv/bin/python -m black llx/;
  step-3: run cmd=.venv/bin/python -m isort llx/;
}

workflow[name="docker-dev"] {
  trigger: manual;
  step-1: run cmd=echo "🐳 Starting development containers...";
  step-2: run cmd=./docker-manage.sh dev;
}

workflow[name="docker-prod"] {
  trigger: manual;
  step-1: run cmd=echo "🐳 Starting production containers...";
  step-2: run cmd=./docker-manage.sh prod;
}

workflow[name="docker-stop"] {
  trigger: manual;
  step-1: run cmd=echo "🛑 Stopping all containers...";
  step-2: run cmd=./docker-manage.sh stop;
}

workflow[name="docker-clean"] {
  trigger: manual;
  step-1: run cmd=echo "🧹 Cleaning Docker resources...";
  step-2: run cmd=./docker-manage.sh clean;
}

workflow[name="docker-logs"] {
  trigger: manual;
  step-1: run cmd=echo "📋 Showing logs...";
  step-2: run cmd=./docker-manage.sh logs dev;
}

workflow[name="docker-status"] {
  trigger: manual;
  step-1: run cmd=echo "📊 Container status...";
  step-2: run cmd=./docker-manage.sh status;
}

workflow[name="examples-basic"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Running basic example...";
  step-2: run cmd=cd examples/basic && ./run.sh;
}

workflow[name="examples-proxy"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Running proxy example...";
  step-2: run cmd=cd examples/proxy && timeout 10s ./run.sh || echo "Proxy example completed (timeout expected)";
}

workflow[name="examples-docker"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Running Docker example...";
  step-2: run cmd=cd examples/docker && ./run.sh;
}

workflow[name="examples-multi"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Running multi-provider example...";
  step-2: run cmd=cd examples/multi-provider && ./run.sh;
}

workflow[name="examples-local"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Running local models example...";
  step-2: run cmd=cd examples/local && ./run.sh;
}

workflow[name="examples-all"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Running all examples...";
  step-2: run cmd=$(MAKE) examples-basic;
  step-3: run cmd=$(MAKE) examples-multi;
  step-4: run cmd=$(MAKE) examples-local;
  step-5: run cmd=$(MAKE) examples-docker;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=echo "🧹 Cleaning temporary files...";
  step-2: run cmd=find . -type f -name "*.pyc" -delete;
  step-3: run cmd=find . -type d -name "__pycache__" -delete;
  step-4: run cmd=find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true;
  step-5: run cmd=rm -rf build/ dist/ .coverage htmlcov/;
  step-6: run cmd=echo "✅ Clean completed!";
}

workflow[name="doctor"] {
  trigger: manual;
  step-1: run cmd=echo "🔍 System health check...";
  step-2: run cmd=echo "";
  step-3: run cmd=echo "Python:";
  step-4: run cmd=python --version || echo "❌ Python not found";
  step-5: run cmd=echo "";
  step-6: run cmd=echo "Docker:";
  step-7: run cmd=docker --version || echo "❌ Docker not found";
  step-8: run cmd=docker info > /dev/null 2>&1 && echo "✅ Docker daemon running" || echo "❌ Docker daemon not running";
  step-9: run cmd=echo "";
  step-10: run cmd=echo "Local Tools:";
  step-11: run cmd=command -v ollama > /dev/null 2>&1 && echo "✅ Ollama installed" || echo "❌ Ollama not installed";
  step-12: run cmd=ollama list > /dev/null 2>&1 && echo "✅ Ollama running" || echo "❌ Ollama not running";
  step-13: run cmd=command -v redis-cli > /dev/null 2>&1 && echo "✅ Redis CLI installed" || echo "❌ Redis CLI not installed";
  step-14: run cmd=echo "";
  step-15: run cmd=echo "Virtual Environment:";
  step-16: run cmd=test -d .venv && echo "✅ .venv exists" || echo "❌ .venv not found";
  step-17: run cmd=test -f .venv/bin/python && echo "✅ Python in .venv" || echo "❌ Python not in .venv";
  step-18: run cmd=echo "";
  step-19: run cmd=echo "Configuration Files:";
  step-20: run cmd=test -f .env && echo "✅ .env exists" || echo "❌ .env not found";
  step-21: run cmd=test -f llx.yaml && echo "✅ llx.yaml exists" || echo "❌ llx.yaml not found";
  step-22: run cmd=test -f litellm-config.yaml && echo "✅ litellm-config.yaml exists" || echo "❌ litellm-config.yaml not found";
  step-23: run cmd=test -f docker-compose.yml && echo "✅ docker-compose.yml exists" || echo "❌ docker-compose.yml not found";
  step-24: run cmd=echo "";
  step-25: run cmd=echo "API Keys:";
  step-26: run cmd=grep -q "ANTHROPIC_API_KEY=" .env && echo "✅ ANTHROPIC_API_KEY configured" || echo "❌ ANTHROPIC_API_KEY not configured";
  step-27: run cmd=grep -q "OPENROUTER_API_KEY=" .env && echo "✅ OPENROUTER_API_KEY configured" || echo "❌ OPENROUTER_API_KEY not configured";
  step-28: run cmd=echo "";
  step-29: run cmd=echo "Docker Services:";
  step-30: run cmd=docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "llx-|llx_" || echo "❌ No llx containers running";
  step-31: run cmd=echo "";
  step-32: run cmd=echo "Local Ollama Models:";
  step-33: run cmd=ollama list 2>/dev/null | head -5 || echo "❌ No local models";
}

workflow[name="backup"] {
  trigger: manual;
  step-1: run cmd=echo "💾 Creating backups...";
  step-2: run cmd=./docker-manage.sh backup;
  step-3: run cmd=echo "✅ Backup completed!";
}

workflow[name="quick-test"] {
  trigger: manual;
  step-1: run cmd=echo "⚡ Quick test...";
  step-2: run cmd=.venv/bin/python -c "from llx import analyze_project, select_model; print('✅ llx imports working')";
}

workflow[name="quick-start"] {
  trigger: manual;
  step-1: run cmd=echo "⚡ Quick start...";
  step-2: run cmd=$(MAKE) install;
  step-3: run cmd=$(MAKE) install-tools;
  step-4: run cmd=$(MAKE) docker-dev;
  step-5: run cmd=echo "✅ Quick start completed!";
  step-6: run cmd=echo "Services: http://localhost:4000 (API), http://localhost:3000 (WebUI)";
}

workflow[name="ci-install"] {
  trigger: manual;
  step-1: run cmd=echo "🔧 CI installation...";
  step-2: run cmd=python -m venv .venv;
  step-3: run cmd=.venv/bin/pip install --upgrade pip;
  step-4: run cmd=.venv/bin/pip install -e .;
  step-5: run cmd=.venv/bin/pip install -r requirements-dev.txt;
}

workflow[name="ci-test"] {
  trigger: manual;
  step-1: run cmd=echo "🧪 CI testing...";
  step-2: run cmd=.venv/bin/python -m pytest tests/ -v --cov=llx --cov-report=xml --cov-report=html;
}

workflow[name="ci-lint"] {
  trigger: manual;
  step-1: run cmd=echo "🔍 CI linting...";
  step-2: run cmd=.venv/bin/python -m flake8 llx/ --max-line-length=100 --ignore=E203,W503 --output-format=github;
  step-3: run cmd=.venv/bin/python -m mypy llx/ --ignore-missing-imports --junit-xml test-results.xml;
}

workflow[name="ci-build"] {
  trigger: manual;
  step-1: run cmd=echo "🐳 CI build...";
  step-2: run cmd=docker build -t llx:${BUILD_NUMBER:-latest} .;
  step-3: run cmd=docker tag llx:${BUILD_NUMBER:-latest} llx:latest;
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Publishing to PyPI...";
  step-2: run cmd=command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build);
  step-3: run cmd=rm -rf dist/ build/ *.egg-info/;
  step-4: run cmd=.venv/bin/python -m build;
  step-5: run cmd=.venv/bin/twine check dist/*;
  step-6: run cmd=echo "⚡ Ready to upload. Run: make publish-confirm to upload to PyPI";
}

workflow[name="publish-confirm"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Uploading to PyPI...";
  step-2: run cmd=.venv/bin/twine upload dist/*;
}

workflow[name="publish-test"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Publishing to TestPyPI...";
  step-2: run cmd=command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build);
  step-3: run cmd=rm -rf dist/ build/ *.egg-info/;
  step-4: run cmd=.venv/bin/python -m build;
  step-5: run cmd=.venv/bin/twine upload --repository testpypi dist/*;
}

workflow[name="version"] {
  trigger: manual;
  step-1: run cmd=echo "📦 Version information...";
  step-2: run cmd=.venv/bin/python -c "import llx; print(f'llx version: {llx.__version__}')";
}

workflow[name="tag"] {
  trigger: manual;
  step-1: run cmd=echo "🏷️  Creating git tag...";
  step-2: run cmd=if [ -z "$(VERSION)" ]; then \;
  step-3: run cmd=echo "Usage: make tag VERSION=v1.0.0"; \;
  step-4: run cmd=exit 1; \;
  step-5: run cmd=fi;
  step-6: run cmd=git tag $(VERSION);
  step-7: run cmd=git push origin $(VERSION);
}

workflow[name="docs"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Building documentation...";
  step-2: run cmd=.venv/bin/python -m mkdocs build;
}

workflow[name="docs-serve"] {
  trigger: manual;
  step-1: run cmd=echo "📚 Serving documentation...";
  step-2: run cmd=.venv/bin/python -m mkdocs serve;
}

workflow[name="profile"] {
  trigger: manual;
  step-1: run cmd=echo "📊 Running performance profile...";
  step-2: run cmd=.venv/bin/python -m cProfile -o profile.stats -m llx analyze .;
  step-3: run cmd=.venv/bin/python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)";
}

workflow[name="security"] {
  trigger: manual;
  step-1: run cmd=echo "🔒 Running security scan...";
  step-2: run cmd=.venv/bin/pip install safety bandit;
  step-3: run cmd=.venv/bin/safety check;
  step-4: run cmd=.venv/bin/bandit -r llx/;
}

workflow[name="db-reset"] {
  trigger: manual;
  step-1: run cmd=echo "🗄️  Resetting database...";
  step-2: run cmd=docker exec llx-postgres-prod psql -U llx -d llx -c "DROP SCHEMA IF EXISTS llx CASCADE; CREATE SCHEMA llx;";
  step-3: run cmd=docker exec llx-postgres-prod psql -U llx -d llx -f /docker-entrypoint-initdb.d/init.sql;
}

workflow[name="db-migrate"] {
  trigger: manual;
  step-1: run cmd=echo "🗄️  Running database migrations...";
  step-2: run cmd=# Add migration commands here;
}

workflow[name="env-dev"] {
  trigger: manual;
  step-1: run cmd=echo "🔧 Setting up development environment...";
  step-2: run cmd=cp .env.example .env.dev;
  step-3: run cmd=echo "✅ Created .env.dev - please edit with your values";
}

workflow[name="env-prod"] {
  trigger: manual;
  step-1: run cmd=echo "🔧 Setting up production environment...";
  step-2: run cmd=cp .env.example .env.prod;
  step-3: run cmd=echo "✅ Created .env.prod - please edit with production values";
}

workflow[name="up"] {
  trigger: manual;
  step-1: depend target=dev;
}

workflow[name="down"] {
  trigger: manual;
  step-1: depend target=docker-stop;
}

workflow[name="logs"] {
  trigger: manual;
  step-1: depend target=docker-logs;
}

workflow[name="ps"] {
  trigger: manual;
  step-1: depend target=docker-status;
}

workflow[name="fmt"] {
  trigger: manual;
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=python -m build;
}

workflow[name="docker-build"] {
  trigger: manual;
  step-1: run cmd=docker build -t llx:latest .;
}

workflow[name="help"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 llx Development Commands";
  step-2: run cmd=echo "==========================";
  step-3: run cmd=echo "";
  step-4: run cmd=echo "Setup:";
  step-5: run cmd=echo "  install          Install llx in development mode";
  step-6: run cmd=echo "  install-tools    Install local development tools";
  step-7: run cmd=echo "";
  step-8: run cmd=echo "Development:";
  step-9: run cmd=echo "  dev              Start development Docker stack";
  step-10: run cmd=echo "  prod             Start production Docker stack";
  step-11: run cmd=echo "  test             Run tests";
  step-12: run cmd=echo "  lint             Run linting";
  step-13: run cmd=echo "  format           Format code";
  step-14: run cmd=echo "";
  step-15: run cmd=echo "Docker:";
  step-16: run cmd=echo "  docker-dev       Start development containers";
  step-17: run cmd=echo "  docker-prod      Start production containers";
  step-18: run cmd=echo "  docker-stop      Stop all containers";
  step-19: run cmd=echo "  docker-clean     Clean Docker resources";
  step-20: run cmd=echo "  docker-logs      Show logs";
  step-21: run cmd=echo "";
  step-22: run cmd=echo "Examples:";
  step-23: run cmd=echo "  examples-basic   Run basic example";
  step-24: run cmd=echo "  examples-docker  Run Docker example";
  step-25: run cmd=echo "  examples-proxy   Run proxy example";
  step-26: run cmd=echo "";
  step-27: run cmd=echo "Utilities:";
  step-28: run cmd=echo "  clean            Clean temporary files";
  step-29: run cmd=echo "  backup           Create backups";
  step-30: run cmd=echo "  doctor           Check system health";
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="import-makefile-hint"] {
  trigger: manual;
  step-1: run cmd=echo 'Run: taskfile import Makefile to import existing targets.';
}

workflow[name="all"] {
  trigger: manual;
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}

workflow[name="sumd"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd))" > SUMD.md
echo "" >> SUMD.md
echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
echo "" >> SUMD.md
echo "## Contents" >> SUMD.md
echo "" >> SUMD.md
echo "- [Metadata](#metadata)" >> SUMD.md
echo "- [Architecture](#architecture)" >> SUMD.md
echo "- [Dependencies](#dependencies)" >> SUMD.md
echo "- [Source Map](#source-map)" >> SUMD.md
echo "- [Intent](#intent)" >> SUMD.md
echo "" >> SUMD.md
echo "## Metadata" >> SUMD.md
echo "" >> SUMD.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
echo "" >> SUMD.md
echo "## Architecture" >> SUMD.md
echo "" >> SUMD.md
echo '```' >> SUMD.md
echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
echo '```' >> SUMD.md
echo "" >> SUMD.md
echo "## Source Map" >> SUMD.md
echo "" >> SUMD.md
find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
echo "Generated SUMD.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
project_name = Path.cwd().name
py_files = list(Path('.').rglob('*.py'))
py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
data = {
    'project_name': project_name,
    'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
    'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
}
with open('sumd.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated sumd.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

workflow[name="sumr"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
echo "" >> SUMR.md
echo "SUMR - Summary Report for project analysis" >> SUMR.md
echo "" >> SUMR.md
echo "## Contents" >> SUMR.md
echo "" >> SUMR.md
echo "- [Metadata](#metadata)" >> SUMR.md
echo "- [Quality Status](#quality-status)" >> SUMR.md
echo "- [Metrics](#metrics)" >> SUMR.md
echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
echo "- [Intent](#intent)" >> SUMR.md
echo "" >> SUMR.md
echo "## Metadata" >> SUMR.md
echo "" >> SUMR.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
echo "" >> SUMR.md
echo "## Quality Status" >> SUMR.md
echo "" >> SUMR.md
if [ -f pyqual.yaml ]; then
  echo "- **pyqual_config**: ✅ Present" >> SUMR.md
  echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
else
  echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
fi
echo "" >> SUMR.md
echo "## Metrics" >> SUMR.md
echo "" >> SUMR.md
py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
echo "- **python_files**: $py_files" >> SUMR.md
lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
echo "- **total_lines**: $lines" >> SUMR.md
echo "" >> SUMR.md
echo "## Refactoring Analysis" >> SUMR.md
echo "" >> SUMR.md
echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
echo "Generated SUMR.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
from datetime import datetime
project_name = Path.cwd().name
py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
data = {
    'project_name': project_name,
    'report_type': 'SUMR',
    'generated_at': datetime.now().isoformat(),
    'metrics': {
        'python_files': py_files,
        'has_pyqual_config': Path('pyqual.yaml').exists()
    }
}
with open('SUMR.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated SUMR.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
}

environment[name="backup"] {
  runtime: docker-compose;
  env_file: .env.backup;
}

environment[name="new"] {
  runtime: docker-compose;
  env_file: .env.new;
}
```

### Source Modules

- `llx.config`
- `llx.litellm_config`
- `llx.llm`

## Interfaces

### CLI Entry Points

- `llx`
- `llx-tools`
- `llx-orchestrator`
- `llx-mcp`

### testql Scenarios

#### `testql-scenarios/generated-api-integration.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-integration.testql.toon.yaml
# SCENARIO: API Integration Tests
# TYPE: api
# GENERATED: true

CONFIG[3]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 30000
  retry_count, 3

API[4]{method, endpoint, expected_status}:
  GET, /health, 200
  GET, /api/v1/status, 200
  POST, /api/v1/test, 201
  GET, /api/v1/docs, 200

ASSERT[2]{field, operator, expected}:
  status, ==, ok
  response_time, <, 1000
```

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector, ConfigEndpointDetector

CONFIG[4]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  detected_frameworks, FastAPIDetector, ConfigEndpointDetector

# REST API Endpoints (11 unique)
API[11]{method, endpoint, expected_status}:
  GET, /health, 200
  GET, /users/, 200
  POST, /users/, 201
  GET, /products/, 200
  POST, /products/, 201
  POST, /items, 201
  GET, /items, 200
  GET, /v1/models, 200
  POST, /v1/chat/completions, 201
  POST, /v1/batch, 201
  GET, /, 200

ASSERT[2]{field, operator, expected}:
  status, <, 500
  response_time, <, 2000

# Summary by Framework:
#   fastapi: 19 endpoints
#   docker: 1 endpoints
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

LOG[73]{message}:
  "Test: test_api_performance"
  "Test: test_api_scalability"
  "Test: test_coverage"
  "Test: test_error_handling"
  "Test: test_security"
  "Test: TestMcpProxyStatus_test_proxy_not_running"
  "Test: TestMcpServerCli_test_mcp_start_sse_routes_to_sse_transport"
  "Test: test_proxy_not_running"
  "Test: test_mcp_start_sse_routes_to_sse_transport"
  "Test: TestProxymClientStructure_test_client_default_url"

INCLUDE[10]{file}:
  "/home/tom/github/semcod/llx/tests/test_privacy_project.py"
  "/home/tom/github/semcod/llx/tests/test_privacy_project.py"
  "/home/tom/github/semcod/llx/tests/test_privacy_extended.py"
  "/home/tom/github/semcod/llx/tests/test_privacy_extended.py"
  "/home/tom/github/semcod/llx/tests/test_privacy_extended.py"
```

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
name: llx
description: Minimal Taskfile
variables:
  APP_NAME: llx
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  lint:
    desc: Run ruff lint check
    cmds:
    - ruff check .
  fmt:
    desc: Auto-format with ruff
    cmds:
    - ruff format .
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  up:
    desc: Start services via docker compose
    cmds:
    - docker compose up -d
  down:
    desc: Stop services
    cmds:
    - docker compose down
  logs:
    desc: Tail compose logs
    cmds:
    - docker compose logs -f
  ps:
    desc: Show running compose services
    cmds:
    - docker compose ps
  docker-build:
    desc: Build docker image
    cmds:
    - docker build -t llx:latest .
  help:
    desc: '[imported from Makefile] help'
    cmds:
    - "echo \"\U0001F680 llx Development Commands\""
    - echo "=========================="
    - echo ""
    - echo "Setup:"
    - echo "  install          Install llx in development mode"
    - echo "  install-tools    Install local development tools"
    - echo ""
    - echo "Development:"
    - echo "  dev              Start development Docker stack"
    - echo "  prod             Start production Docker stack"
    - echo "  test             Run tests"
    - echo "  lint             Run linting"
    - echo "  format           Format code"
    - echo ""
    - echo "Docker:"
    - echo "  docker-dev       Start development containers"
    - echo "  docker-prod      Start production containers"
    - echo "  docker-stop      Stop all containers"
    - echo "  docker-clean     Clean Docker resources"
    - echo "  docker-logs      Show logs"
    - echo ""
    - echo "Examples:"
    - echo "  examples-basic   Run basic example"
    - echo "  examples-docker  Run Docker example"
    - echo "  examples-proxy   Run proxy example"
    - echo ""
    - echo "Utilities:"
    - echo "  clean            Clean temporary files"
    - echo "  backup           Create backups"
    - echo "  doctor           Check system health"
  install-tools:
    desc: '[imported from Makefile] install-tools'
    cmds:
    - "echo \"\U0001F527 Installing local tools...\""
    - if command -v ollama > /dev/null 2>&1; then \
    - "echo \"\u2705 Ollama already installed\"; \\"
    - else \
    - "echo \"\U0001F4E6 Installing Ollama...\"; \\"
    - curl -fsSL https://ollama.ai/install.sh | sh; \
    - fi
    - if command -v redis-cli > /dev/null 2>&1; then \
    - "echo \"\u2705 Redis CLI already installed\"; \\"
    - else \
    - "echo \"\U0001F4E6 Installing Redis CLI...\"; \\"
    - if command -v apt-get > /dev/null 2>&1; then \
    - sudo apt-get update && sudo apt-get install -y redis-tools; \
    - elif command -v brew > /dev/null 2>&1; then \
    - brew install redis; \
    - else \
    - echo "Please install Redis CLI manually"; \
    - fi; \
    - fi
    - "echo \"\u2705 Tools installation completed!\""
  dev:
    desc: '[imported from Makefile] dev'
    cmds:
    - "echo \"\U0001F680 Starting development environment...\""
    - ./docker-manage.sh dev
  prod:
    desc: '[imported from Makefile] prod'
    cmds:
    - "echo \"\U0001F680 Starting production environment...\""
    - ./docker-manage.sh prod
  test-docker:
    desc: '[imported from Makefile] test-docker'
    cmds:
    - "echo \"\U0001F433 Running tests in Docker...\""
    - docker build -t llx-test .
    - docker run --rm llx-test .venv/bin/python -m pytest tests/ -v
  format:
    desc: '[imported from Makefile] format'
    cmds:
    - "echo \"\U0001F4DD Formatting code...\""
    - .venv/bin/python -m black llx/
    - .venv/bin/python -m isort llx/
  docker-dev:
    desc: '[imported from Makefile] docker-dev'
    cmds:
    - "echo \"\U0001F433 Starting development containers...\""
    - ./docker-manage.sh dev
  docker-prod:
    desc: '[imported from Makefile] docker-prod'
    cmds:
    - "echo \"\U0001F433 Starting production containers...\""
    - ./docker-manage.sh prod
  docker-stop:
    desc: '[imported from Makefile] docker-stop'
    cmds:
    - "echo \"\U0001F6D1 Stopping all containers...\""
    - ./docker-manage.sh stop
  docker-clean:
    desc: '[imported from Makefile] docker-clean'
    cmds:
    - "echo \"\U0001F9F9 Cleaning Docker resources...\""
    - ./docker-manage.sh clean
  docker-logs:
    desc: '[imported from Makefile] docker-logs'
    cmds:
    - "echo \"\U0001F4CB Showing logs...\""
    - ./docker-manage.sh logs dev
  docker-status:
    desc: '[imported from Makefile] docker-status'
    cmds:
    - "echo \"\U0001F4CA Container status...\""
    - ./docker-manage.sh status
  examples-basic:
    desc: '[imported from Makefile] examples-basic'
    cmds:
    - "echo \"\U0001F4DA Running basic example...\""
    - cd examples/basic && ./run.sh
  examples-proxy:
    desc: '[imported from Makefile] examples-proxy'
    cmds:
    - "echo \"\U0001F4DA Running proxy example...\""
    - cd examples/proxy && timeout 10s ./run.sh || echo "Proxy example completed (timeout
      expected)"
  examples-docker:
    desc: '[imported from Makefile] examples-docker'
    cmds:
    - "echo \"\U0001F4DA Running Docker example...\""
    - cd examples/docker && ./run.sh
  examples-multi:
    desc: '[imported from Makefile] examples-multi'
    cmds:
    - "echo \"\U0001F4DA Running multi-provider example...\""
    - cd examples/multi-provider && ./run.sh
  examples-local:
    desc: '[imported from Makefile] examples-local'
    cmds:
    - "echo \"\U0001F4DA Running local models example...\""
    - cd examples/local && ./run.sh
  examples-all:
    desc: '[imported from Makefile] examples-all'
    cmds:
    - "echo \"\U0001F4DA Running all examples...\""
    - $(MAKE) examples-basic
    - $(MAKE) examples-multi
    - $(MAKE) examples-local
    - $(MAKE) examples-docker
  doctor:
    desc: '[imported from Makefile] doctor'
    cmds:
    - "echo \"\U0001F50D System health check...\""
    - echo ""
    - echo "Python:"
    - "python --version || echo \"\u274C Python not found\""
    - echo ""
    - echo "Docker:"
    - "docker --version || echo \"\u274C Docker not found\""
    - "docker info > /dev/null 2>&1 && echo \"\u2705 Docker daemon running\" || echo\
      \ \"\u274C Docker daemon not running\""
    - echo ""
    - echo "Local Tools:"
    - "command -v ollama > /dev/null 2>&1 && echo \"\u2705 Ollama installed\" || echo\
      \ \"\u274C Ollama not installed\""
    - "ollama list > /dev/null 2>&1 && echo \"\u2705 Ollama running\" || echo \"\u274C\
      \ Ollama not running\""
    - "command -v redis-cli > /dev/null 2>&1 && echo \"\u2705 Redis CLI installed\"\
      \ || echo \"\u274C Redis CLI not installed\""
    - echo ""
    - echo "Virtual Environment:"
    - "test -d .venv && echo \"\u2705 .venv exists\" || echo \"\u274C .venv not found\""
    - "test -f .venv/bin/python && echo \"\u2705 Python in .venv\" || echo \"\u274C\
      \ Python not in .venv\""
    - echo ""
    - echo "Configuration Files:"
    - "test -f .env && echo \"\u2705 .env exists\" || echo \"\u274C .env not found\""
    - "test -f llx.yaml && echo \"\u2705 llx.yaml exists\" || echo \"\u274C llx.yaml\
      \ not found\""
    - "test -f litellm-config.yaml && echo \"\u2705 litellm-config.yaml exists\" ||\
      \ echo \"\u274C litellm-config.yaml not found\""
    - "test -f docker-compose.yml && echo \"\u2705 docker-compose.yml exists\" ||\
      \ echo \"\u274C docker-compose.yml not found\""
    - echo ""
    - echo "API Keys:"
    - "grep -q \"ANTHROPIC_API_KEY=\" .env && echo \"\u2705 ANTHROPIC_API_KEY configured\"\
      \ || echo \"\u274C ANTHROPIC_API_KEY not configured\""
    - "grep -q \"OPENROUTER_API_KEY=\" .env && echo \"\u2705 OPENROUTER_API_KEY configured\"\
      \ || echo \"\u274C OPENROUTER_API_KEY not configured\""
    - echo ""
    - echo "Docker Services:"
    - "docker ps --format \"table {{.Names}}\\t{{.Status}}\" | grep -E \"llx-|llx_\"\
      \ || echo \"\u274C No llx containers running\""
    - echo ""
    - echo "Local Ollama Models:"
    - "ollama list 2>/dev/null | head -5 || echo \"\u274C No local models\""
  backup:
    desc: '[imported from Makefile] backup'
    cmds:
    - "echo \"\U0001F4BE Creating backups...\""
    - ./docker-manage.sh backup
    - "echo \"\u2705 Backup completed!\""
  quick-test:
    desc: '[imported from Makefile] quick-test'
    cmds:
    - "echo \"\u26A1 Quick test...\""
    - ".venv/bin/python -c \"from llx import analyze_project, select_model; print('\u2705\
      \ llx imports working')\""
  quick-start:
    desc: '[imported from Makefile] quick-start'
    cmds:
    - "echo \"\u26A1 Quick start...\""
    - $(MAKE) install
    - $(MAKE) install-tools
    - $(MAKE) docker-dev
    - "echo \"\u2705 Quick start completed!\""
    - 'echo "Services: http://localhost:4000 (API), http://localhost:3000 (WebUI)"'
  ci-install:
    desc: '[imported from Makefile] ci-install'
    cmds:
    - "echo \"\U0001F527 CI installation...\""
    - python -m venv .venv
    - .venv/bin/pip install --upgrade pip
    - .venv/bin/pip install -e .
    - .venv/bin/pip install -r requirements-dev.txt
  ci-test:
    desc: '[imported from Makefile] ci-test'
    cmds:
    - "echo \"\U0001F9EA CI testing...\""
    - .venv/bin/python -m pytest tests/ -v --cov=llx --cov-report=xml --cov-report=html
  ci-lint:
    desc: '[imported from Makefile] ci-lint'
    cmds:
    - "echo \"\U0001F50D CI linting...\""
    - .venv/bin/python -m flake8 llx/ --max-line-length=100 --ignore=E203,W503 --output-format=github
    - .venv/bin/python -m mypy llx/ --ignore-missing-imports --junit-xml test-results.xml
  ci-build:
    desc: '[imported from Makefile] ci-build'
    cmds:
    - "echo \"\U0001F433 CI build...\""
    - docker build -t llx:${BUILD_NUMBER:-latest} .
    - docker tag llx:${BUILD_NUMBER:-latest} llx:latest
  version:
    desc: '[imported from Makefile] version'
    cmds:
    - "echo \"\U0001F4E6 Version information...\""
    - '.venv/bin/python -c "import llx; print(f''llx version: {llx.__version__}'')"'
  tag:
    desc: '[imported from Makefile] tag'
    cmds:
    - "echo \"\U0001F3F7\uFE0F  Creating git tag...\""
    - if [ -z "$(VERSION)" ]; then \
    - 'echo "Usage: make tag VERSION=v1.0.0"; \'
    - exit 1; \
    - fi
    - git tag $(VERSION)
    - git push origin $(VERSION)
  docs:
    desc: '[imported from Makefile] docs'
    cmds:
    - "echo \"\U0001F4DA Building documentation...\""
    - .venv/bin/python -m mkdocs build
  docs-serve:
    desc: '[imported from Makefile] docs-serve'
    cmds:
    - "echo \"\U0001F4DA Serving documentation...\""
    - .venv/bin/python -m mkdocs serve
  profile:
    desc: '[imported from Makefile] profile'
    cmds:
    - "echo \"\U0001F4CA Running performance profile...\""
    - .venv/bin/python -m cProfile -o profile.stats -m llx analyze .
    - .venv/bin/python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative');
      p.print_stats(20)"
  security:
    desc: '[imported from Makefile] security'
    cmds:
    - "echo \"\U0001F512 Running security scan...\""
    - .venv/bin/pip install safety bandit
    - .venv/bin/safety check
    - .venv/bin/bandit -r llx/
  db-reset:
    desc: '[imported from Makefile] db-reset'
    cmds:
    - "echo \"\U0001F5C4\uFE0F  Resetting database...\""
    - docker exec llx-postgres-prod psql -U llx -d llx -c "DROP SCHEMA IF EXISTS llx
      CASCADE; CREATE SCHEMA llx;"
    - docker exec llx-postgres-prod psql -U llx -d llx -f /docker-entrypoint-initdb.d/init.sql
  db-migrate:
    desc: '[imported from Makefile] db-migrate'
    cmds:
    - "echo \"\U0001F5C4\uFE0F  Running database migrations...\""
    - '# Add migration commands here'
  env-dev:
    desc: '[imported from Makefile] env-dev'
    cmds:
    - "echo \"\U0001F527 Setting up development environment...\""
    - cp .env.example .env.dev
    - "echo \"\u2705 Created .env.dev - please edit with your values\""
  env-prod:
    desc: '[imported from Makefile] env-prod'
    cmds:
    - "echo \"\U0001F527 Setting up production environment...\""
    - cp .env.example .env.prod
    - "echo \"\u2705 Created .env.prod - please edit with production values\""
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  import-makefile-hint:
    desc: '[from doql] workflow: import-makefile-hint'
    cmds:
    - 'echo ''Run: taskfile import Makefile to import existing targets.'''
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
  sumd:
    desc: Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description
    cmds:
    - |
      echo "# $(basename $(pwd))" > SUMD.md
      echo "" >> SUMD.md
      echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Contents" >> SUMD.md
      echo "" >> SUMD.md
      echo "- [Metadata](#metadata)" >> SUMD.md
      echo "- [Architecture](#architecture)" >> SUMD.md
      echo "- [Dependencies](#dependencies)" >> SUMD.md
      echo "- [Source Map](#source-map)" >> SUMD.md
      echo "- [Intent](#intent)" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Metadata" >> SUMD.md
      echo "" >> SUMD.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
      echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
      echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
      echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
      echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Architecture" >> SUMD.md
      echo "" >> SUMD.md
      echo '```' >> SUMD.md
      echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
      echo '```' >> SUMD.md
      echo "" >> SUMD.md
      echo "## Source Map" >> SUMD.md
      echo "" >> SUMD.md
      find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
      echo "Generated SUMD.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      project_name = Path.cwd().name
      py_files = list(Path('.').rglob('*.py'))
      py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
      data = {
          'project_name': project_name,
          'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
          'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
      }
      with open('sumd.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated sumd.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
  sumr:
    desc: Generate SUMR (Summary Report) with project metrics and health status
    cmds:
    - |
      echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
      echo "" >> SUMR.md
      echo "SUMR - Summary Report for project analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Contents" >> SUMR.md
      echo "" >> SUMR.md
      echo "- [Metadata](#metadata)" >> SUMR.md
      echo "- [Quality Status](#quality-status)" >> SUMR.md
      echo "- [Metrics](#metrics)" >> SUMR.md
      echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
      echo "- [Intent](#intent)" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Metadata" >> SUMR.md
      echo "" >> SUMR.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
      echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Quality Status" >> SUMR.md
      echo "" >> SUMR.md
      if [ -f pyqual.yaml ]; then
        echo "- **pyqual_config**: ✅ Present" >> SUMR.md
        echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
      else
        echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
      fi
      echo "" >> SUMR.md
      echo "## Metrics" >> SUMR.md
      echo "" >> SUMR.md
      py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
      echo "- **python_files**: $py_files" >> SUMR.md
      lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
      echo "- **total_lines**: $lines" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Refactoring Analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
      echo "Generated SUMR.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      from datetime import datetime
      project_name = Path.cwd().name
      py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
      data = {
          'project_name': project_name,
          'report_type': 'SUMR',
          'generated_at': datetime.now().isoformat(),
          'metrics': {
              'python_files': py_files,
              'has_pyqual_config': Path('pyqual.yaml').exists()
          }
      }
      with open('SUMR.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated SUMR.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
# Pyqual Pipeline Configuration
# See docs/GITHUB_PUSH_PROTECTION.md for troubleshooting push protection issues

pipeline:
  name: llx-quality-loop-with-aider
  metrics:
    cc_max: 10
    vallm_pass_min: 50
    coverage_min: 20
  stages:
  - name: test
    run: .venv/bin/pytest --cov=llx --cov-report=json:.pyqual/coverage.json -q
    when: always
    env:
      OPENROUTER_API_KEY: dummy-key-for-ci
  # Security: Check for known vulnerabilities in dependencies
  - name: security-audit
    run: .venv/bin/python -m llx.pyqual_plugins.security_audit
    when: always
    optional: true
    timeout: 120
  # Code Quality: Fast linting with ruff
  - name: lint
    run: .venv/bin/python -m llx.pyqual_plugins.lint
    when: always
    optional: true
    timeout: 60
  # Type Checking: Static type analysis with mypy
  - name: type-check
    run: .venv/bin/python -m llx.pyqual_plugins.type_check
    when: always
    optional: true
    timeout: 120
  # Detect Secrets: Scan for hardcoded secrets and credentials
  - name: detect-secrets
    run: .venv/bin/python -m llx.pyqual_plugins.detect_secrets
    when: always
    optional: true
    timeout: 60
  - name: prefact
    tool: prefact
    optional: true
    when: metrics_fail
    timeout: 300
  - name: fix
    run: llx fix . --apply --errors TODO.md --verbose
    when: metrics_fail
    timeout: 1800
  - name: verify
    run: echo "Skipping vallm verify on large project" || vallm batch ./ --recursive
      --format toon --output ./project
    optional: true
    when: after_fix
    timeout: 30
  # Auto-bump version if already on PyPI
  - name: bump-version
    run: .venv/bin/python -m llx.pyqual_plugins.bump_version
    when: metrics_pass
    timeout: 30
  - name: build
    run: .venv/bin/python -m build
    when: metrics_pass
    timeout: 120
  # Idempotent publish - skips if version exists
  - name: publish
    run: .venv/bin/python -m llx.pyqual_plugins.publish
    optional: true
    when: metrics_pass
    timeout: 120
  # NOTE: Push stage auto-commits and pushes. If GitHub Push Protection blocks,
  # see docs/GITHUB_PUSH_PROTECTION.md for remediation steps
  - name: push
    run: |
      git add -A
      if git diff --cached --quiet; then
        echo "No changes to commit"
      else
        git commit -m "chore: auto-commit from pyqual run"
      fi
      git push origin main
    when: always
    timeout: 30
  # Verify deployment with retries
  - name: verify-push-publish
    run: .venv/bin/python -m llx.pyqual_plugins.verify_push_publish
    when: always
    timeout: 60
  loop:
    max_iterations: 3
    on_fail: create_ticket
  env:
    LLM_MODEL: openrouter/openai/gpt-5-mini
    LLX_CODE_TOOL: internal
    LLX_DEFAULT_TIER: balanced
    LLX_VERBOSE: true
    PATH: ".venv/bin:/usr/local/bin:/usr/bin:/bin"
```

## Configuration

```yaml
project:
  name: llx
  version: 0.1.58
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
typer>=0.24
rich>=13.0
pydantic>=2.0
pydantic-settings>=2.0
pydantic-yaml>=1.0
tomli>=2.0; python_version<'3.11'
httpx>=0.27
pyyaml>=6.0
requests>=2.31
docker>=6.0
psutil>=5.9
planfile>=0.1.30
```

### Development

```text markpact:deps python scope=dev
pytest>=8.0
pytest-cov>=5.0
ruff>=0.5
mypy>=1.10
goal>=2.1.0
costs>=0.1.20
click<8.1.0
pfix>=0.1.60
pyqual>=0.1.36
starlette>=0.37
sse-starlette>=2.0
uvicorn>=0.29
```

## Deployment

```bash markpact:run
pip install llx

# development install
pip install -e .[dev]
```

### Requirements Files

#### `requirements-dev.txt`

- `pytest>=8.0`
- `pytest-cov>=5.0`
- `ruff>=0.5`
- `mypy>=1.10`
- `black>=23.0`
- `isort>=5.0`
- `flake8>=6.0`
- `requests>=2.31`
- `redis>=5.0`

#### `requirements.txt`

- `typer>=0.12`
- `rich>=13.0`
- `pydantic>=2.0`
- `pydantic-settings>=2.0`
- `tomli>=2.0; python_version<'3.11'`
- `httpx>=0.27`
- `pyyaml>=6.0`
- `litellm>=1.40`
- `code2llm>=0.5.80`
- `redup>=0.4.15`
- `vallm>=0.1.65`
- `ollama>=0.3`

### Docker

- **base image**: `python:3.11-slim AS builder`
- **expose**: `4000`
- **entrypoint**: `["python", "-m", "llx", "proxy", "start"]`
- **label** `maintainer`: Tom Sapletta <tom@sapletta.org>
- **label** `org.label-schema.build-date`: $BUILD_DATE
- **label** `org.label-schema.name`: llx
- **label** `org.label-schema.description`: Intelligent LLM model router driven by real code metrics
- **label** `org.label-schema.url`: https://github.com/wronai/llx
- **label** `org.label-schema.vcs-ref`: $VCS_REF
- **label** `org.label-schema.vcs-url`: https://github.com/wronai/llx
- **label** `org.label-schema.vendor`: Tom Sapletta
- **label** `org.label-schema.version`: $VERSION

### Docker Compose (`docker-compose.yml`)

- **llx-api** image=`{'context': '.', 'dockerfile': 'Dockerfile'}` ports: `4000:4000`
- **redis** image=`redis:7-alpine` ports: `6379:6379`
- **postgres** image=`postgres:15-alpine` ports: `5432:5432`
- **webui** image=`ghcr.io/open-webui/open-webui:main` ports: `3000:8080`
- **vscode-server** image=`linuxserver/vscode-server:latest` ports: `8080:8443`
- **code-server** image=`codercom/code-server:latest` ports: `8443:8080`
- **grafana** image=`grafana/grafana:latest` ports: `3001:3000`
- **prometheus** image=`prom/prometheus:latest` ports: `9090:9090`
- **loki** image=`grafana/loki:latest` ports: `3100:3100`
- **promtail** image=`grafana/promtail:latest`
- **nginx** image=`nginx:alpine` ports: `80:80`, `443:443`
- **backup** image=`postgres:15-alpine`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Anthropic Claude (Opus, Sonnet, Haiku) |
| `OPENAI_API_KEY` | `sk-...` | OpenAI (GPT-4, GPT-4o, GPT-4o-mini) |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | OpenRouter (300+ models, single key) - RECOMMENDED FOR FREE TIER |
| `GOOGLE_AI_KEY` | `AIza...` | Google AI Studio (Gemini 2.5 Pro/Flash) |
| `DEEPSEEK_API_KEY` | `sk-...` | DeepSeek (V3, R1 - cheapest cloud) |
| `GROQ_API_KEY` | `gsk_...` | Groq (ultra-fast inference) |
| `TOGETHER_API_KEY` | `...` | Together AI (open-source models) |
| `MISTRAL_API_KEY` | `...` | Mistral (Codestral, Mistral Large) |
| `LLX_DEFAULT_PORT` | `8000` | Default server configuration |
| `LLX_DEFAULT_HOST` | `0.0.0.0` |  |
| `LLX_DEFAULT_URL` | `http://localhost:8000` |  |
| `LLX_DEFAULT_PROFILE` | `cheap` | Default generation settings |
| `LLX_DEFAULT_SPRINTS` | `8` |  |
| `LLX_DEFAULT_FOCUS` | `api` |  |
| `LLX_MONITOR_INTERVAL` | `30` | Monitoring settings |
| `LLX_AUTO_INSTALL` | `true` |  |
| `LLX_TOOL` | `llx` | Tool preferences |
| `ENVIRONMENT` | `local` |  |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`llx`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `llx/__init__.py:__version__`

## Makefile Targets

- `help` — Default target
- `install` — Installation
- `install-tools`
- `dev` — Development environments
- `prod`
- `test` — Testing
- `test-docker`
- `lint`
- `format`
- `docker-dev` — Docker commands
- `docker-prod`
- `docker-stop`
- `docker-clean`
- `docker-logs`
- `docker-status`
- `examples-basic` — Examples
- `examples-proxy`
- `examples-docker`
- `examples-multi`
- `examples-local`
- `examples-all`
- `clean` — Utilities
- `doctor`
- `backup`
- `quick-test` — Development shortcuts
- `quick-start`
- `ci-install` — CI/CD helpers
- `ci-test`
- `ci-lint`
- `ci-build`
- `publish` — Release helpers
- `publish-confirm`
- `publish-test`
- `version`
- `tag`
- `docs` — Documentation
- `docs-serve`
- `profile` — Performance profiling
- `security` — Security scanning
- `db-reset` — Database operations
- `db-migrate`
- `env-dev` — Environment management
- `env-prod`
- `up` — Quick commands for common tasks
- `down`
- `logs`
- `ps`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# llx | 250f 44567L | python:217,shell:31,css:1,less:1 | 2026-04-25
# stats: 598 func | 289 cls | 250 mod | CC̄=3.5 | critical:29 | cycles:0
# alerts[5]: CC _collect_file_context=20; CC main=19; CC _parse_unified_hunks=16; CC main=15; CC issue_text=15
# hotspots[5]: main fan=25; execute_v3_pipeline fan=23; main fan=22; create_service_app fan=20; main fan=20
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[250]:
  ai-tools-manage.sh,352
  app.doql.css,562
  app.doql.less,834
  docker/ai-tools/entrypoint.sh,176
  docker/ai-tools/install-tools.sh,370
  docker/ollama/entrypoint.sh,32
  docker/vscode/install-extensions.sh,410
  docker-manage.sh,407
  examples/ai-tools/run.sh,33
  examples/aider/run.sh,32
  examples/basic/run.sh,43
  examples/cleanup.sh,22
  examples/cli-tools/run.sh,27
  examples/cloud-local/run.sh,33
  examples/docker/docker.sh,386
  examples/docker/run.sh,32
  examples/filtering/filtering.sh,295
  examples/filtering/run.sh,44
  examples/fullstack/generate_simple.sh,277
  examples/fullstack/run.sh,28
  examples/hybrid/hybrid.sh,348
  examples/hybrid/run.sh,28
  examples/local/run.sh,28
  examples/multi-provider/run.sh,29
  examples/planfile/run.sh,43
  examples/privacy/advanced/01_api_integration.py,540
  examples/privacy/advanced/02_multi_stage.py,437
  examples/privacy/advanced/03_cicd_integration.py,407
  examples/privacy/basic/01_text_anonymization.py,78
  examples/privacy/basic/02_custom_patterns.py,87
  examples/privacy/ml/01_entropy_ml_detection.py,507
  examples/privacy/ml/02_hybrid_system.py,231
  examples/privacy/ml/03_contextual_passwords.py,463
  examples/privacy/ml/04_behavioral_learning.py,483
  examples/privacy/streaming/01_streaming_anonymization.py,126
  examples/proxy/run.sh,28
  examples/pyqual-llx-demo.sh,56
  examples/python-api/run.sh,42
  examples/python-api/setup-aliases.sh,57
  examples/run.sh,196
  examples/vscode-roocode/run.sh,28
  generate.sh,29
  llx/__init__.py,37
  llx/__main__.py,5
  llx/analysis/__init__.py,2
  llx/analysis/collector.py,483
  llx/analysis/runner.py,83
  llx/cli/__init__.py,4
  llx/cli/app.py,413
  llx/cli/commands/analyze.py,31
  llx/cli/commands/planner.py,25
  llx/cli/formatters.py,313
  llx/cli/strategy_commands.py,111
  llx/commands/__init__.py,2
  llx/commands/_patch_apply.py,111
  llx/commands/fix.py,218
  llx/config.py,377
  llx/detection/__init__.py,6
  llx/detection/detector.py,105
  llx/examples/utils.py,241
  llx/integrations/__init__.py,2
  llx/integrations/context_builder.py,176
  llx/integrations/proxy.py,132
  llx/integrations/proxym.py,332
  llx/litellm_config.py,152
  llx/llm.py,172
  llx/mcp/__init__.py,27
  llx/mcp/__main__.py,9
  llx/mcp/client.py,107
  llx/mcp/server.py,142
  llx/mcp/service.py,244
  llx/mcp/tools.py,996
  llx/mcp/workflows.py,147
  llx/orchestration/__init__.py,36
  llx/orchestration/_utils.py,38
  llx/orchestration/cli.py,194
  llx/orchestration/cli_utils.py,165
  llx/orchestration/instances/__init__.py,15
  llx/orchestration/instances/cli.py,150
  llx/orchestration/instances/manager.py,557
  llx/orchestration/instances/models.py,62
  llx/orchestration/instances/ports.py,65
  llx/orchestration/llm/__init__.py,26
  llx/orchestration/llm/cli.py,159
  llx/orchestration/llm/executors.py,224
  llx/orchestration/llm/health.py,37
  llx/orchestration/llm/models.py,102
  llx/orchestration/llm/orchestrator.py,643
  llx/orchestration/queue/__init__.py,14
  llx/orchestration/queue/cli.py,150
  llx/orchestration/queue/manager.py,496
  llx/orchestration/queue/models.py,76
  llx/orchestration/ratelimit/__init__.py,12
  llx/orchestration/ratelimit/_crud.py,42
  llx/orchestration/ratelimit/_persistence.py,113
  llx/orchestration/ratelimit/cli.py,137
  llx/orchestration/ratelimit/limiter.py,509
  llx/orchestration/ratelimit/models.py,43
  llx/orchestration/routing/__init__.py,22
  llx/orchestration/routing/cli.py,118
  llx/orchestration/routing/engine.py,639
  llx/orchestration/routing/models.py,76
  llx/orchestration/session/__init__.py,13
  llx/orchestration/session/cli.py,115
  llx/orchestration/session/manager.py,446
  llx/orchestration/session/models.py,55
  llx/orchestration/utils/_cmd_cleanup.py,25
  llx/orchestration/utils/_cmd_remove.py,36
  llx/orchestration/utils/_cmd_status.py,41
  llx/orchestration/vscode/__init__.py,15
  llx/orchestration/vscode/cli.py,184
  llx/orchestration/vscode/config_io.py,143
  llx/orchestration/vscode/defaults.py,23
  llx/orchestration/vscode/models.py,62
  llx/orchestration/vscode/orchestrator.py,596
  llx/orchestration/vscode/ports.py,44
  llx/planfile/__init__.py,90
  llx/planfile/builder.py,373
  llx/planfile/builder_simple.py,267
  llx/planfile/config.py,125
  llx/planfile/examples.py,142
  llx/planfile/executor_simple.py,277
  llx/planfile/generate_strategy.py,471
  llx/planfile/model_selector.py,280
  llx/planfile/models.py,160
  llx/planfile/runner.py,264
  llx/prellm/__init__.py,122
  llx/prellm/_nfo_compat.py,221
  llx/prellm/agents/__init__.py,12
  llx/prellm/agents/executor.py,129
  llx/prellm/agents/preprocessor.py,189
  llx/prellm/analyzers/__init__.py,2
  llx/prellm/analyzers/context_engine.py,249
  llx/prellm/budget.py,234
  llx/prellm/chains/__init__.py,1
  llx/prellm/chains/process_chain.py,276
  llx/prellm/cli.py,279
  llx/prellm/cli_commands.py,367
  llx/prellm/cli_config.py,233
  llx/prellm/cli_context.py,102
  llx/prellm/cli_query.py,187
  llx/prellm/context/__init__.py,18
  llx/prellm/context/codebase_indexer.py,419
  llx/prellm/context/folder_compressor.py,225
  llx/prellm/context/schema_generator.py,212
  llx/prellm/context/sensitive_filter.py,263
  llx/prellm/context/shell_collector.py,170
  llx/prellm/context/user_memory.py,362
  llx/prellm/context_ops.py,182
  llx/prellm/core.py,469
  llx/prellm/env_config.py,81
  llx/prellm/extractors.py,230
  llx/prellm/llm_provider.py,151
  llx/prellm/logging_setup.py,104
  llx/prellm/model_catalog.py,79
  llx/prellm/models.py,433
  llx/prellm/pipeline/__init__.py,13
  llx/prellm/pipeline/algo_handlers.py,63
  llx/prellm/pipeline/config.py,49
  llx/prellm/pipeline/engine.py,106
  llx/prellm/pipeline/loader.py,64
  llx/prellm/pipeline.py,484
  llx/prellm/pipeline_ops.py,258
  llx/prellm/prompt_registry.py,186
  llx/prellm/query_decomposer.py,331
  llx/prellm/server.py,448
  llx/prellm/trace.py,649
  llx/prellm/utils/__init__.py,7
  llx/prellm/utils/lazy_imports.py,22
  llx/prellm/utils/lazy_loader.py,21
  llx/prellm/validators.py,213
  llx/privacy/__core.py,292
  llx/privacy/__init__.py,57
  llx/privacy/_project_anonymizer.py,139
  llx/privacy/_project_ast.py,227
  llx/privacy/_project_context.py,186
  llx/privacy/_streaming_chunking.py,149
  llx/privacy/_streaming_impl.py,296
  llx/privacy/_streaming_parallel.py,52
  llx/privacy/deanonymize.py,425
  llx/privacy/deanonymize_engine.py,102
  llx/privacy/deanonymize_results.py,24
  llx/privacy/deanonymize_utils.py,73
  llx/privacy/project.py,45
  llx/privacy/streaming.py,44
  llx/pyqual_plugins/__init__.py,8
  llx/pyqual_plugins/bump_version.py,126
  llx/pyqual_plugins/detect_secrets.py,66
  llx/pyqual_plugins/lint.py,87
  llx/pyqual_plugins/publish.py,75
  llx/pyqual_plugins/security_audit.py,86
  llx/pyqual_plugins/type_check.py,72
  llx/pyqual_plugins/verify_push_publish.py,105
  llx/routing/__init__.py,2
  llx/routing/client.py,288
  llx/routing/selector.py,282
  llx/tools/__init__.py,23
  llx/tools/_docker.py,54
  llx/tools/_utils.py,7
  llx/tools/ai_tools_manager.py,242
  llx/tools/cli.py,134
  llx/tools/config_manager.py,795
  llx/tools/docker_manager.py,553
  llx/tools/health_checker.py,590
  llx/tools/health_runner.py,267
  llx/tools/model_manager.py,757
  llx/tools/utils/_cmd_uninstall_extension.py,32
  llx/tools/vscode_manager.py,792
  llx/utils/aider.py,193
  llx/utils/cli_main.py,31
  llx/utils/formatting.py,86
  llx/utils/issues.py,272
  llx/utils/models.py,30
  my-api/__init__.py,5
  my-api/main.py,107
  my-api/models.py,42
  my-api/monitoring.py,125
  my-api/test_api.py,98
  my-api/tests/test_my_api.py,12
  project.sh,46
  scripts/pyqual_auto.py,258
  simple_generate.py,72
  test-api-qwen/__init__.py,5
  test-api-qwen/main.py,122
  test-api-qwen/models.py,19
  test-api-qwen/test_api.py,170
  test-api-qwen/tests/test_test_api_qwen.py,12
  test-local-chat.py,187
  test_aider_docker.py,72
  test_aider_mcp.py,66
  test_cli.py,10
  test_strategy_integration.py,88
  tests/__init__.py,1
  tests/privacy/test_anonymizer.py,35
  tests/privacy/test_context.py,46
  tests/privacy/test_deanonymizer.py,20
  tests/test_aider_mcp.py,96
  tests/test_anonymization_context.py,70
  tests/test_core.py,214
  tests/test_detection.py,118
  tests/test_fix_aider_mode.py,82
  tests/test_mcp.py,148
  tests/test_prellm_integration.py,143
  tests/test_privacy.py,315
  tests/test_privacy_extended.py,740
  tests/test_privacy_project.py,506
  tests/test_project_anonymizer.py,89
  tests/test_project_deanonymizer.py,69
  tests/test_proxym_integration.py,190
  trace.py,50
D:
  examples/privacy/advanced/01_api_integration.py:
    e: create_realistic_project,main,SimulatedLLMResponse,SimulatedLLMAPI
    SimulatedLLMResponse:  # Simulated LLM API response.
    SimulatedLLMAPI: __init__(1),send_prompt(2)  # Simulates external LLM API (like OpenAI, Anthropic, etc.).
    create_realistic_project(base_path)
    main()
  examples/privacy/advanced/02_multi_stage.py:
    e: create_business_logic_project,main,AnonymizationLevel,MultiStageAnonymizer
    AnonymizationLevel:  # Configuration for a specific anonymization level.
    MultiStageAnonymizer: __init__(1),anonymize_for_level(2),get_comparison(2)  # Manages multiple anonymization levels for different use case
    create_business_logic_project(base_path)
    main()
  examples/privacy/advanced/03_cicd_integration.py:
    e: create_cicd_project,main,SecurityScanResult,CICDPrivacyPipeline
    SecurityScanResult:  # Result of security scan.
    CICDPrivacyPipeline: __init__(1),step1_pre_commit_scan(0),_assess_risk(1),step2_anonymize_for_audit(1),step3_simulate_audit_response(1),step4_generate_report(1)  # Privacy pipeline for CI/CD integration.
    create_cicd_project(base_path)
    main()
  examples/privacy/basic/01_text_anonymization.py:
    e: main
    main()
  examples/privacy/basic/02_custom_patterns.py:
    e: main
    main()
  examples/privacy/ml/01_entropy_ml_detection.py:
    e: create_complex_project,main,EntropyResult,EntropyAnalyzer,MLBasedAnonymizer
    EntropyResult:  # Result of entropy analysis.
    EntropyAnalyzer: calculate_entropy(1),analyze_randomness(2),_classify_by_context(3),find_high_entropy_strings(2)  # Analyzes text entropy to detect random/pseudorandom strings.
    MLBasedAnonymizer: __init__(0),analyze_with_ml(1),_entropy_confidence(1),_detect_contextual_passwords(1),_detect_pii_semantic(1),anonymize_with_ml(1)  # Anonymizer using ML/NLP techniques beyond simple regex.
    create_complex_project(base_path)
    main()
  examples/privacy/ml/02_hybrid_system.py:
    e: DetectionResult,HybridAnonymizer
    DetectionResult:  # Result from hybrid detection.
    HybridAnonymizer: __init__(0),calculate_entropy(1),detect_with_regex(1),detect_ml_entropy(1),detect_ml_context(1),_classify_entropy_string(2),hybrid_detect(1),_merge_results(1),sort_detections(1),create_anonymization_mask(2),perform_anonymization(2),collect_anonymization_stats(1),hybrid_anonymize(1)  # Combines regex and ML detection for maximum coverage.
  examples/privacy/ml/03_contextual_passwords.py:
    e: create_test_code_samples,main,PasswordCandidate,ContextualPasswordDetector
    PasswordCandidate:  # Candidate password detection result.
    ContextualPasswordDetector: __init__(0),_compile_patterns(0),detect_passwords(1),_is_likely_password(3),_calculate_confidence(4),_calculate_password_complexity(1),_calculate_entropy(1),analyze_code(1)  # Detects passwords based on code context and NLP patterns.
    create_test_code_samples()
    main()
  examples/privacy/ml/04_behavioral_learning.py:
    e: create_sample_codebase,main,LearnedPattern,FalsePositiveRecord,BehavioralPasswordDetector
    LearnedPattern:  # A pattern learned from user code.
    FalsePositiveRecord:  # Record of a false positive for learning.
    BehavioralPasswordDetector: __init__(1),_load_learning(0),_save_learning(0),learn_from_codebase(1),_analyze_file(2),_update_learned_patterns(1),report_false_positive(4),is_false_positive(2),calculate_adaptive_confidence(3),_calculate_entropy(1),generate_custom_patterns(0),get_learning_stats(0)  # Learns and adapts to user coding patterns.
    create_sample_codebase(base_path)
    main()
  examples/privacy/streaming/01_streaming_anonymization.py:
    e: create_large_project,main
    create_large_project(base_path;num_files)
    main()
  llx/__init__.py:
  llx/__main__.py:
  llx/analysis/__init__.py:
  llx/analysis/collector.py:
    e: analyze_project,_collect_filesystem_metrics,_collect_code2llm_metrics,_apply_analysis_yaml,_extract_metrics_target,_extract_evolution_stats,_extract_evolution_actions,_apply_evolution_yaml,_apply_evolution_text,_apply_map_yaml,_parse_map_stats_line,_parse_map_alerts_line,_parse_map_hotspots_line,_count_map_modules,_apply_map_text,_collect_redup_metrics,_collect_vallm_metrics,_load_file,_extract_cc_value,_estimate_context_tokens,_classify_scope,ProjectMetrics
    ProjectMetrics: complexity_score(0),scale_score(0),coupling_score(0)  # Aggregated project metrics that drive model selection.
    analyze_project(project_path)
    _collect_filesystem_metrics(root;m)
    _collect_code2llm_metrics(search_dir;m)
    _apply_analysis_yaml(data;m)
    _extract_metrics_target(mt;m)
    _extract_evolution_stats(stats;m)
    _extract_evolution_actions(actions;m)
    _apply_evolution_yaml(data;m)
    _apply_evolution_text(text;m)
    _apply_map_yaml(data;m)
    _parse_map_stats_line(line;m)
    _parse_map_alerts_line(line;m)
    _parse_map_hotspots_line(line;m)
    _count_map_modules(text;m)
    _apply_map_text(text;m)
    _collect_redup_metrics(search_dir;m)
    _collect_vallm_metrics(search_dir;m)
    _load_file(directory;candidates)
    _extract_cc_value(msg)
    _estimate_context_tokens(m)
    _classify_scope(m)
  llx/analysis/runner.py:
    e: check_tool,_run_tool,run_code2llm,run_redup,run_vallm,run_all_tools,ToolResult
    ToolResult:
    check_tool(name)
    _run_tool(tool;cmd;output_dir;timeout)
    run_code2llm(project_path;output_dir;fmt)
    run_redup(project_path;output_dir;fmt)
    run_vallm(project_path;output_dir)
    run_all_tools(project_path;output_dir;on_progress)
  llx/cli/__init__.py:
  llx/cli/app.py:
    e: _run_analysis_tools,analyze,select,chat,proxy_start,proxy_config,proxy_status,mcp_start,plan_generate,plan_review,plan_execute,models,info,fix,init,_get_model_for_profile,_load_sprint_mapping,_generate_sprint_code,_plan_code_impl
    _run_analysis_tools(project_path;config)
    analyze(path;toon_dir;task;local;max_tier;run_tools;verbose;json_output)
    select(path;toon_dir;task;local)
    chat(path;prompt;toon_dir;task;model_override;local;free)
    proxy_start(config_path;port;background)
    proxy_config(output)
    proxy_status()
    mcp_start(mode;port)
    plan_generate(strategy;output_dir;model;profile)
    plan_review(strategy;project_path)
    plan_execute(strategy;project_path;backend;dry_run)
    models(tag;provider;tier)
    info()
    fix(workdir;errors;apply;model;dry_run;verbose)
    init(path)
    _get_model_for_profile(profile;selector)
    _load_sprint_mapping(project_name;description)
    _generate_sprint_code(client;sprint;sprint_files;project_name;description;out;selected_model)
    _plan_code_impl(strategy;out;model;profile)
  llx/cli/commands/analyze.py:
    e: analyze
    analyze(path;toon_dir;task;local;max_tier;run_tools;verbose;json_output)
  llx/cli/commands/planner.py:
    e: _plan_code_impl
    _plan_code_impl(strategy;out;model;profile)
  llx/cli/formatters.py:
    e: output_rich,output_json,_filter_models,_build_model_row,_render_models_table,_build_title,print_models_table,_render_tools_table,_render_tiers_table,_render_agents_table,_render_tags_legend,print_info_tables
    output_rich(metrics;result;verbose)
    output_json(metrics;result)
    _filter_models(models;tag;provider;tier)
    _build_model_row(model)
    _render_models_table(rows;title)
    _build_title(tag;provider;tier)
    print_models_table(config;tag;provider;tier)
    _render_tools_table()
    _render_tiers_table(config)
    _render_agents_table()
    _render_tags_legend()
    print_info_tables(config)
  llx/cli/strategy_commands.py:
    e: create_strategy,validate_strategy,run_strategy_command,verify_strategy,add_strategy_commands
    create_strategy(output;model;local)
    validate_strategy(strategy_file)
    run_strategy_command(strategy_file;project_path;backend;dry_run)
    verify_strategy(strategy_file;project_path;backend)
    add_strategy_commands(main_app)
  llx/commands/__init__.py:
  llx/commands/_patch_apply.py:
    e: _extract_json_from_content,_apply_unified_diff,_parse_unified_hunks,_find_hunk_position
    _extract_json_from_content(content)
    _apply_unified_diff(file_path;patch_text)
    _parse_unified_hunks(patch_text)
    _find_hunk_position(lines;removed_lines;hint)
  llx/commands/fix.py:
    e: apply_code_changes,load_errors_data,select_model_for_fix,display_model_selection_and_metrics,prepare_fix_prompt,handle_dry_run,execute_aider_fix,execute_prellm_fix,fix
    apply_code_changes(workdir;content)
    load_errors_data(errors;console)
    select_model_for_fix(model;metrics;config;console)
    display_model_selection_and_metrics(selection;selected_model_id;metrics;console)
    prepare_fix_prompt(workdir_path;errors_data;selected_model_id;selection)
    handle_dry_run(prompt;console)
    execute_aider_fix(workdir_path;prompt;selected_model_id;issues_for_prompt;config;apply;verbose;console)
    execute_prellm_fix(workdir_path;prompt;selected_model_id;config;apply;verbose;console)
    fix(workdir;errors;apply;model;dry_run;verbose)
  llx/config.py:
    e: normalize_litellm_base_url,_apply_toml,_apply_yaml_thresholds,_apply_yaml_models,_apply_yaml_proxy,_apply_yaml,_apply_env,ModelConfig,TierThresholds,ProxyConfig,LlxConfig
    ModelConfig:  # Configuration for a single model tier.
    TierThresholds:  # Thresholds that determine which model tier to use.
    ProxyConfig:  # LiteLLM proxy settings.
    LlxConfig: __post_init__(0),load(2)  # Root configuration for llx.
    normalize_litellm_base_url(base_url)
    _apply_toml(config;data)
    _apply_yaml_thresholds(config;thresholds)
    _apply_yaml_models(config;models)
    _apply_yaml_proxy(config;proxy)
    _apply_yaml(config;data)
    _apply_env(config)
  llx/detection/__init__.py:
  llx/detection/detector.py:
    e: ProjectTypeDetector
    ProjectTypeDetector: __init__(0),detect_from_path(1),detect_from_files(1),detect_from_config(1),get_project_config(1),get_all_types(0),detect(1)  # Detects project type from directory name and files.
  llx/examples/utils.py:
    e: ExampleHelper,TaskQueue,WorkflowRunner
    ExampleHelper: ensure_venv(0),check_dependencies(0),check_ollama(0),select_model(4),run_llx_chat(5),save_history(3),create_project_structure(3),get_app_template(1),setup_project(1)  # Helper class for common example operations.
    TaskQueue: __init__(1),add(1),process(1)  # Simple task queue for batch processing.
    WorkflowRunner: run_workflow(2)  # Run predefined workflows.
  llx/integrations/__init__.py:
  llx/integrations/context_builder.py:
    e: build_context,_build_summary,_format_health,_format_evolution,_format_map_details,_format_duplication,_load_toon
    build_context(project_path;metrics;tier)
    _build_summary(m)
    _format_health(analysis)
    _format_evolution(data)
    _format_map_details(data)
    _format_duplication(m)
    _load_toon(directory;filename)
  llx/integrations/proxy.py:
    e: generate_proxy_config,start_proxy,check_proxy
    generate_proxy_config(config;output_path)
    start_proxy(config)
    check_proxy(base_url)
  llx/integrations/proxym.py:
    e: _tier_to_proxym,_build_llx_headers,ProxymStatus,ProxymResponse,ProxymClient
    ProxymStatus:  # Status of the proxym proxy server.
    ProxymResponse: prompt_tokens(0),completion_tokens(0),total_tokens(0)  # Response from proxym chat completion.
    ProxymClient: __init__(3),is_available(0),status(0),chat(1),chat_with_analysis(2),list_models(0),_parse_response(1),close(0),__enter__(0),__exit__(0)  # Client for proxym intelligent AI proxy.
    _tier_to_proxym(tier)
    _build_llx_headers(metrics;tier)
  llx/litellm_config.py:
    e: load_litellm_config,LiteLLMModelConfig,LiteLLMConfig
    LiteLLMModelConfig:  # Configuration for a single LiteLLM model.
    LiteLLMConfig: load(2),_default_config(1),get_model_config(1),get_models_by_tag(1),get_models_by_provider(1),get_models_by_tier(1),resolve_alias(1),to_llx_models(0),get_proxy_config(0)  # Complete LiteLLM configuration.
    load_litellm_config(project_path)
  llx/llm.py:
    e: _load_dotenv_fallback,_ensure_dotenv_loaded,get_llm_model,get_api_key,get_llm,LLMResponse,LLM
    LLMResponse:  # Response from an LLM call.
    LLM: __init__(2),complete(4),fix_code(3)  # Synchronous LiteLLM wrapper with .env configuration.
    _load_dotenv_fallback(env_path)
    _ensure_dotenv_loaded()
    get_llm_model()
    get_api_key()
    get_llm(model)
  llx/mcp/__init__.py:
  llx/mcp/__main__.py:
  llx/mcp/client.py:
    e: LlxMcpClient
    LlxMcpClient: __init__(1),_session(0),_extract_text_payload(1),call_tool(2),analyze(3),fix_with_aider(6)  # Thin MCP client for the llx SSE service.
  llx/mcp/server.py:
    e: list_tools,call_tool,run_stdio_server,create_app,run_sse_server,build_parser,main,main_sync
    list_tools()
    call_tool(name;arguments)
    run_stdio_server()
    create_app()
    run_sse_server(host;port)
    build_parser()
    main(argv)
    main_sync(argv)
  llx/mcp/service.py:
    e: _escape_label_value,create_service_app,run_service,build_parser,main,McpServiceState
    McpServiceState: mark_request(1),mark_session_open(0),mark_session_close(0),mark_message(1),mark_error(1),uptime_seconds(0),last_activity_seconds_ago(0),health_payload(0),metrics_text(0)  # Runtime state exposed via health and metrics endpoints.
    _escape_label_value(value)
    create_service_app(state;llx_server)
    run_service(host;port;state)
    build_parser()
    main(argv)
  llx/mcp/tools.py:
    e: _handle_llx_analyze,_handle_llx_select,_handle_llx_chat,_handle_code2llm_analyze,_handle_redup_scan,_handle_vallm_validate,_handle_llx_preprocess,_handle_llx_context,_handle_llx_proxy_status,_handle_llx_proxym_status,_handle_llx_proxym_chat,_handle_aider,_handle_planfile_generate,_handle_planfile_apply,_handle_llx_project_anonymize,_handle_llx_project_deanonymize,_handle_llx_privacy_scan,McpTool
    McpTool:
    _handle_llx_analyze(args)
    _handle_llx_select(args)
    _handle_llx_chat(args)
    _handle_code2llm_analyze(args)
    _handle_redup_scan(args)
    _handle_vallm_validate(args)
    _handle_llx_preprocess(args)
    _handle_llx_context(args)
    _handle_llx_proxy_status(args)
    _handle_llx_proxym_status(args)
    _handle_llx_proxym_chat(args)
    _handle_aider(args)
    _handle_planfile_generate(args)
    _handle_planfile_apply(args)
    _handle_llx_project_anonymize(args)
    _handle_llx_project_deanonymize(args)
    _handle_llx_privacy_scan(args)
  llx/mcp/workflows.py:
    e: run_llx_fix_workflow,run_llx_refactor_workflow,LlxMcpRunResult
    LlxMcpRunResult: to_dict(0)  # Result of an llx MCP fix/refactor workflow.
    run_llx_fix_workflow(workdir;project_path;issues_path;output_path;endpoint_url;model;files;use_docker;docker_args;task)
    run_llx_refactor_workflow(workdir;project_path;issues_path;output_path;endpoint_url;model;files;use_docker;docker_args)
  llx/orchestration/__init__.py:
  llx/orchestration/_utils.py:
    e: load_json,save_json
    load_json(path;label)
    save_json(path;data;label)
  llx/orchestration/cli.py:
    e: _build_parser,_handle_status,_handle_health,_handle_monitor,_delegate_to_subpackage,main
    _build_parser()
    _handle_status()
    _handle_health()
    _handle_monitor(interval;duration)
    _delegate_to_subpackage(component;argv)
    main()
  llx/orchestration/cli_utils.py:
    e: cmd_remove_wrapper,cmd_remove_pair_wrapper,cmd_status_wrapper,cmd_list_wrapper,cmd_cleanup_wrapper
    cmd_remove_wrapper(args;id_attr;id_label;remove_func;save_func)
    cmd_remove_pair_wrapper(args;first_attr;second_attr;first_label;second_label;remove_func;save_func)
    cmd_status_wrapper(args;id_attr;id_label;status_func)
    cmd_list_wrapper(items;title;formatter)
    cmd_cleanup_wrapper(cleanup_func;item_label)
  llx/orchestration/instances/__init__.py:
  llx/orchestration/instances/cli.py:
    e: _build_parser,_dispatch,_cmd_create,_cmd_start,_cmd_stop,_cmd_list,_cmd_metrics,_cmd_health,main
    _build_parser()
    _dispatch(args;mgr)
    _cmd_create(args;mgr)
    _cmd_start(args;mgr)
    _cmd_stop(args;mgr)
    _cmd_list(args;mgr)
    _cmd_metrics(args;mgr)
    _cmd_health(args;mgr)
    main()
  llx/orchestration/instances/manager.py:
    e: InstanceManager
    InstanceManager: __init__(1),load_instances(0),save_instances(0),create_instance(1),start_instance(1),stop_instance(1),remove_instance(1),get_available_instance(3),use_instance(1),get_instance_status(1),list_instances(2),get_instance_metrics(1),health_check_all(0),_health_check_instance(1),_get_uptime_hours(1),_monitor_worker(0),_check_auto_restart(0),print_status_summary(0)  # Manages multiple Docker instances with intelligent allocatio
  llx/orchestration/instances/models.py:
    e: InstanceType,InstanceStatus,InstanceConfig,InstanceState
    InstanceType:  # Types of instances.
    InstanceStatus:  # Instance status.
    InstanceConfig:  # Configuration for an instance.
    InstanceState:  # Current state of an instance.
  llx/orchestration/instances/ports.py:
    e: PortAllocator
    PortAllocator: __init__(0),allocate_port(1),release_port(1),_is_port_available(1),get_status(0)  # Manages port allocation for instances.
  llx/orchestration/llm/__init__.py:
  llx/orchestration/llm/cli.py:
    e: _build_parser,_dispatch,_cmd_add_provider,_cmd_list_providers,_cmd_list_models,_cmd_model_info,_cmd_complete,_cmd_cancel,_cmd_status,_cmd_usage,main
    _build_parser()
    _dispatch(args;orchestrator)
    _cmd_add_provider(args;orch)
    _cmd_list_providers(args;orch)
    _cmd_list_models(args;orch)
    _cmd_model_info(args;orch)
    _cmd_complete(args;orch)
    _cmd_cancel(args;orch)
    _cmd_status(args;orch)
    _cmd_usage(args;orch)
    main()
  llx/orchestration/llm/executors.py:
    e: execute_request,execute_ollama,execute_openai,execute_anthropic,messages_to_prompt,_failed
    execute_request(request;provider;model)
    execute_ollama(request;provider;model)
    execute_openai(request;provider;model)
    execute_anthropic(request;provider;model)
    messages_to_prompt(messages)
    _failed(request;error)
  llx/orchestration/llm/health.py:
    e: perform_health_checks,health_check_worker
    perform_health_checks(providers)
    health_check_worker(orchestrator)
  llx/orchestration/llm/models.py:
    e: LLMProviderType,ModelCapability,LLMModel,LLMProvider,LLMRequest,LLMResponse
    LLMProviderType:  # Types of LLM providers.
    ModelCapability:  # Model capabilities.
    LLMModel:  # LLM model configuration.
    LLMProvider:  # LLM provider configuration.
    LLMRequest:  # LLM request.
    LLMResponse:  # LLM response.
  llx/orchestration/llm/orchestrator.py:
    e: LLMOrchestrator
    LLMOrchestrator: __init__(1),load_config(0),save_config(0),_create_default_config(0),start(0),stop(0),add_provider(1),remove_provider(1),add_model(2),complete_request(1),cancel_request(1),_route_request(1),_execute_request(2),_get_required_capabilities(1),_create_failed_response(2),_add_to_history(1),get_provider_status(1),get_model_info(1),list_models(2),get_usage_stats(0),_get_single_provider_status(1),_get_all_provider_status(0),_start_background_tasks(0),_config_save_worker(0),print_status_summary(0),_print_usage_stats(0),_print_provider_status(0),_print_model_summary(0)  # Orchestrates multiple LLM providers and models with intellig
  llx/orchestration/queue/__init__.py:
  llx/orchestration/queue/cli.py:
    e: _build_parser,_dispatch,_cmd_add,_cmd_enqueue,_cmd_dequeue,_cmd_complete,_cmd_status,_cmd_metrics,main
    _build_parser()
    _dispatch(args;mgr)
    _cmd_add(args;mgr)
    _cmd_enqueue(args;mgr)
    _cmd_dequeue(args;mgr)
    _cmd_complete(args;mgr)
    _cmd_status(args;mgr)
    _cmd_metrics(args;mgr)
    main()
  llx/orchestration/queue/manager.py:
    e: QueueManager
    QueueManager: __init__(1),load_queues(0),save_queues(0),start(0),stop(0),add_queue(1),remove_queue(1),enqueue_request(1),dequeue_request(1),complete_request(3),get_queue_status(1),get_queue_metrics(1),_get_queue_id(2),_get_single_queue_status(1),_get_all_queue_status(0),_worker_loop(2),_process_request(1),_retry_request(2),_calculate_retry_delay(2),_update_averages(2),print_status_summary(0)  # Manages multiple request queues with intelligent prioritizat
  llx/orchestration/queue/models.py:
    e: QueueStatus,RequestPriority,QueueRequest,QueueConfig,QueueState
    QueueStatus:  # Queue status.
    RequestPriority:  # Request priority levels.
    QueueRequest: __lt__(1)  # A request in the queue.
    QueueConfig:  # Configuration for a queue.
    QueueState:  # Current state of a queue.
  llx/orchestration/ratelimit/__init__.py:
  llx/orchestration/ratelimit/_crud.py:
    e: create_default_limits,add_limit,remove_limit
    create_default_limits(self)
    add_limit(self;config)
    remove_limit(self;provider;account)
  llx/orchestration/ratelimit/_persistence.py:
    e: load_limits_from_file,save_limits_to_file
    load_limits_from_file(self)
    save_limits_to_file(self)
  llx/orchestration/ratelimit/cli.py:
    e: _build_parser,_dispatch,_cmd_add,_cmd_remove,_cmd_check,_cmd_record,_cmd_release,_cmd_status,_cmd_available,_cmd_cleanup,main
    _build_parser()
    _dispatch(args;limiter)
    _cmd_add(args;limiter)
    _cmd_remove(args;limiter)
    _cmd_check(args;limiter)
    _cmd_record(args;limiter)
    _cmd_release(args;limiter)
    _cmd_status(args;limiter)
    _cmd_available(args;limiter)
    _cmd_cleanup(args;limiter)
    main()
  llx/orchestration/ratelimit/limiter.py:
    e: RateLimiter
    RateLimiter: __init__(1),load_limits(0),save_limits(0),_create_default_limits(0),add_limit(1),remove_limit(2),check_rate_limit(4),record_request(5),release_request(2),get_status(2),get_available_providers(1),_reset_counters_if_needed(2),_apply_penalty(1),_cleanup_worker(0),_cleanup_expired_penalties(0),_save_state_if_needed(0),print_status_summary(0)  # Manages rate limiting for multiple providers and accounts.
  llx/orchestration/ratelimit/models.py:
    e: LimitType,RateLimitConfig,RateLimitState
    LimitType:  # Types of rate limits.
    RateLimitConfig:  # Configuration for rate limiting.
    RateLimitState:  # Current state of rate limiting.
  llx/orchestration/routing/__init__.py:
  llx/orchestration/routing/cli.py:
    e: _build_parser,_dispatch,_cmd_route,_cmd_status,_cmd_metrics,_cmd_optimize,main
    _build_parser()
    _dispatch(args;engine)
    _cmd_route(args;engine)
    _cmd_status(args;engine)
    _cmd_metrics(args;engine)
    _cmd_optimize(args;engine)
    main()
  llx/orchestration/routing/engine.py:
    e: RoutingEngine
    RoutingEngine: __init__(1),load_config(0),save_config(0),route_request(1),_get_candidates(1),_get_llm_candidates(1),_get_vscode_candidates(1),_get_ai_tools_candidates(1),_filter_candidates(2),_filter_by_rate_limits(2),_apply_routing_strategy(2),_apply_strategy(3),_round_robin_strategy(2),_least_loaded_strategy(2),_priority_based_strategy(2),_cost_optimized_strategy(2),_performance_optimized_strategy(2),_availability_first_strategy(2),_create_decision_from_candidate(5),_validate_decision(1),_create_no_resources_decision(1),_create_routing_failed_decision(1),_create_validation_failed_decision(1),_calculate_llm_score(2),_calculate_vscode_score(2),_calculate_ai_tools_score(2),_get_cost_per_token(2),_get_vscode_cost_per_hour(1),_get_ai_tools_cost_per_hour(1),_get_provider_performance(1),_update_routing_metrics(3),start_background_tasks(0),_metrics_worker(0),_optimization_worker(0),_collect_system_metrics(0),_optimize_routing(0),get_routing_status(0),print_status_summary(0)  # Intelligent routing engine for LLM and VS Code requests.
  llx/orchestration/routing/models.py:
    e: RoutingStrategy,ResourceType,RequestPriority,RoutingRequest,RoutingDecision,RoutingMetrics
    RoutingStrategy:  # Routing strategies.
    ResourceType:  # Types of resources to route to.
    RequestPriority:  # Request priority levels (mirrors queue.models).
    RoutingRequest:  # A request to be routed.
    RoutingDecision:  # A routing decision.
    RoutingMetrics:  # Metrics for routing performance.
  llx/orchestration/session/__init__.py:
  llx/orchestration/session/cli.py:
    e: _build_parser,_dispatch,_cmd_create,_cmd_list,_cmd_queue,_cmd_cleanup,main
    _build_parser()
    _dispatch(args;mgr)
    _cmd_create(args;mgr)
    _cmd_list(args;mgr)
    _cmd_queue(args;mgr)
    _cmd_cleanup(args;mgr)
    main()
  llx/orchestration/session/manager.py:
    e: SessionManager
    SessionManager: __init__(1),load_sessions(0),save_sessions(0),create_session(1),remove_session(1),get_available_session(4),request_session(2),release_session(3),get_session_status(1),list_sessions(2),get_queue_status(0),_is_rate_limited(2),_should_rate_limit(1),_get_utilization(1),_get_time_until_available(1),_get_next_available_time(0),_cleanup_worker(0),_cleanup_expired_limits(0),_update_session_stats(0),print_status_summary(0)  # Manages multiple sessions with intelligent scheduling and ra
  llx/orchestration/session/models.py:
    e: SessionType,SessionStatus,SessionConfig,SessionState
    SessionType:  # Types of sessions.
    SessionStatus:  # Session status.
    SessionConfig:  # Configuration for a session.
    SessionState:  # Current state of a session.
  llx/orchestration/utils/_cmd_cleanup.py:
    e: create_cleanup_handler
    create_cleanup_handler(save_func)
  llx/orchestration/utils/_cmd_remove.py:
    e: create_remove_handler
    create_remove_handler(id_attr;id_label;remove_func;save_func)
  llx/orchestration/utils/_cmd_status.py:
    e: create_status_handler
    create_status_handler(id_attr;entity_label;get_status_func;print_summary_func)
  llx/orchestration/vscode/__init__.py:
  llx/orchestration/vscode/cli.py:
    e: _build_parser,_dispatch,_cmd_add_account,_cmd_list_accounts,_cmd_create,_cmd_start,_cmd_stop,_cmd_list,_cmd_sessions,main
    _build_parser()
    _dispatch(args;orch)
    _cmd_add_account(args;orch)
    _cmd_list_accounts(args;orch)
    _cmd_create(args;orch)
    _cmd_start(args;orch)
    _cmd_stop(args;orch)
    _cmd_list(args;orch)
    _cmd_sessions(args;orch)
    main()
  llx/orchestration/vscode/config_io.py:
    e: load_vscode_config,save_vscode_config
    load_vscode_config(orchestrator)
    save_vscode_config(orchestrator)
  llx/orchestration/vscode/defaults.py:
    e: create_default_vscode_config
    create_default_vscode_config(orchestrator)
  llx/orchestration/vscode/models.py:
    e: VSCodeAccountType,VSCodeAccount,VSCodeInstanceConfig,VSCodeSession
    VSCodeAccountType:  # Types of VS Code accounts.
    VSCodeAccount:  # VS Code account configuration.
    VSCodeInstanceConfig:  # Configuration for a VS Code instance.
    VSCodeSession:  # Active VS Code session.
  llx/orchestration/vscode/orchestrator.py:
    e: VSCodeOrchestrator
    VSCodeOrchestrator: __init__(1),load_config(0),save_config(0),_create_default_config(0),start(0),stop(0),add_account(1),remove_account(1),create_instance(1),remove_instance(1),start_instance(1),end_session(1),get_available_instance(2),get_session_status(1),list_accounts(0),list_instances(1),list_sessions(1),_wait_for_instance_ready(2),_configure_vscode_instance(2),_start_browser_for_instance(1),_close_browser_session(1),_auto_start_instances(0),_stop_all_instances(0),_start_background_tasks(0),_session_cleanup_worker(0),_config_save_worker(0),print_status_summary(0)  # Orchestrates multiple VS Code instances with intelligent man
  llx/orchestration/vscode/ports.py:
    e: VSCodePortAllocator
    VSCodePortAllocator: __init__(0),allocate_port(1),release_port(1),_is_port_available(1)  # Manages port allocation for VS Code instances.
  llx/planfile/__init__.py:
  llx/planfile/builder.py:
    e: create_strategy_command,LLXStrategyBuilder
    LLXStrategyBuilder: __init__(3),_call_llx(1),ask_llm_questions(0),_parse_bullet_list(1),answers_to_strategy(1),build_strategy(1)  # Interactive strategy builder using LLX.
    create_strategy_command(output;model;local)
  llx/planfile/builder_simple.py:
    e: create_strategy_command,SimpleStrategyBuilder
    SimpleStrategyBuilder: __init__(2),build_from_analysis(3),_generate_strategy_content(3),_get_sprint_objectives(3),_get_tasks_for_focus(2)  # Simplified strategy builder using LLX client directly.
    create_strategy_command(project_path;focus;sprints;output)
  llx/planfile/config.py:
    e: PlanfileConfig
    PlanfileConfig: __init__(1),load_config(1),_merge_config(2),get(2),save_default_config(1)  # Configuration for planfile generation and execution.
  llx/planfile/examples.py:
    e: example_create_strategy,example_validate_strategy,example_run_strategy,example_verify_strategy,example_programmatic_strategy
    example_create_strategy()
    example_validate_strategy()
    example_run_strategy()
    example_verify_strategy()
    example_programmatic_strategy()
  llx/planfile/executor_simple.py:
    e: execute_strategy,_load_strategy,_normalize_strategy,_get_sprint_tasks,_execute_task,_select_model,_build_task_prompt,TaskResult
    TaskResult:  # Result of executing a task.
    execute_strategy(strategy_path;project_path)
    _load_strategy(path)
    _normalize_strategy(strategy)
    _get_sprint_tasks(sprint)
    _execute_task(task;project_path;config;metrics;dry_run;model_override)
    _select_model(task;config;metrics)
    _build_task_prompt(task;metrics)
  llx/planfile/generate_strategy.py:
    e: _normalize_strategy_data,_normalize_sprints,_normalize_single_sprint,_extract_sprint_id,_generate_tasks_from_patterns,_normalize_quality_gates,_normalize_single_gate,_normalize_goal,_normalize_metadata,generate_strategy_with_fix,_print_generation_info,_build_strategy_prompt,_call_llm_for_strategy,_parse_and_fix_yaml,_fix_yaml_formatting,_fix_list_formatting,_fix_indentation,save_fixed_strategy,main
    _normalize_strategy_data(data)
    _normalize_sprints(data)
    _normalize_single_sprint(sprint;index;task_patterns)
    _extract_sprint_id(sprint_id;index)
    _generate_tasks_from_patterns(task_patterns)
    _normalize_quality_gates(data)
    _normalize_single_gate(gate;index)
    _normalize_goal(data)
    _normalize_metadata(data)
    generate_strategy_with_fix(project_path;model;sprints;focus;description;project_type;framework)
    _print_generation_info(project_path;model;sprints;focus;description)
    _build_strategy_prompt(metrics;sprints;focus;description;project_type;framework)
    _call_llm_for_strategy(prompt;model)
    _parse_and_fix_yaml(content)
    _fix_yaml_formatting(yaml_text)
    _fix_list_formatting(yaml_text)
    _fix_indentation(yaml_text)
    save_fixed_strategy(data;output_path)
    main()
  llx/planfile/model_selector.py:
    e: ModelProvider,ModelTier,ModelFilter,ModelSelector
    ModelProvider:  # Available model providers.
    ModelTier:  # Model pricing tiers.
    ModelFilter: matches(2),_matches_provider(1),_matches_tier(1),_matches_api_key_requirement(1),_matches_scope(1),_has_api_key(1)  # Filter criteria for model selection.
    ModelSelector: __init__(1),_build_model_registry(0),_get_provider(1),select_model(1),list_models(1),_check_api_key(1)  # Select models based on filters and preferences.
  llx/planfile/models.py:
    e: TaskType,ModelTier,ModelHints,TaskPattern,Sprint,Goal,QualityGate,Strategy
    TaskType:  # Type of task in the strategy.
    ModelTier:  # Model tier for different phases of work.
    ModelHints:  # AI model hints for different phases of task execution.
    TaskPattern:  # A pattern for generating tasks.
    Sprint:  # A sprint in the strategy.
    Goal:  # Project goal definition.
    QualityGate:  # Quality gate definition.
    Strategy: validate_sprint_ids(2),get_task_patterns(1),get_sprint(1),model_validate_yaml(2),model_dump_yaml(0)  # Main strategy configuration.
  llx/planfile/runner.py:
    e: load_valid_strategy,verify_strategy_post_execution,analyze_project_metrics,apply_strategy_to_tickets,run_strategy
    load_valid_strategy(path)
    verify_strategy_post_execution(strategy;project_path;backend)
    analyze_project_metrics(project_path)
    apply_strategy_to_tickets(strategy;project_path;backend;dry_run)
    run_strategy(strategy_path;project_path;backend;dry_run)
  llx/prellm/__init__.py:
    e: _get_process_chain
    _get_process_chain()
  llx/prellm/_nfo_compat.py:
    e: configure,log_call,_FallbackLogger,_FallbackTerminalSink,_FallbackMarkdownSink
    _FallbackLogger: __init__(2),debug(1),info(1),warning(1),error(1),critical(1),exception(1)  # Fallback logger using stdlib logging.
    _FallbackTerminalSink: __init__(6)  # Fallback terminal sink using stdlib logging.
    _FallbackMarkdownSink: __init__(1)  # Fallback markdown sink that writes to a file.
    configure(name;level;sinks;bridge_stdlib;propagate_stdlib;env_prefix;version;force)
    log_call(func)
  llx/prellm/agents/__init__.py:
  llx/prellm/agents/executor.py:
    e: ExecutorResult,ExecutorAgent
    ExecutorResult:  # Output of the ExecutorAgent.
    ExecutorAgent: __init__(4),execute(2),_validate_response(1)  # Agent execution — large LLM (>24B) executes structured tasks
  llx/prellm/agents/preprocessor.py:
    e: _get_user_memory_class,_get_codebase_indexer_class,PreprocessResult,PreprocessorAgent
    PreprocessResult:  # Output of the PreprocessorAgent — structured input for the E
    PreprocessorAgent: __init__(7),preprocess(3),_extract_executor_input(2),_extract_confidence(1)  # Agent preprocessing — small LLM (≤24B) analyzes and structur
    _get_user_memory_class()
    _get_codebase_indexer_class()
  llx/prellm/analyzers/__init__.py:
  llx/prellm/analyzers/context_engine.py:
    e: ContextEngine
    ContextEngine: __init__(1),gather(0),enrich_prompt(2),gather_runtime(0),_auto_collect_env(0),_gather_process(0),_gather_locale(0),_gather_network(0),_gather_env(1),_gather_git(1),_gather_git_gitpython(1),_gather_git_subprocess(1),_gather_system(1)  # Collects context from environment, git, and system for promp
  llx/prellm/budget.py:
    e: _current_month_key,get_budget_tracker,reset_budget_tracker,BudgetExceededError,UsageEntry,BudgetTracker
    BudgetExceededError: __init__(3)  # Raised when the monthly budget limit has been reached.
    UsageEntry:  # Single API call cost record.
    BudgetTracker: _ensure_loaded(0),check(1),record(4),record_from_response(2),total_cost(0),remaining(0),entries(0),summary(0),_persist(0),reset(0)  # Tracks LLM API spend against a monthly budget.
    _current_month_key()
    get_budget_tracker(monthly_limit;persist_path)
    reset_budget_tracker()
  llx/prellm/chains/__init__.py:
  llx/prellm/chains/process_chain.py:
    e: ProcessChain
    ProcessChain: __init__(5),execute(3),_execute_step(4),_check_dependencies(1),_handle_approval(4),_run_dry_run(4),_run_engine(4),get_audit_log(0),_audit_step(3),_load_process_config(1)  # Execute multi-step DevOps workflows with preLLM validation a
  llx/prellm/cli.py:
    e: query,context,process,decompose,init,serve,doctor,budget,models,session_list_cmd,session_export_cmd,session_import_cmd,session_clear_cmd
    query(prompt;small;large;strategy;context;config;memory;codebase;collect_env;compress_folder;no_sanitize;show_schema;show_blocked;json_output;trace;trace_dir;env_file)
    context(json_output;schema;blocked;folder)
    process(config;guard_config;dry_run;json_output;env)
    decompose(query;config;strategy;json_output)
    init(output;devops)
    serve(host;port;small;large;strategy;config;env_file;reload)
    doctor(env_file;live)
    budget(reset;json_output)
    models(provider;search)
    session_list_cmd(memory)
    session_export_cmd(output;memory;session_id)
    session_import_cmd(input_file;memory)
    session_clear_cmd(memory;force)
  llx/prellm/cli_commands.py:
    e: process,decompose,init,serve,_doctor_check_config,_doctor_check_providers,_doctor_check_files,doctor,budget,models
    process(config;guard_config;dry_run;json_output;env)
    decompose(query;config;strategy;json_output)
    init(output;devops)
    serve(host;port;small;large;strategy;config;env_file;reload)
    _doctor_check_config(env)
    _doctor_check_providers(env;live)
    _doctor_check_files(env_file)
    doctor(env_file;live)
    budget(reset;json_output)
    models(provider;search)
  llx/prellm/cli_config.py:
    e: config_set_cmd,config_get_cmd,_format_config_sections,config_list_cmd,config_show_cmd,config_init_env
    config_set_cmd(key;value;global_)
    config_get_cmd(key;raw)
    _format_config_sections(entries)
    config_list_cmd(raw)
    config_show_cmd()
    config_init_env(global_;force)
  llx/prellm/cli_context.py:
    e: context,context_show_cmd
    context(json_output;schema;blocked;folder)
    context_show_cmd(json_output;schema;blocked;folder)
  llx/prellm/cli_query.py:
    e: _init_logging,_handle_query_options,_show_debug_info,_initialize_execution,_execute_and_format_result
    _init_logging()
    _handle_query_options(prompt;small;large;strategy;context;config;memory;codebase;collect_env;compress_folder;no_sanitize;show_schema;show_blocked;json_output;trace;trace_dir;env_file)
    _show_debug_info(options)
    _initialize_execution(options)
    _execute_and_format_result(options;recorder)
  llx/prellm/context/__init__.py:
  llx/prellm/context/codebase_indexer.py:
    e: CodeSymbol,FileIndex,CodebaseIndex,CodebaseIndexer
    CodeSymbol:  # A code symbol extracted from source.
    FileIndex:  # Index of a single source file.
    CodebaseIndex:  # Full codebase index.
    CodebaseIndexer: __init__(1),_check_tree_sitter(0),index_directory(3),_index_file(2),_extract_with_tree_sitter(3),_get_parser(1),_walk_tree(4),_get_line(2),_extract_with_regex(3),_extract_imports(2),search(3),get_context_for_query(3),get_compressed_context(3),estimate_tokens(1)  # Index a codebase using tree-sitter for AST-based symbol extr
  llx/prellm/context/folder_compressor.py:
    e: _relative_path,_path_to_module,_extract_module_from_import,_extract_module_docstring,FolderCompressor
    FolderCompressor: __init__(1),compress(3),to_toon(1),to_dependency_graph(1),to_summary(1),estimate_token_count(1)  # Compresses a project folder into a lightweight representatio
    _relative_path(path;root)
    _path_to_module(rel_path)
    _extract_module_from_import(import_line;project_name)
    _extract_module_docstring(path)
  llx/prellm/context/schema_generator.py:
    e: ContextSchemaGenerator
    ContextSchemaGenerator: generate(5),to_prompt_section(1),estimate_relevance(2),_detect_execution_env(1),_detect_tools(0),_detect_project_type(1),_build_project_summary(1),_summarize_history(1),_estimate_token_cost(1)  # Generates a structured context schema from available context
  llx/prellm/context/sensitive_filter.py:
    e: SensitiveDataFilter
    SensitiveDataFilter: __init__(3),_load_rules(1),classify_key(1),classify_value(1),filter_dict(2),filter_context_for_large_llm(1),sanitize_text(1),get_filter_report(0),_filter_dict_item(2),_filter_env_var_item(3),_filter_non_env_var_item(2),_filter_recursive(1),_looks_like_env_var(1),_mask_value(1)  # Classifies and filters sensitive data from context before LL
  llx/prellm/context/shell_collector.py:
    e: ShellContextCollector
    ShellContextCollector: __init__(1),collect_env_vars(1),collect_process_info(0),collect_locale_info(0),collect_shell_info(0),collect_network_context(0),collect_all(1),_is_safe_key(1)  # Collects full shell environment context for LLM prompt enric
  llx/prellm/context/user_memory.py:
    e: UserMemory
    UserMemory: __init__(2),_init_sqlite(0),_init_chromadb(0),add_interaction(3),get_recent_context(2),get_user_preferences(0),set_preference(2),clear(0),export_session(1),import_session(1),get_relevant_context(2),auto_inject_context(2),learn_preference_from_interaction(2),_get_all_interactions(1),close(0)  # Stores user query history and learned preferences.
  llx/prellm/context_ops.py:
    e: collect_user_context,collect_environment_context,compress_codebase_folder,generate_context_schema,build_sensitive_filter,initialize_context_components,prepare_context,build_pipeline_context
    collect_user_context(user_context)
    collect_environment_context(collect_env)
    compress_codebase_folder(compress_folder;codebase_path)
    generate_context_schema(collect_env;compress_folder;shell_ctx;compressed)
    build_sensitive_filter(sanitize;sensitive_rules;extra_context)
    initialize_context_components(memory_path;codebase_path)
    prepare_context(user_context;domain_rules;collect_env;compress_folder;codebase_path;sanitize;sensitive_rules;memory_path)
    build_pipeline_context(extra_context)
  llx/prellm/core.py:
    e: _resolve_pipeline_name,_apply_config_overrides,_trace_preprocess_configuration,preprocess_and_execute,preprocess_and_execute_sync,PreLLM
    PreLLM: __init__(2),__call__(3),decompose_only(3),get_audit_log(0),_audit(3),_load_config(1)  # preLLM v0.2/v0.3 — small LLM decomposition before large LLM 
    _resolve_pipeline_name(strategy;pipeline)
    _apply_config_overrides(small_llm;large_llm;domain_rules;config_path;kwargs)
    _trace_preprocess_configuration(trace;small_llm;large_llm;pipeline_name;config_path;user_context)
    preprocess_and_execute(query;small_llm;large_llm;strategy;user_context;config_path;domain_rules;pipeline;prompts_path;pipelines_path;schemas_path;memory_path;codebase_path;collect_env;collect_runtime;session_path;compress_folder;sanitize;sensitive_rules)
    preprocess_and_execute_sync(query;small_llm;large_llm;strategy;user_context;config_path;domain_rules;pipeline;prompts_path;pipelines_path;schemas_path)
  llx/prellm/env_config.py:
    e: _load_dotenv,get_env_config
    _load_dotenv(env_path)
    get_env_config(env_path;small_model;large_model)
  llx/prellm/extractors.py:
    e: extract_classification_from_state,extract_structure_from_state,extract_sub_queries_from_state,extract_missing_fields_from_state,extract_matched_rule_from_state,build_decomposition_result,format_classification_context,format_context_schema,format_runtime_context,format_user_context,build_executor_system_prompt
    extract_classification_from_state(state)
    extract_structure_from_state(state)
    extract_sub_queries_from_state(state)
    extract_missing_fields_from_state(state)
    extract_matched_rule_from_state(state;current_missing_fields)
    build_decomposition_result(query;pipeline_name;prep_result)
    format_classification_context(prep_result)
    format_context_schema(extra_context)
    format_runtime_context(extra_context)
    format_user_context(extra_context)
    build_executor_system_prompt(prep_result;extra_context)
  llx/prellm/llm_provider.py:
    e: LLMProvider
    LLMProvider: __init__(1),complete(2),complete_json(2),__repr__(0)  # LiteLLM wrapper with retry and fallback support.
  llx/prellm/logging_setup.py:
    e: setup_logging,get_logger,_get_version
    setup_logging(level;markdown_file;terminal_format)
    get_logger(name)
    _get_version()
  llx/prellm/model_catalog.py:
    e: list_model_pairs,list_openrouter_models
    list_model_pairs(provider;search)
    list_openrouter_models(provider;search)
  llx/prellm/models.py:
    e: SensitivityLevel,ProcessInfo,LocaleInfo,ShellInfo,NetworkContext,ShellContext,ContextSchema,FilterReport,CompressedFolder,RuntimeContext,SessionSnapshot,Policy,ApprovalMode,StepStatus,DecompositionStrategy,BiasPattern,ModelConfig,GuardConfig,AnalysisResult,GuardResponse,DomainRule,LLMProviderConfig,DecompositionPrompts,PreLLMConfig,ClassificationResult,StructureResult,DecompositionResult,PreLLMResponse,ProcessStep,ProcessConfig,StepResult,ProcessResult,AuditEntry
    SensitivityLevel:
    ProcessInfo:
    LocaleInfo:
    ShellInfo:
    NetworkContext:
    ShellContext:
    ContextSchema:
    FilterReport:
    CompressedFolder:
    RuntimeContext:  # Full runtime snapshot — env, process, locale, network, git, 
    SessionSnapshot: to_file(1),from_file(2)  # Exportable session snapshot — enables persistent context acr
    Policy:
    ApprovalMode:
    StepStatus:
    DecompositionStrategy:  # Strategy for how the small LLM preprocesses a query.
    BiasPattern:
    ModelConfig:
    GuardConfig:  # Top-level YAML config model (v0.1 compat).
    AnalysisResult:  # Result of query analysis (v0.1 compat).
    GuardResponse:  # Response from Prellm (v0.1 compat).
    DomainRule:  # Configurable domain rule — keywords, intent, required fields
    LLMProviderConfig:  # Configuration for a single LLM provider (small or large).
    DecompositionPrompts:  # System prompts for each decomposition step — all configurabl
    PreLLMConfig:  # Top-level config for preLLM v0.2 — fully YAML-driven.
    ClassificationResult:  # Output of the CLASSIFY step.
    StructureResult:  # Output of the STRUCTURE step.
    DecompositionResult:  # Full result of the small LLM decomposition pipeline.
    PreLLMResponse:  # Response from preLLM v0.2 — includes decomposition + large L
    ProcessStep:
    ProcessConfig:
    StepResult:  # Result of a single process chain step.
    ProcessResult:  # Result of a full process chain execution.
    AuditEntry:  # Single audit log entry for traceability.
  llx/prellm/pipeline/__init__.py:
  llx/prellm/pipeline/algo_handlers.py:
    e: AlgoHandlersMixin
    AlgoHandlersMixin: _build_algo_handlers(1),_execute_algo_step(2),_resolve_step_input(2),_algo_domain_rule_matcher(3),_algo_field_validator(3),_algo_yaml_formatter(3),_algo_runtime_collector(3),_algo_sensitive_filter(3),_algo_session_injector(3),_algo_shell_context_collector(3),_algo_folder_compressor(3),_algo_context_schema_generator(3)
  llx/prellm/pipeline/config.py:
    e: PipelineStep,PipelineConfig,StepExecutionResult,PipelineResult
    PipelineStep:  # Configuration for a single pipeline step.
    PipelineConfig:  # Configuration for a complete pipeline.
    StepExecutionResult:  # Result of executing a single pipeline step.
    PipelineResult:  # Result of executing a full pipeline.
  llx/prellm/pipeline/engine.py:
    e: PromptPipeline
    PromptPipeline: __init__(4),from_yaml(6),execute(2),_evaluate_condition(2),_execute_llm_step(2)  # Generic pipeline — executes a sequence of LLM + algorithmic 
  llx/prellm/pipeline/loader.py:
    e: load_pipeline_config,build_pipeline
    load_pipeline_config(pipelines_path;pipeline_name)
    build_pipeline(config;registry;small_llm;validators;pipeline_cls)
  llx/prellm/pipeline.py:
    e: PipelineStep,PipelineConfig,StepExecutionResult,PipelineResult,PromptPipeline
    PipelineStep:  # Configuration for a single pipeline step.
    PipelineConfig:  # Configuration for a complete pipeline.
    StepExecutionResult:  # Result of executing a single pipeline step.
    PipelineResult:  # Result of executing a full pipeline.
    PromptPipeline: __init__(4),from_yaml(6),execute(2),_execute_llm_step(2),_execute_algo_step(2),_gather_inputs(2),_build_user_message(2),_evaluate_condition(2),register_algo_handler(2),_algo_domain_rule_matcher(3),_algo_field_validator(3),_algo_yaml_formatter(3),_algo_runtime_collector(3),_algo_sensitive_filter(3),_algo_session_injector(3),_algo_shell_context_collector(3),_algo_folder_compressor(3),_algo_context_schema_generator(3)  # Generic pipeline — executes a sequence of LLM + algorithmic 
  llx/prellm/pipeline_ops.py:
    e: execute_v3_pipeline,run_preprocessing,run_execution,persist_session,record_trace
    execute_v3_pipeline(query;small_llm;large_llm;pipeline;user_context;domain_rules;prompts_path;pipelines_path;schemas_path;memory_path;codebase_path;collect_env;compress_folder;sanitize;sensitive_rules)
    run_preprocessing(preprocessor;query;extra_context;pipeline)
    run_execution(executor;executor_input;system_prompt)
    persist_session(user_memory;query;exec_result)
    record_trace(trace;pipeline;small_llm;large_llm;query;extra_context;prep_result;exec_result;prep_duration_ms;exec_duration_ms)
  llx/prellm/prompt_registry.py:
    e: PromptNotFoundError,PromptRenderError,PromptEntry,PromptRegistry,_StrictUndefined
    PromptNotFoundError:  # Raised when a prompt name is not found in the registry.
    PromptRenderError:  # Raised when a prompt template fails to render.
    PromptEntry: __init__(4),__repr__(0)  # Single prompt entry with template, max_tokens, and temperatu
    PromptRegistry: __init__(1),_ensure_loaded(0),_load(0),get(1),get_entry(1),list_prompts(0),validate(0),register(4),_render(2)  # Loads prompts from YAML, caches, validates placeholders.
    _StrictUndefined:  # Custom undefined that allows `default` filter but raises on 
  llx/prellm/query_decomposer.py:
    e: QueryDecomposer
    QueryDecomposer: __init__(3),decompose(4),_classify(1),_structure(1),_split(1),_enrich(3),_compose(3),_match_domain_rule(2),_auto_select_strategy(2),_find_missing_fields(3)  # Decomposes user queries using a small LLM before routing to 
  llx/prellm/server.py:
    e: _parse_model_pair,_build_prellm_meta,health,list_models,chat_completions,_stream_response,batch_process,create_app,ChatMessage,PreLLMExtras,ChatCompletionRequest,ChatCompletionChoice,UsageInfo,PreLLMMeta,ChatCompletionResponse,BatchItem,HealthResponse,AuthMiddleware
    ChatMessage:
    PreLLMExtras:  # preLLM-specific extensions in the request body.
    ChatCompletionRequest:
    ChatCompletionChoice:
    UsageInfo:
    PreLLMMeta:  # preLLM metadata in the response.
    ChatCompletionResponse:
    BatchItem:
    HealthResponse:
    AuthMiddleware: dispatch(2)  # Bearer token auth using LITELLM_MASTER_KEY. Skips auth if ke
    _parse_model_pair(model_str)
    _build_prellm_meta(result;strategy)
    health()
    list_models()
    chat_completions(req)
    _stream_response(query;small;large;strategy;extras)
    batch_process(items)
    create_app(small_model;large_model;strategy;config_path;master_key;dotenv_path)
  llx/prellm/trace.py:
    e: get_current_trace,set_current_trace,_step_icon,_safe_json,_sanitize,_compact_value,_format_tree_value,_extract_prompt_text,_wrap_text,TraceStep,TraceRecorder
    TraceStep:  # A single recorded step in the execution trace.
    TraceRecorder: start(1),stop(0),step(9),set_result(0),total_duration_ms(0),_generate_markdown_header(0),_generate_markdown_config(0),_generate_markdown_step_details(2),_generate_markdown_decision_path(0),_generate_markdown_result(0),_generate_markdown_summary(0),to_markdown(0),_collect_trace_data(0),_generate_header(1),_generate_decision_tree(1),_generate_response_section(1),_generate_timing_breakdown(1),_generate_step_log(1),_generate_footer(1),to_stdout(0),save(1)  # Records execution trace and generates markdown documentation
    get_current_trace()
    set_current_trace(trace)
    _step_icon(status)
    _safe_json(obj;max_len)
    _sanitize(obj;depth)
    _compact_value(val;max_len)
    _format_tree_value(val)
    _extract_prompt_text(composed)
    _wrap_text(text;width)
  llx/prellm/utils/__init__.py:
  llx/prellm/utils/lazy_imports.py:
    e: lazy_import_global
    lazy_import_global(name;import_path;globals_dict)
  llx/prellm/utils/lazy_loader.py:
    e: LazyLoader
    LazyLoader: __init__(0),_ensure_loaded(0),_load(0)  # Base class for components that need lazy loading of resource
  llx/prellm/validators.py:
    e: ValidationResult,SchemaDefinition,ResponseValidator
    ValidationResult:  # Result of validating data against a schema.
    SchemaDefinition:  # Parsed schema definition from YAML.
    ResponseValidator: __init__(1),_load(0),list_schemas(0),validate(2),validate_or_retry(4),_check_type(3),_check_constraints(3)  # Validates LLM responses against YAML-defined schemas.
  llx/privacy/__core.py:
    e: quick_anonymize,quick_deanonymize,AnonymizationPattern,AnonymizationResult,Anonymizer
    AnonymizationPattern:  # Definition of a sensitive data pattern.
    AnonymizationResult: deanonymize(1)  # Result of anonymization operation with mapping for deanonymi
    Anonymizer: __init__(3),_default_patterns(0),_compile_patterns(0),anonymize(2),_generate_token(4),deanonymize(2),scan(1),add_pattern(5),disable_pattern(1),enable_pattern(1)  # Reversible anonymization engine for sensitive data.
    quick_anonymize(text;salt)
    quick_deanonymize(text;mapping)
  llx/privacy/__init__.py:
  llx/privacy/_project_anonymizer.py:
    e: ProjectAnonymizationResult,ProjectAnonymizer
    ProjectAnonymizationResult:
    ProjectAnonymizer: __init__(2),anonymize_project(3),anonymize_file(1),_anonymize_python(2),_anonymize_source_code(2),_anonymize_config(2),_anonymize_generic(2),anonymize_string(2)
  llx/privacy/_project_ast.py:
    e: ASTAnonymizer
    ASTAnonymizer: __init__(2),visit_FunctionDef(1),visit_ClassDef(1),visit_Name(1),visit_Assign(1),visit_Attribute(1),visit_ImportFrom(1),visit_Import(1),visit_Constant(1),_is_builtin(1)  # AST transformer that anonymizes code symbols while preservin
  llx/privacy/_project_context.py:
    e: _default_salt,_mapping_dict_for,_symbol_prefix,_mappings_to_dict,_dict_to_mappings,SymbolMapping,AnonymizationContext
    SymbolMapping:  # Mapping between original and anonymized symbols.
    AnonymizationContext: __post_init__(0),get_or_create_symbol(5),_get_mapping_dict(1),_generate_symbol(3),to_dict(0),from_dict(2),save(1),load(2)  # Context for project-wide anonymization with persistent mappi
    _default_salt()
    _mapping_dict_for(context;symbol_type)
    _symbol_prefix(symbol_type)
    _mappings_to_dict(mappings)
    _dict_to_mappings(data)
  llx/privacy/_streaming_chunking.py:
    e: ProgressInfo,ProgressCallback,ChunkResult,ChunkedProcessor
    ProgressInfo: percent(0),bytes_percent(0)  # Progress information for streaming operations.
    ProgressCallback: __call__(1)  # Protocol for progress callbacks.
    ChunkResult:  # Result of processing a single chunk.
    ChunkedProcessor: __init__(1),process_file(2),_process_small_file(2),_split_and_process(2)  # Process large files in chunks to manage memory usage.
  llx/privacy/_streaming_impl.py:
    e: anonymize_project_with_progress,deanonymize_response_streaming,StreamingProjectAnonymizer,StreamingProjectDeanonymizer
    StreamingProjectAnonymizer: __init__(2),anonymize_streaming(4),_collect_files(2),_is_excluded(2),_build_progress(3),_iter_batches(2),_process_batch(3),_process_file(3),_anonymize_large_file(1),save_context(1)  # Stream-process large projects with progress tracking.
    StreamingProjectDeanonymizer: __init__(1),deanonymize_streaming(2),deanonymize_files_streaming(2)  # Stream-process large deanonymization operations.
    anonymize_project_with_progress(project_path;output_dir;include;exclude;on_progress)
    deanonymize_response_streaming(llm_response_stream;context_path;on_chunk)
  llx/privacy/_streaming_parallel.py:
    e: ParallelProjectProcessor
    ParallelProjectProcessor: __init__(2),anonymize_parallel(2)  # Process multiple files in parallel for speed.
  llx/privacy/deanonymize.py:
    e: quick_project_deanonymize,DeanonymizationResult,ProjectDeanonymizationResult,ProjectDeanonymizer,StreamingDeanonymizer
    DeanonymizationResult:  # Result of deanonymization operation.
    ProjectDeanonymizationResult:  # Result of project-level deanonymization.
    ProjectDeanonymizer: __init__(1),_build_reverse_lookup(0),deanonymize_text(2),deanonymize_file(2),_restore_imports(1),_restore_decorators(1),deanonymize_project_files(2),deanonymize_chat_response(1),get_symbol_info(1),list_all_mappings(0)  # Restores original values from anonymized project content.
    StreamingDeanonymizer: __init__(1),feed_chunk(1),_find_punctuation_boundary(0),finalize(0),get_stats(0)  # Deanonymizer for streaming/chunked LLM responses.
    quick_project_deanonymize(text;context_path)
  llx/privacy/deanonymize_engine.py:
    e: ProjectDeanonymizer
    ProjectDeanonymizer: __init__(1),deanonymize_text(2),deanonymize_file(2),deanonymize_project_files(2)  # Restores original values from anonymized project content.
  llx/privacy/deanonymize_results.py:
    e: DeanonymizationResult,ProjectDeanonymizationResult
    DeanonymizationResult:  # Result of deanonymization operation.
    ProjectDeanonymizationResult:  # Result of project-level deanonymization.
  llx/privacy/deanonymize_utils.py:
    e: build_reverse_lookup,find_symbol_tokens,find_content_tokens,get_content_mapping,restore_imports,restore_decorators
    build_reverse_lookup(context)
    find_symbol_tokens(text)
    find_content_tokens(text)
    get_content_mapping(context)
    restore_imports(content;reverse_lookup)
    restore_decorators(content;reverse_lookup)
  llx/privacy/project.py:
  llx/privacy/streaming.py:
  llx/pyqual_plugins/__init__.py:
  llx/pyqual_plugins/bump_version.py:
    e: check_version_on_pypi,parse_version,bump_patch_version,update_version_file,update_pyproject_toml,git_commit_version_bump,main
    check_version_on_pypi(version)
    parse_version(version)
    bump_patch_version(version)
    update_version_file(version_path;new_version)
    update_pyproject_toml(toml_path;old_version;new_version)
    git_commit_version_bump(old_version;new_version)
    main()
  llx/pyqual_plugins/detect_secrets.py:
    e: _run_detect_secrets_subprocess,run_detect_secrets,main
    _run_detect_secrets_subprocess(output_file)
    run_detect_secrets(output_dir)
    main()
  llx/pyqual_plugins/lint.py:
    e: run_ruff_lint,run_ruff_format_check,main
    run_ruff_lint(output_dir)
    run_ruff_format_check()
    main()
  llx/pyqual_plugins/publish.py:
    e: get_current_version,check_version_on_pypi,upload_to_pypi,main
    get_current_version()
    check_version_on_pypi(version)
    upload_to_pypi()
    main()
  llx/pyqual_plugins/security_audit.py:
    e: run_pip_audit,run_bandit,main
    run_pip_audit(output_dir)
    run_bandit(output_dir)
    main()
  llx/pyqual_plugins/type_check.py:
    e: run_mypy,main
    run_mypy(output_dir)
    main()
  llx/pyqual_plugins/verify_push_publish.py:
    e: get_current_version,verify_push,verify_publish,main
    get_current_version()
    verify_push()
    verify_publish(version;max_retries;delay)
    main()
  llx/routing/__init__.py:
  llx/routing/client.py:
    e: ChatMessage,ChatResponse,LlxClient
    ChatMessage:  # A single chat message.
    ChatResponse: prompt_tokens(0),completion_tokens(0),total_tokens(0),deanonymize(0)  # Response from LLM completion.
    LlxClient: __init__(1),chat(2),chat_with_context(3),_build_payload(5),_parse_response(3),_fallback_direct(3),_metrics_headers(1),close(0),__enter__(0),__exit__(0)  # LLM client that routes through LiteLLM proxy or calls direct
  llx/routing/selector.py:
    e: select_model,_count_premium_signals,_count_balanced_signals,_apply_task_adjustment,_compute_tier,_compute_alternative,check_context_fit,select_with_context_check,ModelTier,SelectionResult
    ModelTier:  # LLM model tiers ranked by capability and cost.
    SelectionResult: model_id(0),explain(0)  # Result of model selection with explanation.
    select_model(metrics;config)
    _count_premium_signals(m;t;reasons)
    _count_balanced_signals(m;t;reasons)
    _apply_task_adjustment(signals;task_hint;reasons)
    _compute_tier(m;t;reasons;task_hint)
    _compute_alternative(tier;order)
    check_context_fit(metrics;model)
    select_with_context_check(metrics;config)
  llx/tools/__init__.py:
  llx/tools/_docker.py:
    e: is_container_running,docker_exec,docker_cp
    is_container_running(container_name)
    docker_exec(container;cmd;timeout;interactive)
    docker_cp(src;dest;timeout)
  llx/tools/_utils.py:
  llx/tools/ai_tools_manager.py:
    e: AIToolsManager
    AIToolsManager: __init__(1),is_container_running(0),_ensure_llx_api_running(1),_start_ai_tools_container(1),start_ai_tools(1),stop_ai_tools(0),restart_ai_tools(0),_print_shell_help(0),access_shell(0),execute_command(2),_get_service_statuses(0),_get_tool_statuses(0),_get_workspace_status(0),get_status(0),_test_llx_api_connectivity(0),_test_ollama_connectivity(0),test_connectivity(0)  # Manages AI tools container and operations.
  llx/tools/cli.py:
    e: _build_parser,_delegate,_handle_start,_handle_stop,_handle_status,main
    _build_parser()
    _delegate(component;argv)
    _handle_start(args)
    _handle_stop(args)
    _handle_status(args)
    main()
  llx/tools/config_manager.py:
    e: _cmd_load,_cmd_save,_cmd_create_env,_cmd_update_env,_cmd_get_env,_cmd_validate,_cmd_list_models,_cmd_add_model,_cmd_backup,_cmd_docker_env,_cmd_list_profiles,_cmd_summary,_build_parser,_dispatch,main,ConfigManager
    ConfigManager: __init__(1),load_config(1),save_config(2),_load_env_file(1),_save_env_file(2),create_default_env(1),update_env_var(2),get_env_var(2),validate_env_config(0),get_llx_config(0),update_llx_config(1),get_model_config(0),add_model(2),remove_model(1),list_models(0),backup_configs(1),restore_configs(1),generate_docker_env_file(1),validate_docker_configs(0),create_profile(2),load_profile(1),list_profiles(0),get_config_summary(0),_print_config_files_summary(1),_print_env_summary(1),_print_model_summary(1),_count_summary_issues(1),_print_issue_summary(1),_print_profiles_summary(1),print_config_summary(0)  # Manages llx configuration files and settings.
    _cmd_load(args;manager)
    _cmd_save(args;manager)
    _cmd_create_env(args;manager)
    _cmd_update_env(args;manager)
    _cmd_get_env(args;manager)
    _cmd_validate(args;manager)
    _cmd_list_models(args;manager)
    _cmd_add_model(args;manager)
    _cmd_backup(args;manager)
    _cmd_docker_env(args;manager)
    _cmd_list_profiles(args;manager)
    _cmd_summary(args;manager)
    _build_parser()
    _dispatch(args;manager)
    main()
  llx/tools/docker_manager.py:
    e: _build_parser,_dispatch,_handle_restore,_handle_health,_handle_wait,main,DockerManager
    DockerManager: __init__(1),get_compose_cmd(0),run_compose_cmd(2),start_environment(2),stop_environment(2),restart_service(2),get_service_status(1),get_service_logs(3),check_service_health(2),wait_for_service(3),cleanup_environment(2),build_images(2),pull_images(2),get_resource_usage(1),backup_volumes(2),restore_volumes(2),get_network_info(1),print_status_summary(1)  # Manages Docker containers for llx ecosystem.
    _build_parser()
    _dispatch(args;manager)
    _handle_restore(args;manager)
    _handle_health(args;manager)
    _handle_wait(args;manager)
    main()
  llx/tools/health_checker.py:
    e: _build_parser,_write_json_output,_handle_check_command,_handle_quick_command,_handle_monitor_command,_handle_service_command,_handle_container_command,_handle_system_command,_handle_filesystem_command,_handle_network_command,_dispatch,main,HealthChecker
    HealthChecker: __init__(1),_build_service_result(1),_check_redis_health(3),_populate_service_details(3),_check_http_health(4),check_service_health(1),check_container_health(1),check_system_resources(0),check_filesystem_health(0),check_network_connectivity(0),run_comprehensive_health_check(0),_generate_recommendations(1),_print_health_summary(1),run_quick_health_check(0),monitor_services(2)  # Comprehensive health monitoring for llx ecosystem.
    _build_parser()
    _write_json_output(output_path;data)
    _handle_check_command(args;checker)
    _handle_quick_command(args;checker)
    _handle_monitor_command(args;checker)
    _handle_service_command(args;checker)
    _handle_container_command(args;checker)
    _handle_system_command(args;checker)
    _handle_filesystem_command(args;checker)
    _handle_network_command(args;checker)
    _dispatch(args;checker)
    main()
  llx/tools/health_runner.py:
    e: HealthCheckRunner
    HealthCheckRunner: __init__(1),run_comprehensive(0),_generate_recommendations(1),_check_services(1),_check_containers(1),_check_system_resources(1),_check_filesystem(1),_check_network(1),_print_health_summary(1),analyze_monitoring_data(1)  # Runs comprehensive health checks and generates reports.
  llx/tools/model_manager.py:
    e: _cmd_list,_cmd_pull,_cmd_test,_cmd_info,_cmd_recommend,_cmd_benchmark,_cmd_cleanup,_cmd_summary,_cmd_requirements,_build_parser,_dispatch,main,ModelManager
    ModelManager: __init__(1),check_ollama_running(0),check_llx_running(0),get_ollama_models(0),get_llx_models(0),pull_model(2),remove_model(1),test_model(2),test_llx_model(2),get_model_info(1),list_recommended_models(1),get_system_resources(0),recommend_models(1),create_model_profile(1),load_model_profile(1),benchmark_model(2),cleanup_unused_models(1),estimate_model_requirements(1),print_model_summary(0),_print_service_status(0),_print_ollama_models(0),_print_llx_models(0),_print_system_resources(0),_print_recommendations(0)  # Manages local Ollama models and llx configurations.
    _cmd_list(args;manager)
    _cmd_pull(args;manager)
    _cmd_test(args;manager)
    _cmd_info(args;manager)
    _cmd_recommend(args;manager)
    _cmd_benchmark(args;manager)
    _cmd_cleanup(args;manager)
    _cmd_summary(args;manager)
    _cmd_requirements(args;manager)
    _build_parser()
    _dispatch(args;manager)
    main()
  llx/tools/utils/_cmd_uninstall_extension.py:
    e: create_simple_handler
    create_simple_handler(arg_name;arg_label;manager_method)
  llx/tools/vscode_manager.py:
    e: _cmd_start,_cmd_stop,_cmd_restart,_cmd_status,_cmd_logs,_cmd_install_extensions,_cmd_list_extensions,_cmd_update_extensions,_cmd_configure_roocode,_cmd_create_tasks,_cmd_create_launch,_cmd_backup,_cmd_quick_start,_build_parser,_dispatch,main,VSCodeManager
    VSCodeManager: __init__(1),is_vscode_running(0),start_vscode(1),stop_vscode(0),restart_vscode(0),wait_for_vscode_ready(1),check_vscode_health(0),get_vscode_url(0),get_vscode_password(0),install_extensions(1),list_installed_extensions(0),uninstall_extension(1),update_extensions(0),get_vscode_logs(1),configure_roocode(0),create_workspace_tasks(0),create_launch_config(0),backup_settings(1),restore_settings(1),get_status(0),print_status_summary(0),print_quick_start(0)  # Manages VS Code server with AI extensions.
    _cmd_start(args;manager)
    _cmd_stop(args;manager)
    _cmd_restart(args;manager)
    _cmd_status(args;manager)
    _cmd_logs(args;manager)
    _cmd_install_extensions(args;manager)
    _cmd_list_extensions(args;manager)
    _cmd_update_extensions(args;manager)
    _cmd_configure_roocode(args;manager)
    _cmd_create_tasks(args;manager)
    _cmd_create_launch(args;manager)
    _cmd_backup(args;manager)
    _cmd_quick_start(args;manager)
    _build_parser()
    _dispatch(args;manager)
    main()
  llx/utils/aider.py:
    e: _extract_issue_files,_run_aider_fix,_format_aider_result
    _extract_issue_files(issues)
    _run_aider_fix(workdir;prompt;model;files;use_docker)
    _format_aider_result(result)
  llx/utils/cli_main.py:
    e: cli_main
    cli_main(build_parser;dispatch;factory;cleanup)
  llx/utils/formatting.py:
    e: _format_selection,_format_metrics
    _format_selection(selection;selected_model_id)
    _format_metrics(metrics)
  llx/utils/issues.py:
    e: load_issue_source,load_todo_markdown,resolve_issue_source,issue_text,task_prompt_label,build_fix_prompt,_collect_file_context
    load_issue_source(issues_path)
    load_todo_markdown(issues_path)
    resolve_issue_source(workdir;issues_path;fallback_name)
    issue_text(issue)
    task_prompt_label(task)
    build_fix_prompt(project_path;issues;analysis;prompt_limit;action_label)
    _collect_file_context(project_path;issues;max_snippet;max_total)
  llx/utils/models.py:
    e: _select_small_model
    _select_small_model(config)
  my-api/__init__.py:
  my-api/main.py:
    e: health,read_users,read_user,create_user,update_user,delete_user,read_products,read_product,create_product,update_product,delete_product,User,Product
    User:
    Product:
    health()
    read_users()
    read_user(user_id)
    create_user(user)
    update_user(user_id;user)
    delete_user(user_id)
    read_products()
    read_product(product_id)
    create_product(product)
    update_product(product_id;product)
    delete_product(product_id)
  my-api/models.py:
    e: SmoketestRequest,SmoketestResponse,SmoketestDBSchema,SmoketestDBSchemaRequest,SmoketestDBSchemaResponse
    SmoketestRequest:
    SmoketestResponse:
    SmoketestDBSchema:
    SmoketestDBSchemaRequest:
    SmoketestDBSchemaResponse:
  my-api/monitoring.py:
    e: main,CustomMetrics,HealthChecks,PrometheusMetrics,AlertingRules
    CustomMetrics: __init__(0),increment_successful_requests(0),increment_failed_requests(0),record_request_latency(1)
    HealthChecks: __init__(0),check_database_connection(0),check_api_endpoint(0),register_healthchecks(1)
    PrometheusMetrics: __init__(0),register_metrics(1)
    AlertingRules: __init__(0),add_rule(3),register_rules(1)
    main()
  my-api/test_api.py:
    e: client,test_get_users,test_get_user,test_create_user,test_update_user,test_delete_user,test_api_performance,test_api_scalability,test_coverage,test_error_handling,test_security
    client()
    test_get_users(client)
    test_get_user(client)
    test_create_user(client)
    test_update_user(client)
    test_delete_user(client)
    test_api_performance(client)
    test_api_scalability(client)
    test_coverage(client)
    test_error_handling(client)
    test_security(client)
  my-api/tests/test_my_api.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  scripts/pyqual_auto.py:
    e: load_pyqual_config,save_pyqual_config,set_env_file,restore_env_file,backup_config,set_model,force_fix_stage,restore_metrics,run_pyqual,main
    load_pyqual_config(path)
    save_pyqual_config(path;config)
    set_env_file(workdir;model)
    restore_env_file(workdir;old_model)
    backup_config(path)
    set_model(config;model)
    force_fix_stage(config)
    restore_metrics(config;original)
    run_pyqual(workdir;dry_run;verbose)
    main()
  simple_generate.py:
    e: generate_simple_strategy
    generate_simple_strategy(project_path;output)
  test-api-qwen/__init__.py:
  test-api-qwen/main.py:
    e: health_check,create_item,get_items,get_item,update_item,delete_item,Item,ItemResponse,ItemUpdate
    Item:
    ItemResponse:
    ItemUpdate:
    health_check()
    create_item(item)
    get_items()
    get_item(item_id)
    update_item(item_id;item_update)
    delete_item(item_id)
  test-api-qwen/models.py:
    e: ItemBase,ItemCreate,Item
    ItemBase:
    ItemCreate:
    Item:
  test-api-qwen/test_api.py:
    e: test_read_root,test_read_health_check,test_create_item,test_get_item,test_get_item_not_found,test_get_items,test_update_item,test_update_item_not_found,test_delete_item,test_delete_item_not_found,test_invalid_item_data,test_create_item_parametrized,test_read_users,test_create_user,test_get_user,test_get_user_not_found
    test_read_root()
    test_read_health_check()
    test_create_item()
    test_get_item()
    test_get_item_not_found()
    test_get_items()
    test_update_item()
    test_update_item_not_found()
    test_delete_item()
    test_delete_item_not_found()
    test_invalid_item_data()
    test_create_item_parametrized(name;price;expected_status)
    test_read_users()
    test_create_user()
    test_get_user()
    test_get_user_not_found()
  test-api-qwen/tests/test_test_api_qwen.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  test-local-chat.py:
    e: test_llx_health,test_ollama_health,get_available_models,test_llx_models,test_chat_completion,main
    test_llx_health()
    test_ollama_health()
    get_available_models()
    test_llx_models()
    test_chat_completion(model;message)
    main()
  test_aider_docker.py:
    e: test_aider_tool
    test_aider_tool()
  test_aider_mcp.py:
    e: test_aider_tool
    test_aider_tool()
  test_cli.py:
  test_strategy_integration.py:
    e: test_strategy_models,test_strategy_validation
    test_strategy_models()
    test_strategy_validation()
  tests/__init__.py:
  tests/privacy/test_anonymizer.py:
    e: TestProjectAnonymizer
    TestProjectAnonymizer: test_anonymize_python_file(1),test_anonymize_simple_text(0),test_anonymize_project_directory(1),test_respects_file_size_limit(1)
  tests/privacy/test_context.py:
    e: TestAnonymizationContext
    TestAnonymizationContext: test_context_creation(0),test_get_or_create_symbol_consistency(0),test_different_types_get_different_prefixes(0),test_context_serialization(0),test_context_save_load(1)
  tests/privacy/test_deanonymizer.py:
    e: TestProjectDeanonymizer
    TestProjectDeanonymizer: test_deanonymize_symbol(0),test_deanonymize_chat_response(0)
  tests/test_aider_mcp.py:
    e: TestAiderTool
    TestAiderTool: test_aider_not_installed(0),test_aider_success(0),test_aider_timeout(0),test_aider_with_files(0),test_tool_definition(0)  # Test cases for aider MCP tool.
  tests/test_anonymization_context.py:
    e: TestAnonymizationContext
    TestAnonymizationContext: test_context_creation(0),test_get_or_create_symbol_consistency(0),test_different_types_get_different_prefixes(0),test_context_serialization(0),test_context_save_load(1)  # Test AnonymizationContext symbol management.
  tests/test_core.py:
    e: TestProjectMetrics,TestModelSelection,TestContextFit,TestConfig,TestHelpers,TestCode2LLMProject,TestPreLLMProject,TestVallmProject,TestSingleScript
    TestProjectMetrics: test_complexity_score_zero(0),test_complexity_score_high(0),test_scale_score_small(0),test_scale_score_large(0)
    TestModelSelection: test_trivial_gets_free(0),test_small_gets_cheap(0),test_medium_gets_balanced(0),test_large_gets_premium(0),test_local_override(0),test_max_tier_caps(0),test_refactor_hint_upgrades(0),test_quick_fix_downgrades(0),test_has_reasons(0),test_has_scores(0)
    TestContextFit: test_small_fits(0),test_huge_exceeds(0),test_context_auto_upgrade(0)
    TestConfig: test_default_tiers(0)
    TestHelpers: test_extract_cc_value(0)
    TestCode2LLMProject: test_selects_premium(0)  # code2llm: 113 files, 21K lines, CC̄=4.6, max CC=65.
    TestPreLLMProject: test_selects_balanced_or_premium(0),test_analysis_yaml_parsing(0),test_evolution_yaml_parsing(0)  # preLLM: 31 files, 8.9K lines, CC̄=5.0, max CC=28, 3 god modu
    TestVallmProject: test_selects_balanced(0)  # vallm: 56 files, 8604 lines, CC̄=3.5, max CC=42.
    TestSingleScript: test_selects_free(0)
  tests/test_detection.py:
    e: TestProjectTypeDetector
    TestProjectTypeDetector: setup_method(0),test_detect_api_from_path(0),test_detect_webapp_from_path(0),test_detect_cli_from_path(0),test_detect_from_files_package_json(0),test_detect_from_files_setup_py_click(0),test_detect_from_files_requirements_txt_fastapi(0),test_detect_from_files_model_files(0),test_detect_from_files_data_directory(0),test_detect_from_config(0),test_detect_priority(0),test_get_project_config(0),test_get_all_types(0),test_detect_default_to_api(0)  # Test project type detection functionality.
  tests/test_fix_aider_mode.py:
    e: _make_metrics,test_fix_uses_aider_when_code_tool_is_enabled
    _make_metrics()
    test_fix_uses_aider_when_code_tool_is_enabled(tmp_path;monkeypatch)
  tests/test_mcp.py:
    e: event_loop,TestMcpAnalyze,TestMcpSelect,TestMcpProxyStatus,TestMcpServerCli,TestMcpServerEntryPoint,TestMcpPackageEntrypoint
    TestMcpAnalyze: test_analyze_returns_metrics(2),test_analyze_with_task_hint(2)
    TestMcpSelect: test_select_returns_tier(2)
    TestMcpProxyStatus: test_proxy_not_running(1)
    TestMcpServerCli: test_mcp_start_sse_routes_to_sse_transport(2),test_mcp_start_stdio_routes_to_stdio_transport(1),test_mcp_parser_defaults_align_with_sse_server(0)
    TestMcpServerEntryPoint: test_main_dispatches_to_sse_mode(0),test_main_defaults_to_stdio_mode(0)
    TestMcpPackageEntrypoint: test_module_entrypoint_forwards_cli_args(1)
    event_loop()
  tests/test_prellm_integration.py:
    e: TestPreLLMImports,TestPreLLMFunctional,TestPreLLMConfigPaths
    TestPreLLMImports: test_top_level_import(0),test_core_imports(0),test_models_imports(0),test_pipeline_imports(0),test_agents_imports(0),test_context_imports(0),test_utils_imports(0)  # Verify all preLLM public symbols are importable from llx.pre
    TestPreLLMFunctional: test_sensitive_filter_masks_keys(0),test_shell_collector_gathers_context(0),test_budget_tracker_enforces_limit(1),test_decomposition_strategy_enum(0),test_prellm_response_creation(0),test_llm_provider_config_defaults(0),test_env_config_loads(0),test_model_catalog(0),test_trace_recorder_lifecycle(0)  # Functional tests for preLLM components (no LLM calls).
    TestPreLLMConfigPaths: test_configs_directory_exists(0),test_pipelines_yaml_exists(0),test_prompts_yaml_exists(0),test_response_schemas_yaml_exists(0),test_sensitive_rules_yaml_exists(0)  # Verify config files are accessible at expected paths.
  tests/test_privacy.py:
    e: TestAnonymizationPatterns,TestDeanonymization,TestQuickFunctions,TestScanning,TestCustomPatterns,TestAnonymizationResult,TestEdgeCases
    TestAnonymizationPatterns: test_email_anonymization(0),test_api_key_anonymization(0),test_password_anonymization(0),test_phone_anonymization(0),test_pesel_anonymization(0),test_multiple_sensitive_data_types(0)  # Test detection and masking of sensitive data patterns.
    TestDeanonymization: test_simple_deanonymization(0),test_deanonymization_roundtrip(0),test_deanonymization_with_new_text(0),test_empty_mapping_deanonymization(0)  # Test restoring original values from anonymized text.
    TestQuickFunctions: test_quick_anonymize(0),test_quick_deanonymize(0),test_quick_with_salt(0)  # Test convenience functions for one-shot operations.
    TestScanning: test_scan_finds_patterns(0),test_scan_no_modification(0),test_scan_returns_deduplicated(0)  # Test scanning for sensitive data without anonymizing.
    TestCustomPatterns: test_add_custom_pattern(0),test_disable_pattern(0),test_enable_pattern(0)  # Test adding custom patterns.
    TestAnonymizationResult: test_result_has_stats(0),test_result_has_mapping(0)  # Test AnonymizationResult class.
    TestEdgeCases: test_empty_text(0),test_no_sensitive_data(0),test_very_long_value(0),test_overlapping_patterns(0)  # Test edge cases and boundary conditions.
  tests/test_privacy_extended.py:
    e: TestASTAnonymizer,TestStreamingChunkedProcessing,TestMultiFileConsistency,TestContextPersistence,TestDeanonymizeFeatures,TestIntegrationComplexScenarios,TestErrorHandling,TestPerformance
    TestASTAnonymizer: test_ast_anonymize_simple_function(0),test_ast_preserves_dunder_methods(0),test_ast_nested_functions(0),test_ast_class_with_methods(0),test_ast_preserves_builtins(0),test_ast_decorators_preserved(0),test_ast_comprehensions(0),test_ast_lambda_functions(0)  # Test AST-based Python code transformation.
    TestStreamingChunkedProcessing: test_chunked_processor_exact_boundary(1),test_chunked_processor_empty_file(1),test_streaming_anonymizer_empty_project(1),test_streaming_with_single_file(1),test_streaming_large_project_simulation(1),test_streaming_deanonymizer_empty_input(0),test_streaming_deanonymizer_partial_token_handling(0)  # Test streaming and chunked processing.
    TestMultiFileConsistency: test_same_symbol_across_files_consistent(1),test_import_statements_handled(1),test_cross_file_deanonymization(1)  # Test consistency across multiple files.
    TestContextPersistence: test_save_load_with_complex_project(1),test_context_stats_preserved(1),test_context_salt_preserved(1)  # Test saving and loading anonymization context.
    TestDeanonymizeFeatures: test_get_symbol_info_returns_full_details(0),test_list_all_mappings_organized(0),test_deanonymize_unknown_token_reported(0),test_quick_project_deanonymize_function(1)  # Test deanonymization features.
    TestIntegrationComplexScenarios: test_flask_app_anonymization(1),test_dataclass_anonymization(1),test_async_code_anonymization(1),test_end_to_end_workflow(1)  # Complex real-world scenarios.
    TestErrorHandling: test_missing_context_file(1),test_corrupted_context_file(1),test_permission_error_handling(1)  # Test error handling and edge cases.
    TestPerformance: test_large_file_performance(1),test_many_small_files_performance(1),test_context_lookup_performance(0)  # Basic performance characteristics.
  tests/test_privacy_project.py:
    e: TestAnonymizationContext,TestProjectAnonymizer,TestProjectDeanonymizer,TestStreamingDeanonymizer,TestChunkedProcessor,TestStreamingProjectAnonymizer,TestIntegration,TestEdgeCases
    TestAnonymizationContext: test_context_creation(0),test_get_or_create_symbol_consistency(0),test_different_types_get_different_prefixes(0),test_context_serialization(0),test_context_save_load(1)  # Test AnonymizationContext symbol management.
    TestProjectAnonymizer: test_anonymize_python_file(1),test_anonymize_simple_text(0),test_anonymize_project_directory(1),test_respects_file_size_limit(1)  # Test project-level anonymization.
    TestProjectDeanonymizer: test_deanonymize_symbol(0),test_deanonymize_content_tokens(0),test_deanonymize_chat_response(0),test_deanonymize_project_files(1),test_get_symbol_info(0)  # Test project-level deanonymization.
    TestStreamingDeanonymizer: test_feed_chunk_basic(0),test_streaming_finalize(0),test_streaming_stats(0)  # Test streaming deanonymization.
    TestChunkedProcessor: test_process_small_file_single_chunk(1),test_process_large_file_multiple_chunks(1)  # Test chunked file processing.
    TestStreamingProjectAnonymizer: test_streaming_anonymization_progress(1),test_progress_callback_cancellation(1)  # Test streaming project anonymization.
    TestIntegration: test_full_roundtrip_python_code(1),test_context_persistence_roundtrip(1),test_mixed_content_anonymization(1)  # Integration tests for full anonymization/deanonymization rou
    TestEdgeCases: test_empty_project(1),test_syntax_error_file(1),test_unicode_content(1),test_binary_file_handling(1),test_very_long_symbol_names(0)  # Edge cases and error handling.
  tests/test_project_anonymizer.py:
    e: TestProjectAnonymizer
    TestProjectAnonymizer: test_anonymize_python_file(1),test_anonymize_simple_text(0),test_anonymize_project_directory(1),test_respects_file_size_limit(1)  # Test project-level anonymization.
  tests/test_project_deanonymizer.py:
    e: TestProjectDeanonymizer
    TestProjectDeanonymizer: test_deanonymize_symbol(0),test_deanonymize_content_tokens(0),test_deanonymize_chat_response(0),test_deanonymize_project_files(1)  # Test project-level deanonymization.
  tests/test_proxym_integration.py:
    e: TestTierMapping,TestHeaderGeneration,TestProxymClientStructure,TestLlxClientMetrics,TestListModelsUnavailable,TestBaseUrlNormalization
    TestTierMapping: test_free_maps_to_trivial(0),test_local_maps_to_operational(0),test_cheap_maps_to_operational(0),test_balanced_maps_to_standard(0),test_premium_maps_to_complex(0)  # Verify llx ModelTier → proxym TaskTier mapping.
    TestHeaderGeneration: test_empty_metrics_no_headers(0),test_tier_only_sets_task_tier(0),test_metrics_generate_headers(0),test_no_god_modules_omits_header(0)  # Verify X-Llx-* headers built from ProjectMetrics.
    TestProxymClientStructure: test_client_default_url(0),test_client_custom_url(0),test_status_unreachable(0),test_is_available_unreachable(0),test_proxym_status_dataclass(0),test_proxym_response_dataclass(0),test_proxym_response_no_usage(0)  # Test ProxymClient initialization and data models.
    TestLlxClientMetrics: test_metrics_headers_generated(0),test_chat_accepts_metrics_param(0)  # Test LlxClient metrics header integration.
    TestListModelsUnavailable: test_list_models_returns_empty(0)  # Test list_models when proxym is down.
    TestBaseUrlNormalization: test_normalize_litellm_base_url_strips_v1_suffix(0),test_llx_client_normalizes_config_base_url(0),test_proxym_client_normalizes_config_base_url(0)  # Regression tests for llx-side endpoint normalization.
  trace.py:
    e: test
    test()
```

## Source Map

*Top 3 modules by symbol density — signatures for LLM orientation.*

### `llx.litellm_config` (`llx/litellm_config.py`)

```python
def load_litellm_config(project_path)  # CC=1, fan=1
class LiteLLMModelConfig:  # Configuration for a single LiteLLM model.
class LiteLLMConfig:  # Complete LiteLLM configuration.
    def load(cls, project_path)  # CC=4
    def _default_config(cls)  # CC=1
    def get_model_config(model_name)  # CC=3
    def get_models_by_tag(tag)  # CC=3
    def get_models_by_provider(provider)  # CC=3
    def get_models_by_tier(tier)  # CC=3
    def resolve_alias(alias)  # CC=1
    def to_llx_models()  # CC=2
    def get_proxy_config()  # CC=2
```

### `llx.config` (`llx/config.py`)

```python
def normalize_litellm_base_url(base_url)  # CC=5, fan=5
def _apply_toml(config, data)  # CC=9, fan=6
def _apply_yaml_thresholds(config, thresholds)  # CC=4, fan=1
def _apply_yaml_models(config, models)  # CC=3, fan=4
def _apply_yaml_proxy(config, proxy)  # CC=4, fan=1
def _apply_yaml(config, data)  # CC=13, fan=4 ⚠
def _apply_env(config)  # CC=9, fan=3
class ModelConfig:  # Configuration for a single model tier.
class TierThresholds:  # Thresholds that determine which model tier to use.
class ProxyConfig:  # LiteLLM proxy settings.
class LlxConfig:  # Root configuration for llx.
    def __post_init__()  # CC=1
    def load(cls, project_path)  # CC=8
```

### `llx.llm` (`llx/llm.py`)

```python
def _load_dotenv_fallback(env_path)  # CC=10, fan=7 ⚠
def _ensure_dotenv_loaded()  # CC=3, fan=4
def get_llm_model()  # CC=2, fan=4
def get_api_key()  # CC=1, fan=2
def get_llm(model)  # CC=1, fan=1
class LLMResponse:  # Response from an LLM call.
class LLM:  # Synchronous LiteLLM wrapper with .env configuration.
    def __init__(model, api_key)  # CC=4
    def complete(prompt, system, temperature, max_tokens)  # CC=5
    def fix_code(code, error, context)  # CC=3
```

## Call Graph

*513 nodes · 500 edges · 83 modules · CC̄=2.6*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in Taskfile)* | 0 | 1355 | 0 | **1355** |
| `main` *(in examples.privacy.advanced.01_api_integration)* | 15 ⚠ | 0 | 90 | **90** |
| `main` *(in examples.privacy.ml.04_behavioral_learning)* | 11 ⚠ | 0 | 84 | **84** |
| `main` *(in examples.privacy.advanced.02_multi_stage)* | 5 | 0 | 73 | **73** |
| `main` *(in examples.privacy.ml.01_entropy_ml_detection)* | 11 ⚠ | 0 | 65 | **65** |
| `main` *(in examples.privacy.ml.03_contextual_passwords)* | 11 ⚠ | 0 | 64 | **64** |
| `main` *(in examples.privacy.project.01_anonymize_project)* | 4 | 0 | 52 | **52** |
| `context` *(in llx.prellm.cli_context)* | 9 | 1 | 49 | **50** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/llx
# nodes: 513 | edges: 500 | modules: 83
# CC̄=2.6

HUBS[20]:
  Taskfile.print
    CC=0  in:1355  out:0  total:1355
  examples.privacy.advanced.01_api_integration.main
    CC=15  in:0  out:90  total:90
  examples.privacy.ml.04_behavioral_learning.main
    CC=11  in:0  out:84  total:84
  examples.privacy.advanced.02_multi_stage.main
    CC=5  in:0  out:73  total:73
  examples.privacy.ml.01_entropy_ml_detection.main
    CC=11  in:0  out:65  total:65
  examples.privacy.ml.03_contextual_passwords.main
    CC=11  in:0  out:64  total:64
  examples.privacy.project.01_anonymize_project.main
    CC=4  in:0  out:52  total:52
  llx.prellm.cli_context.context
    CC=9  in:1  out:49  total:50
  examples.privacy.streaming.01_streaming_anonymization.main
    CC=5  in:0  out:50  total:50
  test-local-chat.main
    CC=19  in:0  out:49  total:49
  examples.privacy.project.02_deanonymize_project.main
    CC=4  in:0  out:45  total:45
  scripts.pyqual_auto.main
    CC=8  in:0  out:43  total:43
  llx.orchestration.instances.manager.InstanceManager.load_instances
    CC=6  in:0  out:43  total:43
  examples.privacy.advanced.03_cicd_integration.main
    CC=7  in:0  out:42  total:42
  llx.tools.vscode_manager.VSCodeManager.print_quick_start
    CC=1  in:0  out:36  total:36
  llx.orchestration.vscode.config_io.load_vscode_config
    CC=6  in:0  out:36  total:36
  llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.load_config
    CC=6  in:0  out:36  total:36
  llx.planfile.generate_strategy.main
    CC=6  in:0  out:35  total:35
  llx.orchestration.session.manager.SessionManager.load_sessions
    CC=5  in:0  out:34  total:34
  llx.orchestration.llm.orchestrator.LLMOrchestrator.load_config
    CC=6  in:0  out:30  total:30

MODULES:
  Taskfile  [1 funcs]
    print  CC=0  out:0
  examples.docker.docker  [1 funcs]
    docker_exec  CC=0  out:0
  examples.filtering.filtering  [1 funcs]
    select_model  CC=0  out:0
  examples.privacy.advanced.01_api_integration  [2 funcs]
    create_realistic_project  CC=1  out:11
    main  CC=15  out:90
  examples.privacy.advanced.02_multi_stage  [3 funcs]
    anonymize_for_level  CC=6  out:9
    create_business_logic_project  CC=1  out:3
    main  CC=5  out:73
  examples.privacy.advanced.03_cicd_integration  [6 funcs]
    step1_pre_commit_scan  CC=9  out:24
    step2_anonymize_for_audit  CC=2  out:21
    step3_simulate_audit_response  CC=2  out:10
    step4_generate_report  CC=9  out:13
    create_cicd_project  CC=1  out:6
    main  CC=7  out:42
  examples.privacy.basic.01_text_anonymization  [1 funcs]
    main  CC=3  out:27
  examples.privacy.basic.02_custom_patterns  [1 funcs]
    main  CC=3  out:27
  examples.privacy.ml.01_entropy_ml_detection  [1 funcs]
    main  CC=11  out:65
  examples.privacy.ml.03_contextual_passwords  [2 funcs]
    create_test_code_samples  CC=1  out:0
    main  CC=11  out:64
  examples.privacy.ml.04_behavioral_learning  [1 funcs]
    main  CC=11  out:84
  examples.privacy.project.01_anonymize_project  [2 funcs]
    create_sample_project  CC=1  out:5
    main  CC=4  out:52
  examples.privacy.project.02_deanonymize_project  [1 funcs]
    main  CC=4  out:45
  examples.privacy.streaming.01_streaming_anonymization  [2 funcs]
    create_large_project  CC=2  out:3
    main  CC=5  out:50
  llx.analysis.collector  [19 funcs]
    _apply_analysis_yaml  CC=4  out:15
    _apply_evolution_yaml  CC=3  out:10
    _apply_map_text  CC=7  out:7
    _apply_map_yaml  CC=3  out:8
    _classify_scope  CC=6  out:0
    _collect_code2llm_metrics  CC=6  out:13
    _collect_filesystem_metrics  CC=9  out:11
    _collect_redup_metrics  CC=2  out:5
    _collect_vallm_metrics  CC=3  out:5
    _count_map_modules  CC=2  out:3
  llx.analysis.runner  [5 funcs]
    _run_tool  CC=5  out:9
    check_tool  CC=1  out:1
    run_code2llm  CC=1  out:3
    run_redup  CC=1  out:3
    run_vallm  CC=1  out:2
  llx.cli.app  [12 funcs]
    _load_sprint_mapping  CC=3  out:7
    _plan_code_impl  CC=7  out:24
    _run_analysis_tools  CC=1  out:3
    info  CC=1  out:3
    models  CC=1  out:6
    plan_execute  CC=1  out:9
    plan_generate  CC=1  out:7
    plan_review  CC=2  out:12
    proxy_config  CC=1  out:6
    proxy_start  CC=4  out:11
  llx.cli.formatters  [10 funcs]
    _build_model_row  CC=14  out:13
    _build_title  CC=4  out:5
    _filter_models  CC=9  out:3
    _render_agents_table  CC=2  out:2
    _render_models_table  CC=2  out:9
    _render_tags_legend  CC=8  out:9
    _render_tiers_table  CC=2  out:11
    _render_tools_table  CC=3  out:7
    print_info_tables  CC=1  out:4
    print_models_table  CC=8  out:18
  llx.cli.strategy_commands  [4 funcs]
    create_strategy  CC=1  out:9
    run_strategy_command  CC=1  out:13
    validate_strategy  CC=2  out:16
    verify_strategy  CC=6  out:21
  llx.commands._patch_apply  [3 funcs]
    _apply_unified_diff  CC=6  out:14
    _find_hunk_position  CC=9  out:10
    _parse_unified_hunks  CC=16  out:18
  llx.commands.fix  [8 funcs]
    apply_code_changes  CC=3  out:3
    display_model_selection_and_metrics  CC=1  out:7
    execute_aider_fix  CC=7  out:13
    execute_prellm_fix  CC=8  out:18
    fix  CC=4  out:18
    load_errors_data  CC=4  out:9
    prepare_fix_prompt  CC=4  out:1
    select_model_for_fix  CC=3  out:2
  llx.config  [5 funcs]
    __post_init__  CC=1  out:1
    load  CC=8  out:26
    _apply_yaml  CC=13  out:5
    _apply_yaml_proxy  CC=4  out:4
    _apply_yaml_thresholds  CC=4  out:9
  llx.examples.utils  [5 funcs]
    check_dependencies  CC=3  out:4
    check_ollama  CC=3  out:6
    ensure_venv  CC=2  out:3
    process  CC=6  out:11
    run_workflow  CC=3  out:3
  llx.llm  [5 funcs]
    __init__  CC=4  out:3
    _ensure_dotenv_loaded  CC=3  out:4
    _load_dotenv_fallback  CC=10  out:9
    get_api_key  CC=1  out:2
    get_llm_model  CC=2  out:4
  llx.orchestration._utils  [2 funcs]
    load_json  CC=3  out:4
    save_json  CC=2  out:4
  llx.orchestration.cli  [6 funcs]
    _build_parser  CC=1  out:14
    _delegate_to_subpackage  CC=3  out:4
    _handle_health  CC=2  out:7
    _handle_monitor  CC=3  out:14
    _handle_status  CC=4  out:6
    main  CC=8  out:12
  llx.orchestration.cli_utils  [5 funcs]
    cmd_cleanup_wrapper  CC=1  out:2
    cmd_list_wrapper  CC=4  out:6
    cmd_remove_pair_wrapper  CC=5  out:11
    cmd_remove_wrapper  CC=4  out:8
    cmd_status_wrapper  CC=4  out:8
  llx.orchestration.instances.cli  [7 funcs]
    _cmd_create  CC=10  out:6
    _cmd_health  CC=1  out:3
    _cmd_list  CC=3  out:5
    _cmd_metrics  CC=3  out:5
    _cmd_start  CC=3  out:3
    _cmd_stop  CC=3  out:3
    main  CC=1  out:1
  llx.orchestration.instances.manager  [11 funcs]
    __init__  CC=3  out:8
    _check_auto_restart  CC=8  out:8
    _monitor_worker  CC=6  out:8
    create_instance  CC=3  out:6
    get_instance_metrics  CC=9  out:15
    load_instances  CC=6  out:43
    print_status_summary  CC=3  out:23
    remove_instance  CC=6  out:7
    save_instances  CC=6  out:9
    start_instance  CC=7  out:9
  llx.orchestration.llm.cli  [9 funcs]
    _cmd_add_provider  CC=5  out:6
    _cmd_cancel  CC=2  out:2
    _cmd_complete  CC=1  out:1
    _cmd_list_models  CC=3  out:3
    _cmd_list_providers  CC=2  out:3
    _cmd_model_info  CC=3  out:5
    _cmd_usage  CC=1  out:3
    _dispatch  CC=2  out:3
    main  CC=1  out:2
  llx.orchestration.llm.executors  [6 funcs]
    _failed  CC=1  out:1
    execute_anthropic  CC=3  out:15
    execute_ollama  CC=3  out:15
    execute_openai  CC=3  out:14
    execute_request  CC=4  out:4
    messages_to_prompt  CC=5  out:6
  llx.orchestration.llm.health  [2 funcs]
    health_check_worker  CC=3  out:3
    perform_health_checks  CC=5  out:4
  llx.orchestration.llm.orchestrator  [3 funcs]
    _create_default_config  CC=2  out:5
    load_config  CC=6  out:30
    save_config  CC=5  out:6
  llx.orchestration.session.cli  [5 funcs]
    _cmd_cleanup  CC=1  out:3
    _cmd_create  CC=7  out:5
    _cmd_list  CC=3  out:5
    _cmd_queue  CC=1  out:3
    main  CC=1  out:1
  llx.orchestration.session.manager  [8 funcs]
    _cleanup_expired_limits  CC=5  out:3
    _cleanup_worker  CC=3  out:4
    create_session  CC=2  out:5
    load_sessions  CC=5  out:34
    print_status_summary  CC=8  out:26
    release_session  CC=5  out:4
    remove_session  CC=4  out:2
    save_sessions  CC=5  out:8
  llx.orchestration.vscode.cli  [8 funcs]
    _cmd_add_account  CC=5  out:5
    _cmd_create  CC=5  out:4
    _cmd_list  CC=2  out:4
    _cmd_list_accounts  CC=2  out:4
    _cmd_sessions  CC=3  out:4
    _cmd_start  CC=3  out:4
    _cmd_stop  CC=4  out:4
    main  CC=1  out:2
  llx.orchestration.vscode.config_io  [2 funcs]
    load_vscode_config  CC=6  out:36
    save_vscode_config  CC=5  out:10
  llx.orchestration.vscode.orchestrator  [15 funcs]
    _config_save_worker  CC=3  out:3
    _create_default_config  CC=1  out:4
    _session_cleanup_worker  CC=6  out:8
    _start_browser_for_instance  CC=2  out:3
    add_account  CC=2  out:2
    create_instance  CC=5  out:6
    end_session  CC=4  out:3
    load_config  CC=6  out:36
    print_status_summary  CC=11  out:25
    remove_account  CC=5  out:4
  llx.planfile.examples  [4 funcs]
    example_programmatic_strategy  CC=1  out:11
    example_run_strategy  CC=1  out:1
    example_validate_strategy  CC=2  out:5
    example_verify_strategy  CC=2  out:4
  llx.planfile.executor_simple  [7 funcs]
    _build_task_prompt  CC=2  out:5
    _execute_task  CC=5  out:18
    _get_sprint_tasks  CC=3  out:0
    _load_strategy  CC=2  out:4
    _normalize_strategy  CC=12  out:17
    _select_model  CC=13  out:15
    execute_strategy  CC=7  out:16
  llx.planfile.generate_strategy  [18 funcs]
    _build_strategy_prompt  CC=7  out:7
    _call_llm_for_strategy  CC=2  out:14
    _fix_indentation  CC=7  out:9
    _fix_list_formatting  CC=9  out:13
    _fix_yaml_formatting  CC=2  out:10
    _generate_tasks_from_patterns  CC=6  out:9
    _normalize_goal  CC=3  out:9
    _normalize_metadata  CC=1  out:6
    _normalize_quality_gates  CC=4  out:4
    _normalize_single_gate  CC=2  out:8
  llx.planfile.runner  [5 funcs]
    analyze_project_metrics  CC=8  out:11
    apply_strategy_to_tickets  CC=8  out:8
    load_valid_strategy  CC=3  out:7
    run_strategy  CC=8  out:23
    verify_strategy_post_execution  CC=12  out:12
  llx.prellm.agents.preprocessor  [2 funcs]
    _get_codebase_indexer_class  CC=1  out:2
    _get_user_memory_class  CC=1  out:2
  llx.prellm.budget  [3 funcs]
    _ensure_loaded  CC=5  out:11
    _persist  CC=6  out:9
    summary  CC=2  out:4
  llx.prellm.chains.process_chain  [1 funcs]
    _run_engine  CC=7  out:9
  llx.prellm.cli  [4 funcs]
    session_clear_cmd  CC=2  out:11
    session_export_cmd  CC=1  out:17
    session_import_cmd  CC=1  out:14
    session_list_cmd  CC=3  out:18
  llx.prellm.cli_commands  [6 funcs]
    _doctor_check_config  CC=5  out:4
    _doctor_check_providers  CC=6  out:8
    budget  CC=7  out:25
    doctor  CC=5  out:17
    models  CC=5  out:17
    serve  CC=8  out:21
  llx.prellm.cli_config  [1 funcs]
    config_show_cmd  CC=8  out:25
  llx.prellm.cli_context  [2 funcs]
    context  CC=9  out:49
    context_show_cmd  CC=1  out:6
  llx.prellm.cli_query  [4 funcs]
    _execute_and_format_result  CC=9  out:21
    _handle_query_options  CC=9  out:6
    _init_logging  CC=1  out:2
    _initialize_execution  CC=4  out:5
  llx.prellm.context.folder_compressor  [3 funcs]
    to_dependency_graph  CC=11  out:14
    to_summary  CC=11  out:8
    to_toon  CC=8  out:17
  llx.prellm.context_ops  [7 funcs]
    build_sensitive_filter  CC=4  out:5
    collect_environment_context  CC=4  out:8
    collect_user_context  CC=4  out:3
    compress_codebase_folder  CC=4  out:3
    generate_context_schema  CC=4  out:4
    initialize_context_components  CC=5  out:4
    prepare_context  CC=2  out:9
  llx.prellm.core  [5 funcs]
    _apply_config_overrides  CC=7  out:4
    _resolve_pipeline_name  CC=3  out:1
    _trace_preprocess_configuration  CC=3  out:2
    preprocess_and_execute  CC=5  out:8
    preprocess_and_execute_sync  CC=1  out:2
  llx.prellm.env_config  [2 funcs]
    _load_dotenv  CC=4  out:3
    get_env_config  CC=3  out:24
  llx.prellm.extractors  [11 funcs]
    build_decomposition_result  CC=4  out:7
    build_executor_system_prompt  CC=4  out:6
    extract_classification_from_state  CC=2  out:7
    extract_matched_rule_from_state  CC=5  out:3
    extract_missing_fields_from_state  CC=2  out:2
    extract_structure_from_state  CC=2  out:6
    extract_sub_queries_from_state  CC=6  out:5
    format_classification_context  CC=6  out:13
    format_context_schema  CC=7  out:10
    format_runtime_context  CC=5  out:11
  llx.prellm.logging_setup  [3 funcs]
    _get_version  CC=2  out:0
    get_logger  CC=2  out:5
    setup_logging  CC=5  out:8
  llx.prellm.pipeline.engine  [1 funcs]
    from_yaml  CC=1  out:2
  llx.prellm.pipeline_ops  [1 funcs]
    execute_v3_pipeline  CC=10  out:27
  llx.prellm.server  [6 funcs]
    _build_prellm_meta  CC=3  out:2
    _parse_model_pair  CC=10  out:13
    _stream_response  CC=4  out:15
    batch_process  CC=3  out:8
    chat_completions  CC=12  out:22
    create_app  CC=7  out:1
  llx.prellm.trace  [8 funcs]
    _generate_decision_tree  CC=10  out:22
    _generate_markdown_step_details  CC=8  out:14
    _generate_markdown_summary  CC=3  out:4
    _generate_step_log  CC=4  out:4
    start  CC=1  out:2
    stop  CC=1  out:2
    _safe_json  CC=3  out:4
    _sanitize  CC=13  out:17
  llx.privacy._project_context  [4 funcs]
    _generate_symbol  CC=2  out:4
    _get_mapping_dict  CC=1  out:1
    from_dict  CC=1  out:15
    to_dict  CC=1  out:6
  llx.privacy.deanonymize_engine  [3 funcs]
    __init__  CC=1  out:1
    deanonymize_file  CC=3  out:4
    deanonymize_text  CC=7  out:15
  llx.pyqual_plugins.bump_version  [6 funcs]
    bump_patch_version  CC=1  out:1
    git_commit_version_bump  CC=2  out:4
    main  CC=5  out:18
    parse_version  CC=2  out:8
    update_pyproject_toml  CC=1  out:5
    update_version_file  CC=1  out:2
  llx.pyqual_plugins.detect_secrets  [3 funcs]
    _run_detect_secrets_subprocess  CC=4  out:6
    main  CC=2  out:5
    run_detect_secrets  CC=1  out:2
  llx.pyqual_plugins.lint  [3 funcs]
    main  CC=3  out:7
    run_ruff_format_check  CC=4  out:6
    run_ruff_lint  CC=6  out:10
  llx.pyqual_plugins.publish  [4 funcs]
    check_version_on_pypi  CC=2  out:1
    get_current_version  CC=2  out:5
    main  CC=3  out:7
    upload_to_pypi  CC=2  out:4
  llx.pyqual_plugins.security_audit  [3 funcs]
    main  CC=3  out:7
    run_bandit  CC=4  out:8
    run_pip_audit  CC=4  out:7
  llx.pyqual_plugins.type_check  [2 funcs]
    main  CC=2  out:5
    run_mypy  CC=7  out:11
  llx.pyqual_plugins.verify_push_publish  [4 funcs]
    get_current_version  CC=2  out:5
    main  CC=3  out:6
    verify_publish  CC=6  out:9
    verify_push  CC=3  out:8
  llx.tools.ai_tools_manager  [8 funcs]
    _ensure_llx_api_running  CC=5  out:6
    _print_shell_help  CC=2  out:16
    _start_ai_tools_container  CC=4  out:7
    access_shell  CC=3  out:6
    execute_command  CC=4  out:2
    restart_ai_tools  CC=2  out:4
    start_ai_tools  CC=3  out:4
    stop_ai_tools  CC=3  out:5
  llx.tools.cli  [6 funcs]
    _build_parser  CC=2  out:11
    _delegate  CC=3  out:4
    _handle_start  CC=2  out:1
    _handle_status  CC=1  out:1
    _handle_stop  CC=2  out:1
    main  CC=8  out:14
  llx.tools.config_manager  [24 funcs]
    _print_config_files_summary  CC=4  out:3
    _print_env_summary  CC=4  out:5
    _print_issue_summary  CC=6  out:8
    _print_model_summary  CC=2  out:5
    _print_profiles_summary  CC=2  out:2
    backup_configs  CC=7  out:21
    create_default_env  CC=3  out:3
    create_profile  CC=4  out:10
    generate_docker_env_file  CC=3  out:4
    list_models  CC=3  out:18
  llx.tools.docker_manager  [18 funcs]
    backup_volumes  CC=6  out:17
    build_images  CC=4  out:6
    check_service_health  CC=7  out:11
    cleanup_environment  CC=4  out:5
    get_network_info  CC=4  out:11
    get_resource_usage  CC=6  out:8
    get_service_status  CC=4  out:9
    print_status_summary  CC=10  out:27
    pull_images  CC=4  out:6
    restart_service  CC=6  out:5
  llx.tools.health_checker  [11 funcs]
    monitor_services  CC=6  out:30
    run_quick_health_check  CC=5  out:6
    _handle_check_command  CC=2  out:2
    _handle_container_command  CC=2  out:4
    _handle_filesystem_command  CC=1  out:5
    _handle_monitor_command  CC=2  out:2
    _handle_network_command  CC=1  out:5
    _handle_service_command  CC=2  out:4
    _handle_system_command  CC=1  out:3
    _write_json_output  CC=1  out:2
  llx.tools.health_runner  [7 funcs]
    _check_containers  CC=4  out:5
    _check_filesystem  CC=3  out:5
    _check_network  CC=4  out:5
    _check_services  CC=5  out:8
    _check_system_resources  CC=3  out:9
    _print_health_summary  CC=8  out:23
    run_comprehensive  CC=2  out:11
  llx.tools.model_manager  [22 funcs]
    _print_llx_models  CC=4  out:8
    _print_ollama_models  CC=5  out:12
    _print_recommendations  CC=4  out:7
    _print_service_status  CC=5  out:4
    _print_system_resources  CC=1  out:5
    benchmark_model  CC=6  out:17
    cleanup_unused_models  CC=7  out:9
    create_model_profile  CC=5  out:11
    get_system_resources  CC=5  out:10
    print_model_summary  CC=1  out:8
  llx.tools.utils._cmd_uninstall_extension  [1 funcs]
    create_simple_handler  CC=1  out:4
  llx.tools.vscode_manager  [18 funcs]
    backup_settings  CC=4  out:17
    configure_roocode  CC=5  out:13
    create_launch_config  CC=3  out:10
    create_workspace_tasks  CC=3  out:10
    install_extensions  CC=9  out:24
    list_installed_extensions  CC=6  out:5
    print_quick_start  CC=1  out:36
    print_status_summary  CC=10  out:16
    restart_vscode  CC=2  out:4
    restore_settings  CC=8  out:20
  project.map.toon  [62 funcs]
    _apply_env  CC=0  out:0
    _apply_json_patch_strategy  CC=0  out:0
    _apply_markdown_code_block_strategy  CC=0  out:0
    _apply_openai_patch_strategy  CC=0  out:0
    _current_month_key  CC=0  out:0
    _dict_to_mappings  CC=0  out:0
    _extract_issue_files  CC=0  out:0
    _extract_module_docstring  CC=0  out:0
    _format_metrics  CC=0  out:0
    _format_selection  CC=0  out:0
  scripts.pyqual_auto  [2 funcs]
    main  CC=8  out:43
    run_pyqual  CC=3  out:5
  simple_generate  [1 funcs]
    generate_simple_strategy  CC=4  out:18
  test-local-chat  [6 funcs]
    get_available_models  CC=4  out:3
    main  CC=19  out:49
    test_chat_completion  CC=4  out:16
    test_llx_health  CC=2  out:1
    test_llx_models  CC=4  out:3
    test_ollama_health  CC=2  out:1
  trace  [1 funcs]
    test  CC=11  out:10

EDGES:
  trace.test → project.map.toon._normalize_strategy_data
  simple_generate.generate_simple_strategy → project.map.toon.generate_strategy_with_fix
  simple_generate.generate_simple_strategy → project.map.toon.save_fixed_strategy
  test-local-chat.test_chat_completion → Taskfile.print
  test-local-chat.main → Taskfile.print
  test-local-chat.main → test-local-chat.test_llx_health
  test-local-chat.main → test-local-chat.test_ollama_health
  test-local-chat.main → test-local-chat.get_available_models
  test-local-chat.main → test-local-chat.test_llx_models
  examples.privacy.ml.01_entropy_ml_detection.main → Taskfile.print
  examples.privacy.ml.04_behavioral_learning.main → Taskfile.print
  examples.privacy.ml.03_contextual_passwords.main → Taskfile.print
  examples.privacy.ml.03_contextual_passwords.main → examples.privacy.ml.03_contextual_passwords.create_test_code_samples
  examples.privacy.streaming.01_streaming_anonymization.main → Taskfile.print
  examples.privacy.streaming.01_streaming_anonymization.main → examples.privacy.streaming.01_streaming_anonymization.create_large_project
  examples.privacy.project.02_deanonymize_project.main → Taskfile.print
  examples.privacy.project.01_anonymize_project.main → Taskfile.print
  examples.privacy.project.01_anonymize_project.main → examples.privacy.project.01_anonymize_project.create_sample_project
  examples.privacy.advanced.03_cicd_integration.CICDPrivacyPipeline.step1_pre_commit_scan → Taskfile.print
  examples.privacy.advanced.03_cicd_integration.CICDPrivacyPipeline.step2_anonymize_for_audit → Taskfile.print
  examples.privacy.advanced.03_cicd_integration.CICDPrivacyPipeline.step3_simulate_audit_response → Taskfile.print
  examples.privacy.advanced.03_cicd_integration.CICDPrivacyPipeline.step4_generate_report → Taskfile.print
  examples.privacy.advanced.03_cicd_integration.main → Taskfile.print
  examples.privacy.advanced.03_cicd_integration.main → examples.privacy.advanced.03_cicd_integration.create_cicd_project
  examples.privacy.advanced.02_multi_stage.MultiStageAnonymizer.anonymize_for_level → Taskfile.print
  examples.privacy.advanced.02_multi_stage.main → Taskfile.print
  examples.privacy.advanced.02_multi_stage.main → examples.privacy.advanced.02_multi_stage.create_business_logic_project
  examples.privacy.advanced.01_api_integration.main → Taskfile.print
  examples.privacy.advanced.01_api_integration.main → examples.privacy.advanced.01_api_integration.create_realistic_project
  examples.privacy.basic.01_text_anonymization.main → Taskfile.print
  examples.privacy.basic.01_text_anonymization.main → project.map.toon.quick_anonymize
  examples.privacy.basic.02_custom_patterns.main → Taskfile.print
  scripts.pyqual_auto.run_pyqual → Taskfile.print
  scripts.pyqual_auto.main → Taskfile.print
  llx.config.LlxConfig.__post_init__ → project.map.toon.normalize_litellm_base_url
  llx.config.LlxConfig.load → project.map.toon._apply_env
  llx.config.LlxConfig.load → project.map.toon.normalize_litellm_base_url
  llx.config._apply_yaml → llx.config._apply_yaml_proxy
  llx.config._apply_yaml → llx.config._apply_yaml_thresholds
  llx.llm._ensure_dotenv_loaded → llx.llm._load_dotenv_fallback
  llx.llm.get_llm_model → llx.llm._ensure_dotenv_loaded
  llx.llm.get_api_key → llx.llm._ensure_dotenv_loaded
  llx.llm.LLM.__init__ → project.map.toon.get_llm_model
  llx.llm.LLM.__init__ → project.map.toon.get_api_key
  llx.commands._patch_apply._apply_unified_diff → llx.commands._patch_apply._parse_unified_hunks
  llx.commands._patch_apply._apply_unified_diff → llx.commands._patch_apply._find_hunk_position
  llx.commands.fix.apply_code_changes → project.map.toon._apply_json_patch_strategy
  llx.commands.fix.apply_code_changes → project.map.toon._apply_openai_patch_strategy
  llx.commands.fix.apply_code_changes → project.map.toon._apply_markdown_code_block_strategy
  llx.commands.fix.load_errors_data → project.map.toon.load_issue_source
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (2)

**`API Integration Tests`**
- `GET /health` → `200`
- `GET /api/v1/status` → `200`
- `POST /api/v1/test` → `201`
- assert `status == ok`
- assert `response_time < 1000`

**`Auto-generated API Smoke Tests`**
- `GET /health` → `200`
- `GET /users/` → `200`
- `POST /users/` → `201`
- assert `status < 500`
- assert `response_time < 2000`
- detectors: FastAPIDetector, ConfigEndpointDetector

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

Intelligent LLM model router driven by real code metrics — successor to preLLM
