# LLX + Pyqual Integration

This guide shows how to use **llx** for intelligent code generation within **pyqual** quality pipelines.

## Overview

Pyqual provides a quality gate system that runs tools in loops until metrics pass. LLX enhances this by:
- Analyzing project metrics (files, lines, complexity, duplication)
- Selecting the optimal LLM model based on actual code metrics
- Generating targeted fixes using the selected model

# Install llx with preLLM integration
pip install llx[prellm]

# Install pyqual
pip install pyqual
```

### 2. Configure pyqual to use llx

Create or update `pyqual.yaml` in your project:

```yaml
pipeline:
  name: quality-loop-with-llx
  
  metrics:
    cc_max: 15
    vallm_pass_min: 90
    coverage_min: 80
  
  stages:
    - name: analyze
      run: code2llm ./ -f toon,evolution
    
    - name: validate
      run: vallm batch ./ --recursive --errors-json > .pyqual/errors.json
    
    # LLX-powered code generation
    - name: fix
      run: llx fix . --errors .pyqual/errors.json --verbose
      when: metrics_fail
    
    - name: test
      run: pytest --cov --cov-report=json:.pyqual/coverage.json
      when: always
  
  loop:
    max_iterations: 3
    on_fail: report
```

### 3. Run the pipeline

```bash
pyqual run
```

## How LLX Selects Models

LLX uses code metrics to select the most cost-effective model:

| Metric | Premium | Balanced | Cheap | Free |
|--------|---------|----------|-------|------|
| Files | ≥50 | ≥10 | ≥3 | <3 |
| Lines | ≥20K | ≥5K | ≥500 | <500 |
| Avg CC | ≥6.0 | ≥4.0 | ≥2.0 | <2.0 |
| Max CC | ≥25 | ≥15 | — | — |
| Dup Groups | ≥15 | ≥5 | — | — |

**Example selections:**
- Small script (1 file, 100 lines): **free** (Gemini 2.5 Pro)
- Medium CLI (10 files, 2K lines): **cheap** (Claude Haiku 4.5)
- Large project (100 files, 20K lines, high CC): **premium** (Claude Opus 4)

## LLX Fix Command

The `llx fix` command integrates with pyqual's error reports:

```bash
llx fix [workdir] [options]
```

### Options

- `--errors, -e`: Path to errors JSON file (from vallm, bandit, etc.)
- `--apply`: Apply fixes automatically (experimental)
- `--model, -m`: Force specific model instead of auto-selection
- `--dry-run`: Show what would be done without executing
- `--verbose, -v`: Detailed output

# Fix using auto-selected model
llx fix . --errors .pyqual/errors.json

# Force a specific model
llx fix . --errors .pyqual/errors.json --model claude-sonnet-4-20250514

# Dry run to see what would be done
llx fix . --errors .pyqual/errors.json --dry-run --verbose
```

### Custom Model Thresholds

Create `llx.toml` to adjust selection thresholds:

```toml
[thresholds]
files_premium = 100      # Require more files for premium tier
files_balanced = 20
lines_premium = 50000    # Require more lines for premium
avg_cc_premium = 8.0     # Higher complexity threshold
```

### Environment Variables

```bash
export LLX_DEFAULT_TIER=balanced  # Default when metrics are unclear
export LLX_VERBOSE=true           # Detailed logging
export LLM_MODEL=custom-model     # Override model selection
```

### Pattern 1: Basic Quality Loop

```yaml
stages:
  - name: analyze
    run: code2llm ./ -f toon
  - name: validate
    run: vallm batch ./ --errors-json > .pyqual/errors.json
  - name: fix
    run: llx fix . --errors .pyqual/errors.json
    when: metrics_fail
```

### Pattern 2: Security-Focused

```yaml
stages:
  - name: security-scan
    run: |
      bandit -r . -f json -o .pyqual/bandit.json || true
      trufflehog filesystem . --json > .pyqual/secrets.json 2>/dev/null || true
  - name: fix-security
    run: llx fix . --errors .pyqual/bandit.json --model claude-opus-4
    when: metrics_fail
```

### Pattern 3: Multi-Stage Refactoring

```yaml
stages:
  - name: analyze-complexity
    run: code2llm ./ -f toon,evolution
  - name: reduce-complexity
    run: llx fix . --model claude-sonnet-4 --prompt "Reduce cyclomatic complexity"
    when: metrics_fail
  - name: validate-refactor
    run: vallm batch ./ --errors-json > .pyqual/errors.json
  - name: final-fixes
    run: llx fix . --errors .pyqual/errors.json
    when: metrics_fail
```

### When LLX Cannot Fix

If LLX cannot resolve issues after the maximum iterations:

1. **Report mode** (default): Summary is displayed
2. **Create ticket**: Generate issue with details
3. **Block mode**: Stop pipeline with error

```yaml
loop:
  max_iterations: 3
  on_fail: create_ticket  # Generate GitHub/GitLab issue
```

### Manual Intervention

The fix command outputs structured suggestions that can be applied manually:

```bash
# Run with dry-run to get suggestions
llx fix . --errors .pyqual/errors.json --dry-run > fixes.md

## Best Practices

1. **Start with dry-run**: Always review fixes before applying
2. **Use version control**: Commit before running auto-fix
3. **Adjust thresholds**: Tune model selection for your project
4. **Monitor costs**: Check LLX model selection decisions
5. **Iterate gradually**: Fix high-impact issues first

### Common Issues

1. **"preLLM not available"**
   ```bash
   pip install llx[prellm]
   ```

2. **Model selection too aggressive**
   - Adjust thresholds in `llx.toml`
   - Set `LLX_DEFAULT_TIER=cheap`

3. **Fixes not applied**
   - Use `--dry-run` to preview
   - Check error JSON format
   - Verify working directory

# Enable verbose logging
export LLX_VERBOSE=true

# Trace model selection
llx analyze . --verbose

# Check what llx would do
llx fix . --errors .pyqual/errors.json --dry-run --verbose
```

## Example Project

See `examples/pyqual-llx.yaml` for a complete configuration that demonstrates:
- Quality gates with multiple metrics
- LLX integration for code generation
- Security scanning stages
- Proper error handling

## Next Steps

1. Try the basic integration with your project
2. Adjust model thresholds based on your needs
3. Add custom stages for specific quality requirements
4. Monitor and iterate on the pipeline effectiveness
