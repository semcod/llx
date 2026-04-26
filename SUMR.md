# llx

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `llx`
- **version**: `0.1.60`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements-dev.txt, requirements.txt, Taskfile.yml, Makefile, testql(3), app.doql.less, pyqual.yaml, goal.yaml, .env.example, Dockerfile, docker-compose.yml, src(3 mod), project/(6 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: llx;
  version: 0.1.60;
}

dependencies {
  runtime: "typer>=0.24, rich>=13.0, pydantic>=2.0, pydantic-settings>=2.0, pydantic-yaml>=1.0, tomli>=2.0; python_version<'3.11', httpx>=0.27, pyyaml>=6.0, requests>=2.31, docker>=6.0, psutil>=5.9, planfile>=0.1.30";
  dev: "pytest>=8.0, pytest-cov>=5.0, ruff>=0.5, mypy>=1.10";
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
  step-2: run cmd=if command -v uv > /dev/null 2>&1; then \;
  step-3: run cmd=uv venv; \;
  step-4: run cmd=.venv/bin/pip install --upgrade pip; \;
  step-5: run cmd=uv pip install -e ".[dev]"; \;
  step-6: run cmd=else \;
  step-7: run cmd=python -m venv .venv; \;
  step-8: run cmd=.venv/bin/pip install --upgrade pip; \;
  step-9: run cmd=.venv/bin/pip install -e ".[dev]"; \;
  step-10: run cmd=fi;
  step-11: run cmd=echo "✅ Installation completed!";
  step-12: run cmd=echo "Run 'source .venv/bin/activate' to activate the virtual environment";
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
  step-1: run cmd=echo "🔍 Running linting with ruff...";
  step-2: run cmd=.venv/bin/python -m ruff check llx/;
  step-3: run cmd=.venv/bin/python -m ruff check tests/;
  step-4: run cmd=.venv/bin/python -m mypy llx/ --ignore-missing-imports;
}

workflow[name="format"] {
  trigger: manual;
  step-1: run cmd=echo "📝 Formatting code with ruff...";
  step-2: run cmd=.venv/bin/python -m ruff format llx/;
  step-3: run cmd=.venv/bin/python -m ruff format tests/;
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
  step-1: run cmd=echo "🔍 CI linting with ruff...";
  step-2: run cmd=.venv/bin/python -m ruff check llx/ --format=github;
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

*482 nodes · 500 edges · 91 modules · CC̄=2.6*

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
# nodes: 482 | edges: 500 | modules: 91
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
  examples.privacy.project.02_deanonymize_project.main
    CC=4  in:0  out:45  total:45
  llx.orchestration.instances.manager.InstanceManager.load_instances
    CC=6  in:0  out:43  total:43
  scripts.pyqual_auto.main
    CC=8  in:0  out:43  total:43
  examples.privacy.advanced.03_cicd_integration.main
    CC=7  in:0  out:42  total:42
  llx.tools.vscode_manager.VSCodeManager.print_quick_start
    CC=1  in:0  out:36  total:36
  llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.load_config
    CC=6  in:0  out:36  total:36
  llx.orchestration.vscode.config_io.load_vscode_config
    CC=6  in:0  out:36  total:36
  llx.planfile.generate_strategy.main
    CC=6  in:0  out:35  total:35
  llx.orchestration.session.manager.SessionManager.load_sessions
    CC=5  in:0  out:34  total:34
  llx.prellm.env_config.get_env_config
    CC=3  in:7  out:24  total:31
  llx.tools.health_checker.HealthChecker.monitor_services
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
  llx.commands._patch_apply  [5 funcs]
    _apply_unified_diff  CC=6  out:14
    _classify_line  CC=6  out:5
    _finalize_hunk  CC=3  out:1
    _find_hunk_position  CC=9  out:10
    _parse_unified_hunks  CC=10  out:14
  llx.commands.fix  [8 funcs]
    apply_code_changes  CC=3  out:3
    display_model_selection_and_metrics  CC=1  out:7
    execute_aider_fix  CC=7  out:13
    execute_prellm_fix  CC=8  out:18
    fix  CC=4  out:18
    load_errors_data  CC=4  out:9
    prepare_fix_prompt  CC=4  out:1
    select_model_for_fix  CC=3  out:2
  llx.examples.utils  [5 funcs]
    check_dependencies  CC=3  out:4
    check_ollama  CC=3  out:6
    ensure_venv  CC=2  out:3
    process  CC=6  out:11
    run_workflow  CC=3  out:3
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
  llx.orchestration.llm.orchestrator  [16 funcs]
    _config_save_worker  CC=3  out:3
    _create_default_config  CC=2  out:5
    _execute_request  CC=4  out:9
    _print_model_summary  CC=4  out:6
    _print_provider_status  CC=2  out:6
    _print_usage_stats  CC=1  out:7
    add_model  CC=2  out:2
    add_provider  CC=3  out:3
    cancel_request  CC=2  out:1
    complete_request  CC=4  out:11
  llx.orchestration.queue.cli  [5 funcs]
    _cmd_add  CC=5  out:4
    _cmd_complete  CC=2  out:2
    _cmd_dequeue  CC=3  out:4
    _cmd_enqueue  CC=6  out:5
    _cmd_status  CC=1  out:3
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
  llx.planfile.examples  [5 funcs]
    example_create_strategy  CC=1  out:1
    example_programmatic_strategy  CC=1  out:11
    example_run_strategy  CC=1  out:1
    example_validate_strategy  CC=2  out:5
    example_verify_strategy  CC=2  out:4
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
  llx.prellm._nfo_compat  [1 funcs]
    configure  CC=3  out:4
  llx.prellm.agents.preprocessor  [2 funcs]
    _get_codebase_indexer_class  CC=1  out:2
    _get_user_memory_class  CC=1  out:2
  llx.prellm.budget  [5 funcs]
    _ensure_loaded  CC=5  out:11
    _persist  CC=6  out:9
    summary  CC=2  out:4
    _current_month_key  CC=1  out:2
    get_budget_tracker  CC=6  out:1
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
  llx.prellm.context.folder_compressor  [6 funcs]
    to_dependency_graph  CC=11  out:14
    to_summary  CC=11  out:8
    to_toon  CC=8  out:17
    _extract_module_docstring  CC=6  out:11
    _path_to_module  CC=3  out:5
    _relative_path  CC=2  out:3
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
  llx.prellm.model_catalog  [2 funcs]
    list_model_pairs  CC=8  out:4
    list_openrouter_models  CC=8  out:4
  llx.prellm.pipeline.engine  [1 funcs]
    from_yaml  CC=1  out:2
  llx.prellm.pipeline.loader  [2 funcs]
    build_pipeline  CC=2  out:2
    load_pipeline_config  CC=5  out:20
  llx.prellm.pipeline_ops  [1 funcs]
    execute_v3_pipeline  CC=10  out:27
  llx.prellm.server  [6 funcs]
    _build_prellm_meta  CC=3  out:2
    _parse_model_pair  CC=10  out:13
    _stream_response  CC=4  out:15
    batch_process  CC=3  out:8
    chat_completions  CC=12  out:22
    create_app  CC=7  out:1
  llx.prellm.trace  [11 funcs]
    _generate_decision_tree  CC=10  out:22
    _generate_markdown_step_details  CC=8  out:14
    _generate_markdown_summary  CC=3  out:4
    _generate_step_log  CC=4  out:4
    start  CC=1  out:2
    stop  CC=1  out:2
    _safe_json  CC=3  out:4
    _sanitize  CC=13  out:17
    _step_icon  CC=1  out:1
    get_current_trace  CC=1  out:1
  llx.prellm.utils.lazy_imports  [1 funcs]
    lazy_import_global  CC=2  out:3
  llx.privacy.__core  [1 funcs]
    quick_anonymize  CC=1  out:2
  llx.privacy._project_context  [8 funcs]
    _generate_symbol  CC=2  out:4
    _get_mapping_dict  CC=1  out:1
    from_dict  CC=1  out:15
    to_dict  CC=1  out:6
    _dict_to_mappings  CC=2  out:2
    _mapping_dict_for  CC=1  out:1
    _mappings_to_dict  CC=2  out:1
    _symbol_prefix  CC=1  out:1
  llx.privacy.deanonymize_engine  [3 funcs]
    __init__  CC=1  out:1
    deanonymize_file  CC=3  out:4
    deanonymize_text  CC=7  out:15
  llx.privacy.deanonymize_utils  [6 funcs]
    build_reverse_lookup  CC=3  out:1
    find_content_tokens  CC=1  out:2
    find_symbol_tokens  CC=1  out:5
    get_content_mapping  CC=2  out:1
    restore_decorators  CC=1  out:3
    restore_imports  CC=1  out:4
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
  llx.tools._docker  [1 funcs]
    docker_cp  CC=1  out:1
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
    main  CC=6  out:11
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
  llx.utils.aider  [2 funcs]
    _extract_issue_files  CC=9  out:8
    _run_aider_fix  CC=10  out:19
  llx.utils.cli_main  [1 funcs]
    cli_main  CC=3  out:6
  llx.utils.formatting  [2 funcs]
    _format_metrics  CC=2  out:24
    _format_selection  CC=4  out:3
  llx.utils.issues  [2 funcs]
    build_fix_prompt  CC=11  out:11
    load_issue_source  CC=9  out:10
  project.map.toon  [1 funcs]
    create_strategy_command  CC=0  out:0
  scripts.pyqual_auto  [2 funcs]
    main  CC=8  out:43
    run_pyqual  CC=3  out:5
  simple_generate  [1 funcs]
    generate_simple_strategy  CC=4  out:18
  test-local-chat  [11 funcs]
    _check_services  CC=3  out:5
    _print_models  CC=4  out:12
    _print_summary  CC=2  out:9
    _run_chat_tests  CC=4  out:9
    _select_test_models  CC=7  out:4
    get_available_models  CC=4  out:3
    main  CC=4  out:13
    test_chat_completion  CC=4  out:16
    test_llx_health  CC=2  out:1
    test_llx_models  CC=4  out:3
  trace  [1 funcs]
    test  CC=11  out:10

EDGES:
  trace.test → llx.planfile.generate_strategy._normalize_strategy_data
  simple_generate.generate_simple_strategy → llx.planfile.generate_strategy.generate_strategy_with_fix
  simple_generate.generate_simple_strategy → llx.planfile.generate_strategy.save_fixed_strategy
  test-local-chat.test_chat_completion → Taskfile.print
  test-local-chat._check_services → Taskfile.print
  test-local-chat._check_services → test-local-chat.test_llx_health
  test-local-chat._check_services → test-local-chat.test_ollama_health
  test-local-chat._print_models → Taskfile.print
  test-local-chat._print_models → test-local-chat.get_available_models
  test-local-chat._print_models → test-local-chat.test_llx_models
  test-local-chat._run_chat_tests → Taskfile.print
  test-local-chat._run_chat_tests → test-local-chat.test_chat_completion
  test-local-chat._print_summary → Taskfile.print
  test-local-chat.main → Taskfile.print
  test-local-chat.main → test-local-chat._check_services
  test-local-chat.main → test-local-chat._print_models
  test-local-chat.main → test-local-chat._select_test_models
  test-local-chat.main → test-local-chat._run_chat_tests
  test-local-chat.main → test-local-chat._print_summary
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
  examples.privacy.basic.01_text_anonymization.main → llx.privacy.__core.quick_anonymize
  examples.privacy.basic.02_custom_patterns.main → Taskfile.print
  scripts.pyqual_auto.run_pyqual → Taskfile.print
  scripts.pyqual_auto.main → Taskfile.print
  llx.commands._patch_apply._apply_unified_diff → llx.commands._patch_apply._parse_unified_hunks
  llx.commands._patch_apply._apply_unified_diff → llx.commands._patch_apply._find_hunk_position
  llx.commands._patch_apply._parse_unified_hunks → llx.commands._patch_apply._classify_line
  llx.commands._patch_apply._parse_unified_hunks → llx.commands._patch_apply._finalize_hunk
  llx.commands.fix.load_errors_data → llx.utils.issues.load_issue_source
  llx.commands.fix.select_model_for_fix → examples.filtering.filtering.select_model
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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/llx
# nodes: 482 | edges: 500 | modules: 91
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
  examples.privacy.project.02_deanonymize_project.main
    CC=4  in:0  out:45  total:45
  llx.orchestration.instances.manager.InstanceManager.load_instances
    CC=6  in:0  out:43  total:43
  scripts.pyqual_auto.main
    CC=8  in:0  out:43  total:43
  examples.privacy.advanced.03_cicd_integration.main
    CC=7  in:0  out:42  total:42
  llx.tools.vscode_manager.VSCodeManager.print_quick_start
    CC=1  in:0  out:36  total:36
  llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.load_config
    CC=6  in:0  out:36  total:36
  llx.orchestration.vscode.config_io.load_vscode_config
    CC=6  in:0  out:36  total:36
  llx.planfile.generate_strategy.main
    CC=6  in:0  out:35  total:35
  llx.orchestration.session.manager.SessionManager.load_sessions
    CC=5  in:0  out:34  total:34
  llx.prellm.env_config.get_env_config
    CC=3  in:7  out:24  total:31
  llx.tools.health_checker.HealthChecker.monitor_services
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
  llx.commands._patch_apply  [5 funcs]
    _apply_unified_diff  CC=6  out:14
    _classify_line  CC=6  out:5
    _finalize_hunk  CC=3  out:1
    _find_hunk_position  CC=9  out:10
    _parse_unified_hunks  CC=10  out:14
  llx.commands.fix  [8 funcs]
    apply_code_changes  CC=3  out:3
    display_model_selection_and_metrics  CC=1  out:7
    execute_aider_fix  CC=7  out:13
    execute_prellm_fix  CC=8  out:18
    fix  CC=4  out:18
    load_errors_data  CC=4  out:9
    prepare_fix_prompt  CC=4  out:1
    select_model_for_fix  CC=3  out:2
  llx.examples.utils  [5 funcs]
    check_dependencies  CC=3  out:4
    check_ollama  CC=3  out:6
    ensure_venv  CC=2  out:3
    process  CC=6  out:11
    run_workflow  CC=3  out:3
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
  llx.orchestration.llm.orchestrator  [16 funcs]
    _config_save_worker  CC=3  out:3
    _create_default_config  CC=2  out:5
    _execute_request  CC=4  out:9
    _print_model_summary  CC=4  out:6
    _print_provider_status  CC=2  out:6
    _print_usage_stats  CC=1  out:7
    add_model  CC=2  out:2
    add_provider  CC=3  out:3
    cancel_request  CC=2  out:1
    complete_request  CC=4  out:11
  llx.orchestration.queue.cli  [5 funcs]
    _cmd_add  CC=5  out:4
    _cmd_complete  CC=2  out:2
    _cmd_dequeue  CC=3  out:4
    _cmd_enqueue  CC=6  out:5
    _cmd_status  CC=1  out:3
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
  llx.planfile.examples  [5 funcs]
    example_create_strategy  CC=1  out:1
    example_programmatic_strategy  CC=1  out:11
    example_run_strategy  CC=1  out:1
    example_validate_strategy  CC=2  out:5
    example_verify_strategy  CC=2  out:4
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
  llx.prellm._nfo_compat  [1 funcs]
    configure  CC=3  out:4
  llx.prellm.agents.preprocessor  [2 funcs]
    _get_codebase_indexer_class  CC=1  out:2
    _get_user_memory_class  CC=1  out:2
  llx.prellm.budget  [5 funcs]
    _ensure_loaded  CC=5  out:11
    _persist  CC=6  out:9
    summary  CC=2  out:4
    _current_month_key  CC=1  out:2
    get_budget_tracker  CC=6  out:1
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
  llx.prellm.context.folder_compressor  [6 funcs]
    to_dependency_graph  CC=11  out:14
    to_summary  CC=11  out:8
    to_toon  CC=8  out:17
    _extract_module_docstring  CC=6  out:11
    _path_to_module  CC=3  out:5
    _relative_path  CC=2  out:3
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
  llx.prellm.model_catalog  [2 funcs]
    list_model_pairs  CC=8  out:4
    list_openrouter_models  CC=8  out:4
  llx.prellm.pipeline.engine  [1 funcs]
    from_yaml  CC=1  out:2
  llx.prellm.pipeline.loader  [2 funcs]
    build_pipeline  CC=2  out:2
    load_pipeline_config  CC=5  out:20
  llx.prellm.pipeline_ops  [1 funcs]
    execute_v3_pipeline  CC=10  out:27
  llx.prellm.server  [6 funcs]
    _build_prellm_meta  CC=3  out:2
    _parse_model_pair  CC=10  out:13
    _stream_response  CC=4  out:15
    batch_process  CC=3  out:8
    chat_completions  CC=12  out:22
    create_app  CC=7  out:1
  llx.prellm.trace  [11 funcs]
    _generate_decision_tree  CC=10  out:22
    _generate_markdown_step_details  CC=8  out:14
    _generate_markdown_summary  CC=3  out:4
    _generate_step_log  CC=4  out:4
    start  CC=1  out:2
    stop  CC=1  out:2
    _safe_json  CC=3  out:4
    _sanitize  CC=13  out:17
    _step_icon  CC=1  out:1
    get_current_trace  CC=1  out:1
  llx.prellm.utils.lazy_imports  [1 funcs]
    lazy_import_global  CC=2  out:3
  llx.privacy.__core  [1 funcs]
    quick_anonymize  CC=1  out:2
  llx.privacy._project_context  [8 funcs]
    _generate_symbol  CC=2  out:4
    _get_mapping_dict  CC=1  out:1
    from_dict  CC=1  out:15
    to_dict  CC=1  out:6
    _dict_to_mappings  CC=2  out:2
    _mapping_dict_for  CC=1  out:1
    _mappings_to_dict  CC=2  out:1
    _symbol_prefix  CC=1  out:1
  llx.privacy.deanonymize_engine  [3 funcs]
    __init__  CC=1  out:1
    deanonymize_file  CC=3  out:4
    deanonymize_text  CC=7  out:15
  llx.privacy.deanonymize_utils  [6 funcs]
    build_reverse_lookup  CC=3  out:1
    find_content_tokens  CC=1  out:2
    find_symbol_tokens  CC=1  out:5
    get_content_mapping  CC=2  out:1
    restore_decorators  CC=1  out:3
    restore_imports  CC=1  out:4
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
  llx.tools._docker  [1 funcs]
    docker_cp  CC=1  out:1
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
    main  CC=6  out:11
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
  llx.utils.aider  [2 funcs]
    _extract_issue_files  CC=9  out:8
    _run_aider_fix  CC=10  out:19
  llx.utils.cli_main  [1 funcs]
    cli_main  CC=3  out:6
  llx.utils.formatting  [2 funcs]
    _format_metrics  CC=2  out:24
    _format_selection  CC=4  out:3
  llx.utils.issues  [2 funcs]
    build_fix_prompt  CC=11  out:11
    load_issue_source  CC=9  out:10
  project.map.toon  [1 funcs]
    create_strategy_command  CC=0  out:0
  scripts.pyqual_auto  [2 funcs]
    main  CC=8  out:43
    run_pyqual  CC=3  out:5
  simple_generate  [1 funcs]
    generate_simple_strategy  CC=4  out:18
  test-local-chat  [11 funcs]
    _check_services  CC=3  out:5
    _print_models  CC=4  out:12
    _print_summary  CC=2  out:9
    _run_chat_tests  CC=4  out:9
    _select_test_models  CC=7  out:4
    get_available_models  CC=4  out:3
    main  CC=4  out:13
    test_chat_completion  CC=4  out:16
    test_llx_health  CC=2  out:1
    test_llx_models  CC=4  out:3
  trace  [1 funcs]
    test  CC=11  out:10

EDGES:
  trace.test → llx.planfile.generate_strategy._normalize_strategy_data
  simple_generate.generate_simple_strategy → llx.planfile.generate_strategy.generate_strategy_with_fix
  simple_generate.generate_simple_strategy → llx.planfile.generate_strategy.save_fixed_strategy
  test-local-chat.test_chat_completion → Taskfile.print
  test-local-chat._check_services → Taskfile.print
  test-local-chat._check_services → test-local-chat.test_llx_health
  test-local-chat._check_services → test-local-chat.test_ollama_health
  test-local-chat._print_models → Taskfile.print
  test-local-chat._print_models → test-local-chat.get_available_models
  test-local-chat._print_models → test-local-chat.test_llx_models
  test-local-chat._run_chat_tests → Taskfile.print
  test-local-chat._run_chat_tests → test-local-chat.test_chat_completion
  test-local-chat._print_summary → Taskfile.print
  test-local-chat.main → Taskfile.print
  test-local-chat.main → test-local-chat._check_services
  test-local-chat.main → test-local-chat._print_models
  test-local-chat.main → test-local-chat._select_test_models
  test-local-chat.main → test-local-chat._run_chat_tests
  test-local-chat.main → test-local-chat._print_summary
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
  examples.privacy.basic.01_text_anonymization.main → llx.privacy.__core.quick_anonymize
  examples.privacy.basic.02_custom_patterns.main → Taskfile.print
  scripts.pyqual_auto.run_pyqual → Taskfile.print
  scripts.pyqual_auto.main → Taskfile.print
  llx.commands._patch_apply._apply_unified_diff → llx.commands._patch_apply._parse_unified_hunks
  llx.commands._patch_apply._apply_unified_diff → llx.commands._patch_apply._find_hunk_position
  llx.commands._patch_apply._parse_unified_hunks → llx.commands._patch_apply._classify_line
  llx.commands._patch_apply._parse_unified_hunks → llx.commands._patch_apply._finalize_hunk
  llx.commands.fix.load_errors_data → llx.utils.issues.load_issue_source
  llx.commands.fix.select_model_for_fix → examples.filtering.filtering.select_model
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 317f 59707L | python:190,yaml:59,shell:32,yml:10,txt:4,json:4,conf:3,toml:1 | 2026-04-26
# CC̄=2.6 | critical:6/1958 | dups:0 | cycles:0

HEALTH[6]:
  🟡 CC    main CC=15 (limit:15)
  🟡 CC    execute_strategy CC=34 (limit:15)
  🟡 CC    _normalize_strategy CC=22 (limit:15)
  🟡 CC    _execute_task CC=26 (limit:15)
  🟡 CC    plan_run CC=42 (limit:15)
  🟡 CC    chat CC=16 (limit:15)

REFACTOR[1]:
  1. split 6 high-CC methods  (CC>15)

PIPELINES[1013]:
  [1] Src [test]: test → _normalize_strategy_data → _normalize_goal
      PURITY: 100% pure
  [2] Src [generate_simple_strategy]: generate_simple_strategy → generate_strategy_with_fix → _print_generation_info
      PURITY: 100% pure
  [3] Src [main]: main → print
      PURITY: 100% pure
  [4] Src [__init__]: __init__
      PURITY: 100% pure
  [5] Src [increment_successful_requests]: increment_successful_requests
      PURITY: 100% pure

LAYERS:
  llx/                            CC̄=3.8    ←in:23  →out:12  !! split
  │ !! tools                      995L  1C   17m  CC=13     ←0
  │ !! executor_simple            833L  2C   15m  CC=34     ←1
  │ !! config_manager             794L  1C   45m  CC=12     ←0
  │ !! vscode_manager             791L  1C   38m  CC=10     ←0
  │ !! model_manager              756L  1C   36m  CC=8      ←0
  │ !! trace                      648L  2C   29m  CC=13     ←2
  │ !! orchestrator               642L  1C   28m  CC=10     ←0
  │ !! engine                     638L  1C   38m  CC=11     ←0
  │ !! app                        598L  0C   21m  CC=42     ←0
  │ !! orchestrator               595L  1C   27m  CC=12     ←0
  │ !! health_checker             589L  1C   27m  CC=10     ←0
  │ !! manager                    556L  1C   18m  CC=12     ←0
  │ !! docker_manager             552L  1C   24m  CC=10     ←0
  │ !! limiter                    525L  1C   20m  CC=14     ←0
  │ !! planfile_config.yaml       508L  0C    0m  CC=0.0    ←0
  │ manager                    495L  1C   21m  CC=9      ←0
  │ pipeline                   483L  5C   18m  CC=9      ←1
  │ collector                  482L  1C   21m  CC=10     ←7
  │ generate_strategy          470L  0C   19m  CC=9      ←2
  │ core                       468L  1C   11m  CC=10     ←5
  │ server                     447L  10C    9m  CC=12     ←2
  │ manager                    445L  1C   20m  CC=14     ←0
  │ models                     432L  33C    2m  CC=1      ←1
  │ deanonymize                424L  4C   16m  CC=8      ←1
  │ codebase_indexer           418L  4C   14m  CC=11     ←0
  │ config                     376L  4C    9m  CC=13     ←9
  │ cli_commands               366L  0C   10m  CC=8      ←0
  │ user_memory                361L  1C   15m  CC=12     ←0
  │ !! client                     347L  3C   12m  CC=16     ←0
  │ proxym                     331L  3C   12m  CC=8      ←1
  │ query_decomposer           330L  1C   10m  CC=9      ←0
  │ formatters                 312L  0C   12m  CC=14     ←2
  │ issues                     300L  0C   11m  CC=11     ←2
  │ _streaming_impl            295L  2C   15m  CC=6      ←0
  │ __core                     291L  3C   13m  CC=8      ←1
  │ selector                   281L  2C    9m  CC=8      ←5
  │ cli                        278L  0C   13m  CC=3      ←0
  │ process_chain              275L  1C   10m  CC=7      ←0
  │ health_runner              266L  1C   10m  CC=10     ←0
  │ model_selector             264L  4C   15m  CC=14     ←0
  │ runner                     263L  0C    5m  CC=12     ←3
  │ sensitive_filter           262L  1C   14m  CC=7      ←0
  │ pipeline_ops               257L  0C    5m  CC=12     ←1
  │ context_engine             248L  1C   13m  CC=13     ←0
  │ service                    243L  1C   14m  CC=4      ←0
  │ ai_tools_manager           241L  1C   17m  CC=5      ←0
  │ utils                      240L  3C   13m  CC=6      ←0
  │ budget                     233L  3C   11m  CC=6      ←2
  │ cli_config                 232L  0C    6m  CC=9      ←0
  │ extractors                 229L  0C   11m  CC=7      ←1
  │ _project_ast               226L  1C   10m  CC=10     ←0
  │ folder_compressor          224L  1C   10m  CC=11     ←0
  │ executors                  223L  0C    6m  CC=5      ←1
  │ _nfo_compat                220L  3C   11m  CC=4      ←1
  │ fix                        218L  0C    9m  CC=8      ←0
  │ validators                 212L  3C    7m  CC=14     ←0
  │ schema_generator           211L  1C    9m  CC=11     ←0
  │ cli                        193L  0C    6m  CC=8      ←0
  │ aider                      192L  0C    3m  CC=10     ←2
  │ preprocessor               188L  2C    6m  CC=13     ←0
  │ cli_query                  186L  0C    5m  CC=9      ←2
  │ _project_context           185L  2C   13m  CC=2      ←3
  │ prompt_registry            185L  5C   11m  CC=6      ←1
  │ cli                        183L  0C   10m  CC=5      ←0
  │ context_ops                181L  0C    8m  CC=5      ←1
  │ llm                        171L  2C    8m  CC=10     ←0
  │ shell_collector            169L  1C    8m  CC=5      ←0
  │ cli_utils                  164L  0C    5m  CC=5      ←2
  │ pipelines.yaml             161L  0C    0m  CC=0.0    ←0
  │ models                     159L  8C    5m  CC=6      ←1
  │ cli                        158L  0C   11m  CC=5      ←0
  │ litellm_config             151L  2C   10m  CC=4      ←1
  │ llm_provider               150L  1C    4m  CC=11     ←0
  │ cli                        149L  0C    9m  CC=10     ←0
  │ cli                        149L  0C    9m  CC=6      ←0
  │ _streaming_chunking        148L  4C    5m  CC=8      ←0
  │ workflows                  146L  1C    3m  CC=8      ←0
  │ config_io                  142L  0C    2m  CC=6      ←0
  │ examples                   141L  0C    5m  CC=2      ←0
  │ server                     141L  0C    8m  CC=2      ←1
  │ _project_anonymizer        138L  2C    8m  CC=10     ←0
  │ _patch_apply               137L  0C    6m  CC=10     ←0
  │ cli                        136L  0C   11m  CC=6      ←0
  │ cli                        134L  0C    6m  CC=6      ←0
  │ proxy                      131L  0C    3m  CC=7      ←2
  │ prellm_config.yaml         130L  0C    0m  CC=0.0    ←0
  │ executor                   128L  2C    3m  CC=8      ←0
  │ bump_version               125L  0C    7m  CC=5      ←0
  │ config.yaml                125L  0C    0m  CC=0.0    ←0
  │ config                     124L  1C    5m  CC=5      ←0
  │ __init__                   121L  0C    1m  CC=1      ←0
  │ cli                        117L  0C    7m  CC=6      ←0
  │ detector                   115L  1C   12m  CC=5      ←0
  │ cli                        114L  0C    7m  CC=7      ←0
  │ _persistence               112L  0C    2m  CC=9      ←0
  │ strategy_commands          110L  0C    5m  CC=6      ←0
  │ project_types.yaml         109L  0C    0m  CC=0.0    ←0
  │ client                     106L  1C    6m  CC=6      ←0
  │ engine                     105L  1C    5m  CC=9      ←0
  │ verify_push_publish        104L  0C    4m  CC=6      ←0
  │ logging_setup              103L  0C    3m  CC=5      ←1
  │ deanonymize_engine         101L  1C    4m  CC=7      ←0
  │ cli_context                101L  0C    2m  CC=9      ←0
  │ models                     101L  6C    0m  CC=0.0    ←0
  │ prompts.yaml                94L  0C    0m  CC=0.0    ←0
  │ __init__                    89L  0C    0m  CC=0.0    ←0
  │ lint                        86L  0C    3m  CC=6      ←0
  │ security_audit              85L  0C    3m  CC=4      ←0
  │ formatting                  85L  0C    2m  CC=4      ←1
  │ devops.yaml                 85L  0C    0m  CC=0.0    ←0
  │ runner                      82L  1C    6m  CC=6      ←3
  │ env_config                  80L  0C    2m  CC=4      ←4
  │ model_catalog               78L  0C    2m  CC=8      ←1
  │ polish_finance.yaml         78L  0C    0m  CC=0.0    ←0
  │ embedded.yaml               78L  0C    0m  CC=0.0    ←0
  │ models                      75L  5C    1m  CC=2      ←0
  │ models                      75L  6C    0m  CC=0.0    ←0
  │ coding.yaml                 75L  0C    0m  CC=0.0    ←0
  │ embedded.yaml               75L  0C    0m  CC=0.0    ←0
  │ devops_k8s.yaml             75L  0C    0m  CC=0.0    ←0
  │ publish                     74L  0C    4m  CC=3      ←0
  │ deanonymize_utils           72L  0C    6m  CC=3      ←1
  │ type_check                  71L  0C    2m  CC=7      ←0
  │ business.yaml               67L  0C    0m  CC=0.0    ←0
  │ detect_secrets              65L  0C    3m  CC=4      ←0
  │ ports                       64L  1C    5m  CC=4      ←0
  │ rules.yaml                  64L  0C    0m  CC=0.0    ←0
  │ loader                      63L  0C    2m  CC=5      ←1
  │ algo_handlers               62L  1C   12m  CC=3      ←0
  │ models                      61L  4C    0m  CC=0.0    ←0
  │ models                      61L  4C    0m  CC=0.0    ←0
  │ __init__                    56L  0C    0m  CC=0.0    ←0
  │ models                      54L  4C    0m  CC=0.0    ←0
  │ _docker                     53L  0C    3m  CC=3      ←1
  │ deploy.yaml                 52L  0C    0m  CC=0.0    ←0
  │ _streaming_parallel         51L  1C    2m  CC=4      ←0
  │ config                      48L  4C    0m  CC=0.0    ←0
  │ response_schemas.yaml       45L  0C    0m  CC=0.0    ←0
  │ project                     44L  0C    0m  CC=0.0    ←0
  │ ports                       43L  1C    4m  CC=4      ←0
  │ streaming                   43L  0C    0m  CC=0.0    ←0
  │ models                      42L  3C    0m  CC=0.0    ←0
  │ _crud                       41L  0C    3m  CC=3      ←0
  │ _cmd_status                 40L  0C    1m  CC=1      ←0
  │ _utils                      37L  0C    2m  CC=3      ←9
  │ health                      36L  0C    2m  CC=5      ←1
  │ __init__                    36L  0C    0m  CC=0.0    ←0
  │ _cmd_remove                 35L  0C    1m  CC=1      ←0
  │ __init__                    35L  0C    0m  CC=0.0    ←0
  │ sensitive_rules.yaml        34L  0C    0m  CC=0.0    ←0
  │ _cmd_uninstall_extension    31L  0C    1m  CC=1      ←0
  │ analyze                     31L  0C    1m  CC=5      ←0
  │ cli_main                    30L  0C    1m  CC=3      ←12
  │ models                      29L  0C    1m  CC=4      ←1
  │ __init__                    26L  0C    0m  CC=0.0    ←0
  │ planner                     25L  0C    1m  CC=9      ←0
  │ __init__                    25L  0C    0m  CC=0.0    ←0
  │ _cmd_cleanup                24L  0C    1m  CC=1      ←0
  │ deanonymize_results         23L  2C    0m  CC=0.0    ←0
  │ defaults                    22L  0C    1m  CC=1      ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ lazy_imports                21L  0C    1m  CC=2      ←1
  │ __init__                    21L  0C    0m  CC=0.0    ←0
  │ lazy_loader                 20L  1C    3m  CC=2      ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    0m  CC=0.0    ←0
  │ __init__                    13L  0C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ __main__                     8L  0C    0m  CC=0.0    ←0
  │ __init__                     7L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ _utils                       6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __main__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=3.1    ←in:0  →out:0
  │ !! 01_api_integration         539L  2C    4m  CC=15     ←0
  │ !! 01_entropy_ml_detection    506L  3C   12m  CC=14     ←0
  │ 04_behavioral_learning     482L  3C   14m  CC=11     ←0
  │ 03_contextual_passwords    462L  2C   10m  CC=12     ←0
  │ 02_multi_stage             436L  2C    5m  CC=6      ←0
  │ 03_cicd_integration        406L  2C    8m  CC=9      ←0
  │ docker.sh                  385L  0C   14m  CC=0.0    ←2
  │ hybrid.sh                  347L  0C    3m  CC=0.0    ←0
  │ filtering.sh               294L  0C    7m  CC=0.0    ←5
  │ generate_simple.sh         276L  0C    6m  CC=0.0    ←0
  │ 02_hybrid_system           231L  2C   13m  CC=12     ←0
  │ run.sh                     195L  0C    4m  CC=0.0    ←0
  │ 01_anonymize_project       177L  0C    2m  CC=4      ←0
  │ strategy_complete.yaml     164L  0C    0m  CC=0.0    ←0
  │ strategy.yaml              138L  0C    0m  CC=0.0    ←0
  │ strategy.yaml              126L  0C    0m  CC=0.0    ←0
  │ 01_streaming_anonymization   125L  0C    2m  CC=5      ←0
  │ 02_deanonymize_project     122L  0C    1m  CC=4      ←0
  │ 02_custom_patterns          86L  0C    1m  CC=3      ←0
  │ docker-compose.yml          82L  0C    0m  CC=0.0    ←0
  │ strategy.yaml               80L  0C    0m  CC=0.0    ←0
  │ 01_text_anonymization       77L  0C    1m  CC=3      ←0
  │ docker-compose.yml          77L  0C    0m  CC=0.0    ←0
  │ strategy_cheaper.yaml       73L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          72L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          70L  0C    0m  CC=0.0    ←0
  │ strategy_desc.yaml          63L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          63L  0C    0m  CC=0.0    ←0
  │ pyqual-llx.yaml             57L  0C    0m  CC=0.0    ←0
  │ setup-aliases.sh            56L  0C    0m  CC=0.0    ←0
  │ pyqual-llx-demo.sh          55L  0C    0m  CC=0.0    ←0
  │ planfile_config.yaml        48L  0C    0m  CC=0.0    ←0
  │ run.sh                      43L  0C    0m  CC=0.0    ←0
  │ run.sh                      42L  0C    0m  CC=0.0    ←0
  │ run.sh                      42L  0C    0m  CC=0.0    ←0
  │ run.sh                      41L  0C    0m  CC=0.0    ←0
  │ run.sh                      32L  0C    0m  CC=0.0    ←0
  │ run.sh                      32L  0C    0m  CC=0.0    ←0
  │ run.sh                      31L  0C    0m  CC=0.0    ←0
  │ run.sh                      31L  0C    0m  CC=0.0    ←0
  │ run.sh                      28L  0C    0m  CC=0.0    ←0
  │ proxy-test.yaml             27L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ run.sh                      27L  0C    0m  CC=0.0    ←0
  │ run.sh                      26L  0C    0m  CC=0.0    ←0
  │ strategy.yaml               25L  0C    0m  CC=0.0    ←0
  │ strategy.yaml               25L  0C    0m  CC=0.0    ←0
  │ strategy-FocusArea.COMPLEXITY-20260326-155016.yaml    22L  0C    0m  CC=0.0    ←0
  │ cleanup.sh                  21L  0C    0m  CC=0.0    ←0
  │ duplication.json            16L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml          16L  0C    0m  CC=0.0    ←0
  │ duplication.json            16L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml          16L  0C    0m  CC=0.0    ←0
  │ strategy.yaml               11L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=2.9    ←in:0  →out:19  !! split
  │ pyqual_auto                257L  0C   10m  CC=8      ←0
  │
  test-api-qwen/                  CC̄=1.8    ←in:0  →out:0
  │ main                       122L  3C    6m  CC=4      ←0
  │ models                      19L  3C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=1.5    ←in:0  →out:0
  │ !! planfile.yaml             1668L  0C    0m  CC=0.0    ←0
  │ Taskfile.yml               498L  0C    1m  CC=0.0    ←56
  │ goal.yaml                  429L  0C    0m  CC=0.0    ←0
  │ docker-manage.sh           406L  0C    7m  CC=0.0    ←0
  │ docker-compose.yml         352L  0C    0m  CC=0.0    ←0
  │ ai-tools-manage.sh         351L  0C   15m  CC=0.0    ←0
  │ docker-compose-prod.yml    261L  0C    0m  CC=0.0    ←0
  │ test-local-chat            195L  0C   11m  CC=7      ←0
  │ docker-compose-dev.yml     156L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             146L  0C    0m  CC=0.0    ←0
  │ test.yaml                  114L  0C    0m  CC=0.0    ←0
  │ strategy.yaml              107L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 96L  0C    0m  CC=0.0    ←0
  │ redsl.yaml                  84L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                82L  0C    0m  CC=0.0    ←0
  │ simple_generate             71L  0C    1m  CC=4      ←0
  │ refactor-strategy.yaml      70L  0C    0m  CC=0.0    ←0
  │ trace                       49L  0C    1m  CC=11     ←0
  │ project.sh                  48L  0C    0m  CC=0.0    ←0
  │ generate.sh                 28L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_report.toon.yaml    25L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_plan.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ requirements.txt            12L  0C    0m  CC=0.0    ←0
  │ requirements-dev.txt         9L  0C    0m  CC=0.0    ←0
  │ github.planfile.yaml         4L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  my-api/                         CC̄=1.5    ←in:0  →out:0
  │ monitoring                 125L  4C   14m  CC=2      ←0
  │ main                       107L  2C   11m  CC=3      ←0
  │ docker-compose.yml          64L  0C    0m  CC=0.0    ←0
  │ models                      42L  5C    0m  CC=0.0    ←0
  │ requirements.txt             6L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │
  docker/                         CC̄=0.0    ←in:0  →out:0
  │ install-extensions.sh      409L  0C    2m  CC=0.0    ←0
  │ install-tools.sh           369L  0C    0m  CC=0.0    ←0
  │ llx.conf                   241L  0C    0m  CC=0.0    ←0
  │ entrypoint.sh              175L  0C    2m  CC=0.0    ←0
  │ settings.json               98L  0C    0m  CC=0.0    ←0
  │ redis.conf                  86L  0C    0m  CC=0.0    ←0
  │ nginx.conf                  81L  0C    0m  CC=0.0    ←0
  │ entrypoint.sh               31L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                7167L  0C    0m  CC=0.0    ←0
  │ !! map.toon.yaml             2304L  0C  546m  CC=0.0    ←9
  │ !! calls.toon.yaml            615L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         417L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml      244L  0C    0m  CC=0.0    ←0
  │ validation.toon.yaml       157L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         54L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           53L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │
  code2llm_output/                CC̄=0.0    ←in:0  →out:0
  │ analysis.toon.yaml         217L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         217L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         217L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         70L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         70L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    32L  0C    0m  CC=0.0    ←0
  │ generated-from-pytests.testql.toon.yaml    22L  0C    0m  CC=0.0    ←0
  │ generated-api-integration.testql.toon.yaml    18L  0C    0m  CC=0.0    ←0
  │
  .taskill/                       CC̄=0.0    ←in:0  →out:0
  │ state.json                  13L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Dockerfile                                0L
     Makefile                                  0L
     examples/basic/my-api/Dockerfile          0L
     examples/python-api/my-api-complete/Dockerfile  0L
     examples/python-api/my-api-final/Dockerfile  0L
     examples/python-api/my-api-restaurant/Dockerfile  0L
     examples/python-api/test-api/Dockerfile   0L
     examples/python-api/test-cli-debug/Dockerfile  0L
     examples/python-api/test-cli-final/Dockerfile  0L
     examples/python-api/test-cli-v2/Dockerfile  0L
     examples/python-api/test-cli/Dockerfile   0L
     examples/python-api/test-project/Dockerfile  0L
     llx/prellm/chains/__init__.py             0L
     my-api/Dockerfile                         0L

COUPLING:
                                Taskfile    examples.privacy           llx.tools   llx.orchestration  llx.pyqual_plugins             llx.cli        llx.planfile     test-local-chat                 llx           llx.utils             llx.mcp         project.map             scripts        llx.analysis        llx.examples
            Taskfile                  ──                ←435                ←405                ←319                 ←76                 ←24                 ←26                 ←39                                                                                                 ←19                                     ←12  hub
    examples.privacy                 435                  ──                                                                                                                                                                                                                                                                      !! fan-out
           llx.tools                 405                                      ──                                                                                                                                           5                                                                                                      !! fan-out
   llx.orchestration                 319                                                          ──                                                                                                                       7                                                                                                      !! fan-out
  llx.pyqual_plugins                  76                                                                              ──                                                                                                                                                                                                          !! fan-out
             llx.cli                  24                                                                                                  ──                   8                                      13                                                           4                                       6                      !! fan-out
        llx.planfile                  26                                                                                                  ←8                  ──                                       2                   1                                       1                                       2                      hub
     test-local-chat                  39                                                                                                                                          ──                                                                                                                                              !! fan-out
                 llx                                                                                                                     ←13                  ←2                                      ──                                      ←5                  12                                                          ←1  hub
           llx.utils                                                          ←5                  ←7                                                          ←1                                                          ──                   1                                                                                  hub
             llx.mcp                                                                                                                                                                                   5                   3                  ──                   2                                       6                      !! fan-out
         project.map                                                                                                                      ←4                  ←1                                     ←12                                      ←2                  ──                                                              hub
             scripts                  19                                                                                                                                                                                                                                              ──                                          !! fan-out
        llx.analysis                                                                                                                      ←6                  ←2                                                                              ←6                                                          ──                      hub
        llx.examples                  12                                                                                                                                                               1                                                                                                                      ──  !! fan-out
  CYCLES: none
  HUB: Taskfile/ (fan-in=1355)
  HUB: examples.filtering/ (fan-in=5)
  HUB: llx.planfile/ (fan-in=11)
  HUB: llx.integrations/ (fan-in=7)
  HUB: llx.routing/ (fan-in=9)
  HUB: llx.analysis/ (fan-in=16)
  HUB: project.map/ (fan-in=22)
  HUB: llx.utils/ (fan-in=24)
  HUB: examples.docker/ (fan-in=7)
  HUB: llx/ (fan-in=23)
  SMELL: llx.mcp/ fan-out=23 → split needed
  SMELL: llx.planfile/ fan-out=32 → split needed
  SMELL: examples.privacy/ fan-out=438 → split needed
  SMELL: llx.cli/ fan-out=67 → split needed
  SMELL: llx.examples/ fan-out=13 → split needed
  SMELL: llx.commands/ fan-out=12 → split needed
  SMELL: test-local-chat/ fan-out=39 → split needed
  SMELL: llx.tools/ fan-out=417 → split needed
  SMELL: llx.pyqual_plugins/ fan-out=76 → split needed
  SMELL: llx.orchestration/ fan-out=326 → split needed
  SMELL: scripts/ fan-out=19 → split needed
  SMELL: llx/ fan-out=12 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 30 groups | 189f 36580L | 2026-04-26

SUMMARY:
  files_scanned: 189
  total_lines:   36580
  dup_groups:    30
  dup_fragments: 70
  saved_lines:   515
  scan_ms:       9408

HOTSPOTS[7] (files with most duplication):
  examples/privacy/advanced/02_multi_stage.py  dup=185L  groups=1  frags=1  (0.5%)
  llx/planfile/executor_simple.py  dup=138L  groups=1  frags=3  (0.4%)
  examples/privacy/ml/01_entropy_ml_detection.py  dup=60L  groups=1  frags=1  (0.2%)
  my-api/main.py  dup=40L  groups=4  frags=8  (0.1%)
  llx/tools/config_manager.py  dup=38L  groups=4  frags=6  (0.1%)
  llx/orchestration/instances/cli.py  dup=30L  groups=3  frags=4  (0.1%)
  llx/tools/health_checker.py  dup=27L  groups=3  frags=5  (0.1%)

DUPLICATES[30] (ranked by impact):
  [209d7601e17179e8] !! STRU  create_business_logic_project  L=185 N=2 saved=185 sim=1.00
      examples/privacy/advanced/02_multi_stage.py:118-302  (create_business_logic_project)
      examples/privacy/ml/01_entropy_ml_detection.py:310-369  (create_complex_project)
  [8c946c7e76c66a74] ! STRU  _run_cursor_edit  L=46 N=3 saved=92 sim=1.00
      llx/planfile/executor_simple.py:157-202  (_run_cursor_edit)
      llx/planfile/executor_simple.py:205-250  (_run_windsurf_edit)
      llx/planfile/executor_simple.py:253-298  (_run_claude_code_edit)
  [d5cce6ecbb1bbe7b]   STRU  _dispatch  L=9 N=3 saved=18 sim=1.00
      llx/tools/config_manager.py:777-785  (_dispatch)
      llx/tools/model_manager.py:742-747  (_dispatch)
      llx/tools/vscode_manager.py:774-782  (_dispatch)
  [53538b7c7e9fbc5c]   STRU  _dispatch  L=15 N=2 saved=15 sim=1.00
      llx/orchestration/queue/cli.py:40-54  (_dispatch)
      llx/orchestration/ratelimit/cli.py:33-47  (_dispatch)
  [88c0613292de7e44]   STRU  main  L=13 N=2 saved=13 sim=1.00
      llx/pyqual_plugins/detect_secrets.py:49-61  (main)
      llx/pyqual_plugins/type_check.py:55-67  (main)
  [8593830f9a7b5964]   EXAC  check_version_on_pypi  L=12 N=2 saved=12 sim=1.00
      llx/pyqual_plugins/bump_version.py:13-24  (check_version_on_pypi)
      llx/pyqual_plugins/publish.py:20-32  (check_version_on_pypi)
  [0bcdd1c90487899c]   STRU  _cmd_health  L=4 N=4 saved=12 sim=1.00
      llx/orchestration/instances/cli.py:132-135  (_cmd_health)
      llx/orchestration/llm/cli.py:140-143  (_cmd_usage)
      llx/orchestration/routing/cli.py:89-92  (_cmd_status)
      llx/orchestration/session/cli.py:96-99  (_cmd_queue)
  [528ed74255f443b6]   STRU  _cmd_list_models  L=3 N=5 saved=12 sim=1.00
      llx/tools/config_manager.py:669-671  (_cmd_list_models)
      llx/tools/config_manager.py:737-739  (_cmd_summary)
      llx/tools/model_manager.py:695-697  (_cmd_summary)
      llx/tools/vscode_manager.py:681-683  (_cmd_status)
      llx/tools/vscode_manager.py:740-742  (_cmd_quick_start)
  [3320986d3ce8fc5d]   STRU  main  L=3 N=5 saved=12 sim=1.00
      llx/tools/config_manager.py:788-790  (main)
      llx/tools/docker_manager.py:546-548  (main)
      llx/tools/health_checker.py:583-585  (main)
      llx/tools/model_manager.py:750-752  (main)
      llx/tools/vscode_manager.py:785-787  (main)
  [02eca6ee695df7e9]   EXAC  _calculate_entropy  L=11 N=2 saved=11 sim=1.00
      examples/privacy/ml/03_contextual_passwords.py:251-261  (_calculate_entropy)
      examples/privacy/ml/04_behavioral_learning.py:238-248  (_calculate_entropy)
  [bdcd613ed1021c54]   EXAC  add_limit  L=11 N=2 saved=11 sim=1.00
      llx/orchestration/ratelimit/_crud.py:19-29  (add_limit)
      llx/orchestration/ratelimit/limiter.py:173-183  (add_limit)
  [6a3aad3970abbd84]   EXAC  _is_port_available  L=10 N=2 saved=10 sim=1.00
      llx/orchestration/instances/ports.py:42-51  (_is_port_available)
      llx/orchestration/vscode/ports.py:34-43  (_is_port_available)
  [2e87b67e7eee9cee]   STRU  _cmd_metrics  L=10 N=2 saved=10 sim=1.00
      llx/orchestration/instances/cli.py:120-129  (_cmd_metrics)
      llx/orchestration/queue/cli.py:126-135  (_cmd_metrics)
  [cce0a7ea7702688d]   STRU  _cmd_save  L=10 N=2 saved=10 sim=1.00
      llx/tools/config_manager.py:623-632  (_cmd_save)
      llx/tools/config_manager.py:674-683  (_cmd_add_model)
  [e26e831161f2f1d2]   EXAC  _config_save_worker  L=8 N=2 saved=8 sim=1.00
      llx/orchestration/llm/orchestrator.py:589-596  (_config_save_worker)
      llx/orchestration/vscode/orchestrator.py:547-553  (_config_save_worker)
  [22b7b8561585d4c4]   STRU  _handle_code2llm_analyze  L=8 N=2 saved=8 sim=1.00
      llx/mcp/tools.py:154-161  (_handle_code2llm_analyze)
      llx/mcp/tools.py:182-189  (_handle_redup_scan)
  [3e682d446ab2381f]   STRU  _cmd_start  L=8 N=2 saved=8 sim=1.00
      llx/orchestration/instances/cli.py:73-80  (_cmd_start)
      llx/orchestration/instances/cli.py:83-90  (_cmd_stop)
  [d324ba0f062bed7b]   STRU  _handle_service_command  L=8 N=2 saved=8 sim=1.00
      llx/tools/health_checker.py:526-533  (_handle_service_command)
      llx/tools/health_checker.py:536-543  (_handle_container_command)
  [b0d59b7862226346]   EXAC  release_port  L=7 N=2 saved=7 sim=1.00
      llx/orchestration/instances/ports.py:34-40  (release_port)
      llx/orchestration/vscode/ports.py:26-32  (release_port)
  [17be19fef21a7240]   EXAC  get_current_version  L=6 N=2 saved=6 sim=1.00
      llx/pyqual_plugins/publish.py:12-17  (get_current_version)
      llx/pyqual_plugins/verify_push_publish.py:15-20  (get_current_version)
  [83026584c525e357]   STRU  _handle_start  L=6 N=2 saved=6 sim=1.00
      llx/tools/cli.py:82-87  (_handle_start)
      llx/tools/cli.py:90-95  (_handle_stop)
  [2a01d29b3678662a]   STRU  update_user  L=6 N=2 saved=6 sim=1.00
      my-api/main.py:56-61  (update_user)
      my-api/main.py:89-94  (update_product)
  [bcde7bc80b917330]   STRU  delete_user  L=6 N=2 saved=6 sim=1.00
      my-api/main.py:64-69  (delete_user)
      my-api/main.py:97-102  (delete_product)
  [38f15ace413e5d70]   STRU  _cmd_cleanup  L=5 N=2 saved=5 sim=1.00
      llx/orchestration/ratelimit/cli.py:124-128  (_cmd_cleanup)
      llx/orchestration/session/cli.py:102-106  (_cmd_cleanup)
  [1d592924ec6ba97c]   STRU  _cmd_pull  L=5 N=2 saved=5 sim=1.00
      llx/tools/model_manager.py:625-629  (_cmd_pull)
      llx/tools/model_manager.py:640-644  (_cmd_test)
  [5eac5bd423a29ef7]   STRU  read_user  L=5 N=2 saved=5 sim=1.00
      my-api/main.py:44-48  (read_user)
      my-api/main.py:77-81  (read_product)
  [224614e51da65d16]   STRU  _get_user_memory_class  L=4 N=2 saved=4 sim=1.00
      llx/prellm/agents/preprocessor.py:32-35  (_get_user_memory_class)
      llx/prellm/agents/preprocessor.py:38-41  (_get_codebase_indexer_class)
  [801efa63310fb318]   STRU  _handle_filesystem_command  L=4 N=2 saved=4 sim=1.00
      llx/tools/health_checker.py:552-555  (_handle_filesystem_command)
      llx/tools/health_checker.py:558-561  (_handle_network_command)
  [a2c18c2549f1e90a]   STRU  _cmd_status  L=3 N=2 saved=3 sim=1.00
      llx/orchestration/llm/cli.py:135-137  (_cmd_status)
      llx/orchestration/routing/cli.py:95-97  (_cmd_metrics)
  [7293ed92dfd16686]   STRU  create_user  L=3 N=2 saved=3 sim=1.00
      my-api/main.py:51-53  (create_user)
      my-api/main.py:84-86  (create_product)

REFACTOR[30] (ranked by priority):
  [1] ◐ extract_module     → examples/privacy/utils/create_business_logic_project.py
      WHY: 2 occurrences of 185-line block across 2 files — saves 185 lines
      FILES: examples/privacy/advanced/02_multi_stage.py, examples/privacy/ml/01_entropy_ml_detection.py
  [2] ○ extract_function   → llx/planfile/utils/_run_cursor_edit.py
      WHY: 3 occurrences of 46-line block across 1 files — saves 92 lines
      FILES: llx/planfile/executor_simple.py
  [3] ○ extract_function   → llx/tools/utils/_dispatch.py
      WHY: 3 occurrences of 9-line block across 3 files — saves 18 lines
      FILES: llx/tools/config_manager.py, llx/tools/model_manager.py, llx/tools/vscode_manager.py
  [4] ○ extract_function   → llx/orchestration/utils/_dispatch.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: llx/orchestration/queue/cli.py, llx/orchestration/ratelimit/cli.py
  [5] ○ extract_function   → llx/pyqual_plugins/utils/main.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: llx/pyqual_plugins/detect_secrets.py, llx/pyqual_plugins/type_check.py
  [6] ○ extract_function   → llx/pyqual_plugins/utils/check_version_on_pypi.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: llx/pyqual_plugins/bump_version.py, llx/pyqual_plugins/publish.py
  [7] ○ extract_function   → llx/orchestration/utils/_cmd_health.py
      WHY: 4 occurrences of 4-line block across 4 files — saves 12 lines
      FILES: llx/orchestration/instances/cli.py, llx/orchestration/llm/cli.py, llx/orchestration/routing/cli.py, llx/orchestration/session/cli.py
  [8] ○ extract_function   → llx/tools/utils/_cmd_list_models.py
      WHY: 5 occurrences of 3-line block across 3 files — saves 12 lines
      FILES: llx/tools/config_manager.py, llx/tools/model_manager.py, llx/tools/vscode_manager.py
  [9] ○ extract_function   → llx/tools/utils/main.py
      WHY: 5 occurrences of 3-line block across 5 files — saves 12 lines
      FILES: llx/tools/config_manager.py, llx/tools/docker_manager.py, llx/tools/health_checker.py, llx/tools/model_manager.py, llx/tools/vscode_manager.py
  [10] ○ extract_function   → examples/privacy/ml/utils/_calculate_entropy.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: examples/privacy/ml/03_contextual_passwords.py, examples/privacy/ml/04_behavioral_learning.py
  [11] ○ extract_class      → llx/orchestration/ratelimit/utils/add_limit.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: llx/orchestration/ratelimit/_crud.py, llx/orchestration/ratelimit/limiter.py
  [12] ○ extract_function   → llx/orchestration/utils/_is_port_available.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: llx/orchestration/instances/ports.py, llx/orchestration/vscode/ports.py
  [13] ○ extract_function   → llx/orchestration/utils/_cmd_metrics.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: llx/orchestration/instances/cli.py, llx/orchestration/queue/cli.py
  [14] ○ extract_function   → llx/tools/utils/_cmd_save.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: llx/tools/config_manager.py
  [15] ○ extract_function   → llx/orchestration/utils/_config_save_worker.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: llx/orchestration/llm/orchestrator.py, llx/orchestration/vscode/orchestrator.py
  [16] ○ extract_function   → llx/mcp/utils/_handle_code2llm_analyze.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: llx/mcp/tools.py
  [17] ○ extract_function   → llx/orchestration/instances/utils/_cmd_start.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: llx/orchestration/instances/cli.py
  [18] ○ extract_function   → llx/tools/utils/_handle_service_command.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: llx/tools/health_checker.py
  [19] ○ extract_function   → llx/orchestration/utils/release_port.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: llx/orchestration/instances/ports.py, llx/orchestration/vscode/ports.py
  [20] ○ extract_function   → llx/pyqual_plugins/utils/get_current_version.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: llx/pyqual_plugins/publish.py, llx/pyqual_plugins/verify_push_publish.py
  [21] ○ extract_function   → llx/tools/utils/_handle_start.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: llx/tools/cli.py
  [22] ○ extract_function   → my-api/utils/update_user.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: my-api/main.py
  [23] ○ extract_function   → my-api/utils/delete_user.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: my-api/main.py
  [24] ○ extract_function   → llx/orchestration/utils/_cmd_cleanup.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: llx/orchestration/ratelimit/cli.py, llx/orchestration/session/cli.py
  [25] ○ extract_function   → llx/tools/utils/_cmd_pull.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: llx/tools/model_manager.py
  [26] ○ extract_function   → my-api/utils/read_user.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: my-api/main.py
  [27] ○ extract_function   → llx/prellm/agents/utils/_get_user_memory_class.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: llx/prellm/agents/preprocessor.py
  [28] ○ extract_function   → llx/tools/utils/_handle_filesystem_command.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: llx/tools/health_checker.py
  [29] ○ extract_function   → llx/orchestration/utils/_cmd_status.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: llx/orchestration/llm/cli.py, llx/orchestration/routing/cli.py
  [30] ○ extract_function   → my-api/utils/create_user.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: my-api/main.py

QUICK_WINS[22] (low risk, high savings — do first):
  [2] extract_function   saved=92L  → llx/planfile/utils/_run_cursor_edit.py
      FILES: executor_simple.py
  [3] extract_function   saved=18L  → llx/tools/utils/_dispatch.py
      FILES: config_manager.py, model_manager.py, vscode_manager.py
  [4] extract_function   saved=15L  → llx/orchestration/utils/_dispatch.py
      FILES: cli.py, cli.py
  [5] extract_function   saved=13L  → llx/pyqual_plugins/utils/main.py
      FILES: detect_secrets.py, type_check.py
  [6] extract_function   saved=12L  → llx/pyqual_plugins/utils/check_version_on_pypi.py
      FILES: bump_version.py, publish.py
  [7] extract_function   saved=12L  → llx/orchestration/utils/_cmd_health.py
      FILES: cli.py, cli.py, cli.py +1
  [8] extract_function   saved=12L  → llx/tools/utils/_cmd_list_models.py
      FILES: config_manager.py, model_manager.py, vscode_manager.py
  [9] extract_function   saved=12L  → llx/tools/utils/main.py
      FILES: config_manager.py, docker_manager.py, health_checker.py +2
  [10] extract_function   saved=11L  → examples/privacy/ml/utils/_calculate_entropy.py
      FILES: 03_contextual_passwords.py, 04_behavioral_learning.py
  [11] extract_class      saved=11L  → llx/orchestration/ratelimit/utils/add_limit.py
      FILES: _crud.py, limiter.py

EFFORT_ESTIMATE (total ≈ 21.8h):
  hard   create_business_logic_project       saved=185L  ~555min
  hard   _run_cursor_edit                    saved=92L  ~276min
  medium _dispatch                           saved=18L  ~36min
  medium _dispatch                           saved=15L  ~30min
  easy   main                                saved=13L  ~26min
  easy   check_version_on_pypi               saved=12L  ~24min
  easy   _cmd_health                         saved=12L  ~24min
  easy   _cmd_list_models                    saved=12L  ~24min
  easy   main                                saved=12L  ~24min
  easy   _calculate_entropy                  saved=11L  ~22min
  ... +20 more (~266min)

METRICS-TARGET:
  dup_groups:  30 → 0
  saved_lines: 515 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 1828 func | 140f | 2026-04-26

NEXT[8] (ranked by impact):
  [1] !! SPLIT           llx/planfile/executor_simple.py
      WHY: 878L, 2 classes, max CC=34
      EFFORT: ~4h  IMPACT: 29852

  [2] !! SPLIT           llx/mcp/tools.py
      WHY: 995L, 1 classes, max CC=13
      EFFORT: ~4h  IMPACT: 12935

  [3] !! SPLIT           llx/tools/config_manager.py
      WHY: 794L, 1 classes, max CC=12
      EFFORT: ~4h  IMPACT: 9528

  [4] !! SPLIT-FUNC      plan_run  CC=42  fan=22
      WHY: CC=42 exceeds 15
      EFFORT: ~1h  IMPACT: 924

  [5] !! SPLIT-FUNC      execute_strategy  CC=34  fan=24
      WHY: CC=34 exceeds 15
      EFFORT: ~1h  IMPACT: 816

  [6] !! SPLIT-FUNC      _execute_task  CC=26  fan=20
      WHY: CC=26 exceeds 15
      EFFORT: ~1h  IMPACT: 520

  [7] !  SPLIT-FUNC      LlxClient.chat  CC=16  fan=15
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 240

  [8] !  SPLIT-FUNC      _normalize_strategy  CC=22  fan=9
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 198


RISKS[3]:
  ⚠ Splitting llx/mcp/tools.py may break 17 import paths
  ⚠ Splitting llx/planfile/executor_simple.py may break 15 import paths
  ⚠ Splitting llx/tools/config_manager.py may break 45 import paths

METRICS-TARGET:
  CC̄:          2.6 → ≤1.8
  max-CC:      42 → ≤20
  god-modules: 14 → 0
  high-CC(≥15): 5 → ≤2
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=2.5 → now CC̄=2.6
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 424f | 272✓ 14⚠ 23✗ | 2026-04-09

SUMMARY:
  scanned: 424  passed: 272 (64.2%)  warnings: 14  errors: 23  unsupported: 129

WARNINGS[14]{path,score}:
  llx/commands/fix.py,0.87
    issues[8]{rule,severity,message,line}:
      complexity.cyclomatic,warning,fix has cyclomatic complexity 25 (max: 15),39
      complexity.cyclomatic,warning,_apply_markdown_code_block_strategy has cyclomatic complexity 22 (max: 15),238
      complexity.cyclomatic,warning,_apply_openai_patch has cyclomatic complexity 21 (max: 15),286
      complexity.maintainability,warning,Low maintainability index: 16.9 (threshold: 20),
      complexity.lizard_cc,warning,fix: CC=25 exceeds limit 15,39
      complexity.lizard_length,warning,fix: 105 lines exceeds limit 100,39
      complexity.lizard_cc,warning,_apply_markdown_code_block_strategy: CC=22 exceeds limit 15,238
      complexity.lizard_cc,warning,_apply_openai_patch: CC=21 exceeds limit 15,286
  examples/privacy/advanced/01_api_integration.py,0.97
    issues[1]{rule,severity,message,line}:
      complexity.lizard_length,warning,create_realistic_project: 289 lines exceeds limit 100,73
  examples/privacy/advanced/02_multi_stage.py,0.97
    issues[1]{rule,severity,message,line}:
      complexity.lizard_length,warning,create_business_logic_project: 179 lines exceeds limit 100,118
  examples/privacy/ml/04_behavioral_learning.py,0.97
    issues[1]{rule,severity,message,line}:
      complexity.lizard_length,warning,main: 110 lines exceeds limit 100,326
  llx/commands/_patch_apply.py,0.97
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_parse_unified_hunks has cyclomatic complexity 16 (max: 15),58
      complexity.lizard_cc,warning,_parse_unified_hunks: CC=16 exceeds limit 15,58
  llx/planfile/builder.py,0.97
    issues[1]{rule,severity,message,line}:
      complexity.lizard_length,warning,ask_llm_questions: 119 lines exceeds limit 100,64
  llx/utils/issues.py,0.97
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_collect_file_context has cyclomatic complexity 20 (max: 15),216
      complexity.lizard_cc,warning,_collect_file_context: CC=20 exceeds limit 15,216
  test-local-chat.py,0.97
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,main has cyclomatic complexity 19 (max: 15),101
      complexity.lizard_cc,warning,main: CC=17 exceeds limit 15,101
  llx/orchestration/instances/manager.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.maintainability,warning,Low maintainability index: 16.5 (threshold: 20),
  llx/orchestration/ratelimit/limiter.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.maintainability,warning,Low maintainability index: 17.6 (threshold: 20),
  llx/orchestration/routing/engine.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.maintainability,warning,Low maintainability index: 10.7 (threshold: 20),
  llx/orchestration/vscode/orchestrator.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.maintainability,warning,Low maintainability index: 17.2 (threshold: 20),
  llx/prellm/trace.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.maintainability,warning,Low maintainability index: 18.3 (threshold: 20),
  llx/tools/model_manager.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.maintainability,warning,Low maintainability index: 16.2 (threshold: 20),

ERRORS[23]{path,score}:
  docker/postgres/init.sql,0.00
    issues[1]{rule,severity,message,line}:
      syntax.tree_sitter,error,tree-sitter found 7 parse error(s) in sql,
  test-api-qwen/test_api.py,0.57
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,1
      python.import.resolvable,error,Module 'fastapi.testclient' not found,2
      python.import.resolvable,error,Module 'main' not found,3
  my-api/test_api.py,0.74
    issues[9]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,2
      python.import.resolvable,error,Module 'fastapi.testclient' not found,3
      python.import.resolvable,error,Module 'main' not found,4
      python.import.resolvable,error,Module 'pytest' not found,11
      python.import.resolvable,error,Module 'pytest' not found,46
      python.import.resolvable,error,Module 'pytest' not found,56
      python.import.resolvable,error,Module 'pytest' not found,67
      python.import.resolvable,error,Module 'pytest' not found,78
      python.import.resolvable,error,Module 'pytest' not found,90
  my-api/monitoring.py,0.76
    issues[4]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'prometheus_client' not found,6
      python.import.resolvable,error,Module 'prometheus_client' not found,7
      python.import.resolvable,error,Module 'flask' not found,10
      python.import.resolvable,error,Module 'flask_healthcheck' not found,11
  my-api/main.py,0.79
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'fastapi' not found,5
      python.import.resolvable,error,Module 'uvicorn' not found,106
  tests/privacy/test_anonymizer.py,0.79
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,1
  tests/test_privacy.py,0.79
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,3
  test-api-qwen/main.py,0.83
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'fastapi' not found,1
      python.import.resolvable,error,Module 'uvicorn' not found,4
  tests/privacy/test_context.py,0.86
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,1
  tests/privacy/test_deanonymizer.py,0.86
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,1
  llx/mcp/server.py,0.87
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'mcp.server' not found,26
      python.import.resolvable,error,Module 'mcp.types' not found,27
      python.import.resolvable,error,Module 'mcp.server.stdio' not found,51
  llx/prellm/server.py,0.90
    issues[4]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'fastapi' not found,22
      python.import.resolvable,error,Module 'fastapi.middleware.cors' not found,23
      python.import.resolvable,error,Module 'fastapi.responses' not found,24
      python.import.resolvable,error,Module 'starlette.middleware.base' not found,26
  tests/test_aider_mcp.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,3
  tests/test_core.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,9
  tests/test_detection.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,3
  llx/config.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'tomli' not found,29
  llx/tools/config_manager.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'toml' not found,8
  tests/test_mcp.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,5
  tests/test_privacy_extended.py,0.97
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,14
  llx/prellm/cli_commands.py,0.98
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'uvicorn' not found,145
  tests/test_prellm_integration.py,0.98
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,7
  tests/test_proxym_integration.py,0.98
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,7
  llx/mcp/tools.py,0.99
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'mcp.types' not found,11

UNSUPPORTED[6]{bucket,count}:
  *.md,71
  Dockerfile*,13
  *.txt,18
  *.yml,9
  *.example,1
  other,17
```

## Intent

Intelligent LLM model router driven by real code metrics — successor to preLLM
