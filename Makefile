# Makefile for llx
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev install-full install-ci dev prod test clean docker docker-dev docker-prod

# Default target
help:
	@echo "🚀 llx Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  install          Install llx in development mode (with uv if available)"
	@echo "  install-dev      Fast dev install - test + lint only (< 60s)"
	@echo "  install-full     Full dev install with CI tools and MCP (< 2 min)"
	@echo "  install-ci       CI install with all dependencies"
	@echo "  install-tools    Install local development tools (Ollama, Redis)"
	@echo ""
	@echo "Development:"
	@echo "  dev              Start development Docker stack"
	@echo "  prod             Start production Docker stack"
	@echo "  test             Run tests"
	@echo "  lint             Run linting"
	@echo "  format           Format code"
	@echo ""
	@echo "Docker:"
	@echo "  docker-dev       Start development containers"
	@echo "  docker-prod      Start production containers"
	@echo "  docker-stop      Stop all containers"
	@echo "  docker-clean     Clean Docker resources"
	@echo "  docker-logs      Show logs"
	@echo ""
	@echo "Examples:"
	@echo "  examples-basic   Run basic example"
	@echo "  examples-docker  Run Docker example"
	@echo "  examples-proxy   Run proxy example"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean temporary files"
	@echo "  backup           Create backups"
	@echo "  doctor           Check system health"
	@echo ""
	@echo "Release:"
	@echo "  publish          Build package for PyPI (dry-run)"
	@echo "  publish-confirm  Upload to PyPI"
	@echo "  publish-test     Upload to TestPyPI"

# Installation (with uv for speed)
install:
	@echo "📦 Installing llx with uv..."
	@if command -v uv > /dev/null 2>&1; then \
		uv venv; \
		uv pip install -e ".[dev]"; \
	else \
		python -m venv .venv; \
		.venv/bin/pip install --upgrade pip; \
		.venv/bin/pip install -e ".[dev]"; \
	fi
	@echo "✅ Installation completed!"
	@echo "Run 'source .venv/bin/activate' to activate the virtual environment"

install-dev:
	@echo "📦 Fast dev install (< 60s)..."
	@uv venv 2>/dev/null || python -m venv .venv
	@uv pip install -e ".[dev]" 2>/dev/null || .venv/bin/pip install -e ".[dev]"
	@echo "✅ Dev installation completed!"

install-full:
	@echo "📦 Full dev install with CI tools (< 2 min)..."
	@uv venv 2>/dev/null || python -m venv .venv
	@uv pip install -e ".[dev-full]" 2>/dev/null || .venv/bin/pip install -e ".[dev-full]"
	@echo "✅ Full installation completed!"

install-ci:
	@echo "📦 CI install with all tools..."
	@uv pip install -e ".[all]" 2>/dev/null || .venv/bin/pip install -e ".[all]"
	@echo "✅ CI installation completed!"

install-tools:
	@echo "🔧 Installing local tools..."
	@if command -v ollama > /dev/null 2>&1; then \
		echo "✅ Ollama already installed"; \
	else \
		echo "📦 Installing Ollama..."; \
		curl -fsSL https://ollama.ai/install.sh | sh; \
	fi
	@if command -v redis-cli > /dev/null 2>&1; then \
		echo "✅ Redis CLI already installed"; \
	else \
		echo "📦 Installing Redis CLI..."; \
		if command -v apt-get > /dev/null 2>&1; then \
			sudo apt-get update && sudo apt-get install -y redis-tools; \
		elif command -v brew > /dev/null 2>&1; then \
			brew install redis; \
		else \
			echo "Please install Redis CLI manually"; \
		fi; \
	fi
	@echo "✅ Tools installation completed!"

# Development environments
dev:
	@echo "🚀 Starting development environment..."
	./docker-manage.sh dev

prod:
	@echo "🚀 Starting production environment..."
	./docker-manage.sh prod

# Testing
test:
	@echo "🧪 Running tests..."
	.venv/bin/python -m pytest tests/ -v --tb=short

test-docker:
	@echo "🐳 Running tests in Docker..."
	docker build -t llx-test .
	docker run --rm llx-test .venv/bin/python -m pytest tests/ -v

lint:
	@echo "🔍 Running linting with ruff..."
	.venv/bin/python -m ruff check llx/
	.venv/bin/python -m ruff check tests/
	.venv/bin/python -m mypy llx/ --ignore-missing-imports

format:
	@echo "📝 Formatting code with ruff..."
	.venv/bin/python -m ruff format llx/
	.venv/bin/python -m ruff format tests/

# Docker commands
docker-dev:
	@echo "🐳 Starting development containers..."
	./docker-manage.sh dev

docker-prod:
	@echo "🐳 Starting production containers..."
	./docker-manage.sh prod

docker-stop:
	@echo "🛑 Stopping all containers..."
	./docker-manage.sh stop

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	./docker-manage.sh clean

docker-logs:
	@echo "📋 Showing logs..."
	./docker-manage.sh logs dev

docker-status:
	@echo "📊 Container status..."
	./docker-manage.sh status

# Examples
examples-basic:
	@echo "📚 Running basic example..."
	cd examples/basic && ./run.sh

examples-proxy:
	@echo "📚 Running proxy example..."
	cd examples/proxy && timeout 10s ./run.sh || echo "Proxy example completed (timeout expected)"

examples-docker:
	@echo "📚 Running Docker example..."
	cd examples/docker && ./run.sh

examples-multi:
	@echo "📚 Running multi-provider example..."
	cd examples/multi-provider && ./run.sh

examples-local:
	@echo "📚 Running local models example..."
	cd examples/local && ./run.sh

examples-all:
	@echo "📚 Running all examples..."
	$(MAKE) examples-basic
	$(MAKE) examples-multi
	$(MAKE) examples-local
	$(MAKE) examples-docker

# Utilities
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/
	@echo "✅ Clean completed!"

doctor:
	@echo "🔍 System health check..."
	@echo ""
	@echo "Python:"
	@python --version || echo "❌ Python not found"
	@echo ""
	@echo "Docker:"
	@docker --version || echo "❌ Docker not found"
	@docker info > /dev/null 2>&1 && echo "✅ Docker daemon running" || echo "❌ Docker daemon not running"
	@echo ""
	@echo "Local Tools:"
	@command -v ollama > /dev/null 2>&1 && echo "✅ Ollama installed" || echo "❌ Ollama not installed"
	@ollama list > /dev/null 2>&1 && echo "✅ Ollama running" || echo "❌ Ollama not running"
	@command -v redis-cli > /dev/null 2>&1 && echo "✅ Redis CLI installed" || echo "❌ Redis CLI not installed"
	@echo ""
	@echo "Virtual Environment:"
	@test -d .venv && echo "✅ .venv exists" || echo "❌ .venv not found"
	@test -f .venv/bin/python && echo "✅ Python in .venv" || echo "❌ Python not in .venv"
	@echo ""
	@echo "Configuration Files:"
	@test -f .env && echo "✅ .env exists" || echo "❌ .env not found"
	@test -f llx.yaml && echo "✅ llx.yaml exists" || echo "❌ llx.yaml not found"
	@test -f litellm-config.yaml && echo "✅ litellm-config.yaml exists" || echo "❌ litellm-config.yaml not found"
	@test -f docker-compose.yml && echo "✅ docker-compose.yml exists" || echo "❌ docker-compose.yml not found"
	@echo ""
	@echo "API Keys:"
	@grep -q "ANTHROPIC_API_KEY=" .env && echo "✅ ANTHROPIC_API_KEY configured" || echo "❌ ANTHROPIC_API_KEY not configured"
	@grep -q "OPENROUTER_API_KEY=" .env && echo "✅ OPENROUTER_API_KEY configured" || echo "❌ OPENROUTER_API_KEY not configured"
	@echo ""
	@echo "Docker Services:"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "llx-|llx_" || echo "❌ No llx containers running"
	@echo ""
	@echo "Local Ollama Models:"
	@ollama list 2>/dev/null | head -5 || echo "❌ No local models"

backup:
	@echo "💾 Creating backups..."
	./docker-manage.sh backup
	@echo "✅ Backup completed!"

# Development shortcuts
quick-test:
	@echo "⚡ Quick test..."
	.venv/bin/python -c "from llx import analyze_project, select_model; print('✅ llx imports working')"

quick-start:
	@echo "⚡ Quick start..."
	$(MAKE) install
	$(MAKE) install-tools
	$(MAKE) docker-dev
	@echo "✅ Quick start completed!"
	@echo "Services: http://localhost:4000 (API), http://localhost:3000 (WebUI)"

# CI/CD helpers
ci-install:
	@echo "🔧 CI installation..."
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e .
	.venv/bin/pip install -r requirements-dev.txt

ci-test:
	@echo "🧪 CI testing..."
	.venv/bin/python -m pytest tests/ -v --cov=llx --cov-report=xml --cov-report=html

ci-lint:
	@echo "🔍 CI linting with ruff..."
	.venv/bin/python -m ruff check llx/ --format=github
	.venv/bin/python -m mypy llx/ --ignore-missing-imports --junit-xml test-results.xml

ci-build:
	@echo "🐳 CI build..."
	docker build -t llx:${BUILD_NUMBER:-latest} .
	docker tag llx:${BUILD_NUMBER:-latest} llx:latest

# Release helpers
publish:
	@echo "📦 Publishing to PyPI..."
	@command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)
	rm -rf dist/ build/ *.egg-info/
	.venv/bin/python -m build
	.venv/bin/twine check dist/*
	@echo "⚡ Ready to upload. Run: make publish-confirm to upload to PyPI"

publish-confirm:
	@echo "🚀 Uploading to PyPI..."
	.venv/bin/twine upload dist/*

publish-test:
	@echo "📦 Publishing to TestPyPI..."
	@command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)
	rm -rf dist/ build/ *.egg-info/
	.venv/bin/python -m build
	.venv/bin/twine upload --repository testpypi dist/*

version:
	@echo "📦 Version information..."
	.venv/bin/python -c "import llx; print(f'llx version: {llx.__version__}')"

tag:
	@echo "🏷️  Creating git tag..."
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make tag VERSION=v1.0.0"; \
		exit 1; \
	fi
	git tag $(VERSION)
	git push origin $(VERSION)

# Documentation
docs:
	@echo "📚 Building documentation..."
	.venv/bin/python -m mkdocs build

docs-serve:
	@echo "📚 Serving documentation..."
	.venv/bin/python -m mkdocs serve

# Performance profiling
profile:
	@echo "📊 Running performance profile..."
	.venv/bin/python -m cProfile -o profile.stats -m llx analyze .
	.venv/bin/python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Security scanning
security:
	@echo "🔒 Running security scan..."
	.venv/bin/pip install safety bandit
	.venv/bin/safety check
	.venv/bin/bandit -r llx/

# Database operations
db-reset:
	@echo "🗄️  Resetting database..."
	docker exec llx-postgres-prod psql -U llx -d llx -c "DROP SCHEMA IF EXISTS llx CASCADE; CREATE SCHEMA llx;"
	docker exec llx-postgres-prod psql -U llx -d llx -f /docker-entrypoint-initdb.d/init.sql

db-migrate:
	@echo "🗄️  Running database migrations..."
	# Add migration commands here

# Environment management
env-dev:
	@echo "🔧 Setting up development environment..."
	cp .env.example .env.dev
	@echo "✅ Created .env.dev - please edit with your values"

env-prod:
	@echo "🔧 Setting up production environment..."
	cp .env.example .env.prod
	@echo "✅ Created .env.prod - please edit with production values"

# Quick commands for common tasks
up: dev
down: docker-stop
logs: docker-logs
ps: docker-status
