# Contributing to LLX

Thank you for your interest in contributing to LLX! This document provides guidelines and best practices for contributors.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Security Guidelines](#security-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [GitHub Push Protection](#github-push-protection)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/llx.git`
3. Set up the development environment (see below)
4. Create a feature branch: `git checkout -b feature/your-feature-name`

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,prellm-full]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### ⚠️ Critical: Avoiding GitHub Push Protection Blocks

When adding examples or test data that contain "fake secrets" (API keys, tokens, passwords), follow these rules to prevent GitHub from blocking your push:

# ❌ BAD - Looks like a real secret
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"

# ✅ GOOD - Clearly marked as placeholder
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
STRIPE_KEY = "<YOUR_STRIPE_LIVE_KEY_HERE>"
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"  # GitHub allows this pattern
```

# ✅ Add comment to clarify it's an example
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"  # This is a dummy key for documentation
```

#### 3. Use Safe Patterns for Common Secrets

| Secret Type | ❌ Bad Pattern | ✅ Safe Pattern |
|-------------|---------------|-----------------|
| Stripe | `sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL[a-zA-Z0-9]{24,}` | `sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL*` or `<...>` |
| GitHub Token | `ghp_[a-zA-Z0-9]{36}` | `ghp_EXAMPLE_TOKEN` |
| AWS Access Key | `AKIA[0-9A-Z]{16}` | `AKIAEXAMPLE12345678` |
| Generic API Key | `[a-zA-Z0-9]{32,64}` | `EXAMPLE_API_KEY_*` |

#### 4. Pre-Push Verification

Before pushing, run:

```bash
# Check for suspicious patterns
grep -rE "(sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL|ghp_|AKIA[0-9A-Z]{16})" examples/ tests/ docs/ \
  --include="*.py" --include="*.md" --include="*.yaml"

# If you have git-secrets installed
git secrets --scan
```

### Additional Security Best Practices

- Never commit real `.env` files
- Use `OPENROUTER_API_KEY: dummy-key-for-ci` in CI configs
- Store real secrets in environment variables only
- Use `~/.pypirc` for PyPI credentials (never commit them)

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

Run before committing:

```bash
ruff check . --fix
ruff format .
mypy llx/
```

## Testing

All contributions should include tests:

```bash
# Run with coverage
pytest --cov=llx --cov-report=html

# Run specific test file
pytest tests/test_privacy.py -v
```

## GitHub Push Protection

If GitHub blocks your push with "Push Protection" error:

1. **Identify the problem**:
   ```bash
   git push origin main 2>&1 | grep -A10 "secret"
   ```

2. **Fix the files** (see docs/GITHUB_PUSH_PROTECTION.md for detailed steps)

3. **Amend the commit**:
   ```bash
   git add -A
   git commit --amend --no-edit
   git push origin main
   ```

4. **If still blocked**, see [docs/GITHUB_PUSH_PROTECTION.md](docs/GITHUB_PUSH_PROTECTION.md)

## Submitting Changes

1. Ensure all tests pass: `pytest`
2. Run `pyqual run` locally to verify the full pipeline
3. Update documentation if needed
4. Create a Pull Request with clear description

## Questions?

- Open an issue for bugs or feature requests
- See [docs/GITHUB_PUSH_PROTECTION.md](docs/GITHUB_PUSH_PROTECTION.md) for push protection help
- Check existing examples in `examples/` for patterns

Thank you for contributing!
