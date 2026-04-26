# LLX TestQL Integration

This guide documents how **llx** bridges **TestQL** DSL validation with **planfile** ticket generation, upsert, and multi-backend synchronization.

## Overview

TestQL scenarios describe expected API behavior in a declarative DSL. When a scenario fails, llx can:

1. **Validate** the scenario via the TestQL CLI.
2. **Generate** planfile tickets for each failure.
3. **Upsert** tickets into `planfile.yaml` with identity-aware deduplication.
4. **Sync** tickets to `TODO.md` and configured integrations (GitHub, GitLab, Jira).

All of this is available both as a standalone CLI command and as a workflow step.

---

## `llx plan testql` — Standalone Command

Run a TestQL scenario and optionally create/sync tickets in one shot.

```bash
llx plan testql SCENARIO [OPTIONS]
```

### Arguments

- `SCENARIO` — Path to the `.testql.toon.yaml` scenario file.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--strategy`, `-s` | `planfile.yaml` | Target planfile YAML |
| `--project`, `-p` | `.` | Project root directory |
| `--url` | `http://localhost:8101` | TestQL service base URL |
| `--dry-run`, `-d` | `False` | Parse/validate only; do not execute |
| `--create-tickets` / `--no-create-tickets` | `True` | Create planfile tickets for failures |
| `--sync` / `--no-sync` | `True` | Sync tickets to TODO.md and integrations |
| `--max-tickets` | `25` | Max tickets generated from one run |
| `--testql-bin` | `testql` | TestQL CLI executable name/path |
| `--testql-repo-path` | `/home/tom/github/semcod/testql` | Fallback local repo path |
| `--output-yaml`, `-o` | — | Save full payload to a YAML file |

### Examples

```bash
# Basic validation + ticket generation + sync
llx plan testql testql-scenarios/api-smoke.testql.toon.yaml

# Dry-run: validate without creating tickets
llx plan testql testql-scenarios/api-smoke.testql.toon.yaml --dry-run

# Custom project and strategy
llx plan testql scenarios/smoke.testql.toon.yaml -p ./my-api -s my-api/planfile.yaml

# Save results for CI inspection
llx plan testql scenarios/smoke.testql.toon.yaml -o testql-results.yaml
```

### Output

The command prints a summary to stderr and writes a YAML payload to stdout:

```yaml
scenario: scenarios/smoke.testql.toon.yaml
strategy: planfile.yaml
project: /home/tom/projects/my-api
dry_run: false
validation:
  ok: false
  passed: 2
  failed: 1
  exit_code: 1
  errors:
    - "step 'health-check': status mismatch"
tickets:
  generated: 1
  created: 1
  skipped: 0
  created_ticket_ids:
    - TQL-a1b2c3d4e5
  sync:
    sync_order:
      - markdown
      - github
    integrations:
      - integration: markdown
        created: 1
        updated: 0
        skipped: 0
        failed: 0
      - integration: github
        created: 1
        updated: 0
        skipped: 0
        failed: 0
```

If validation fails (`ok: false`), the CLI exits with code `1`.

---

## Workflow Step — `testql`

In llx workflow YAML, use the `testql` step to embed TestQL validation inside a pipeline.

```yaml
steps:
  - name: validate-api
    type: testql
    params:
      scenario: testql-scenarios/api-smoke.testql.toon.yaml
      strategy: planfile.yaml
      project: .
      url: http://localhost:8101
      dry_run: false
      create_tickets: true
      sync_targets: true
      max_tickets: 25
      testql_bin: testql
      testql_repo_path: /home/tom/github/semcod/testql
      fail_on_failure: true
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `scenario` | **required** | Path to `.testql.toon.yaml` |
| `strategy` | `planfile.yaml` | Target planfile YAML |
| `project` | `.` | Project root directory |
| `url` | `http://localhost:8101` | TestQL service URL |
| `dry_run` | `false` | Parse/validate only |
| `create_tickets` | `true` | Create tickets for failures |
| `sync_targets` | `true` | Sync to TODO.md and integrations |
| `max_tickets` | `25` | Ticket cap per run |
| `testql_bin` | `testql` | TestQL CLI executable |
| `testql_repo_path` | `/home/tom/github/semcod/testql` | Fallback repo path |
| `fail_on_failure` | `true` | Mark step as failed when checks fail |

---

## Pre-flight Freshness Validation (`llx plan run` & `llx plan validate`)

Before executing tasks, `llx plan run` can run a **prefact-driven freshness check** to detect stale tickets and optionally skip or cancel them.

### `llx plan run` Options

| Option | Default | Description |
|--------|---------|-------------|
| `--validate` / `--no-validate` | `True` | Pre-flight: scan code and skip stale tickets |
| `--cancel-stale` | `False` | Mark stale tickets as canceled in planfile |
| `--prefact-yaml` | — | Explicit prefact.yaml for the scan |
| `--prefact-bin` | — | Custom prefact executable name/path |

### Examples

```bash
# Run with pre-flight freshness check (default)
llx plan run planfile.yaml

# Cancel stale tickets before running
llx plan run planfile.yaml --cancel-stale

# Disable pre-flight validation
llx plan run planfile.yaml --no-validate
```

### `llx plan validate` — Dedicated Freshness Command

```bash
# Validate ticket freshness and print markdown report
llx plan validate planfile.yaml

# Cancel stale tickets in the planfile
llx plan validate planfile.yaml --cancel-stale

# Exit non-zero when stale tickets are found
llx plan validate planfile.yaml --fail-on-stale

# Require a successful prefact scan
llx plan validate planfile.yaml --require-scan --fail-on-stale
```

The freshness report contains:

```yaml
scan:
  backend: prefact
  ok: true
stale_ticket_ids:
  - TICKET-42
  - TICKET-99
stale: 2
current: 15
unknown: 3
```

---

## Identity-Aware Ticket Deduplication

When upserting TestQL tickets into `planfile.yaml`, the system collects **identity keys** from each ticket to prevent duplicates across integrations:

- `local_id` — ticket `id` or `ticket_id`
- `external_id` — `external_id` or integration-specific IDs (`github_id`, `gitlab_id`, `jira_id`)
- `external_key` — `external_key`, `key`, or integration-specific keys
- `external_url` — `external_url`, `url`, `issue_url`, `ticket_url`, or integration-specific URLs
- `source` and `external_refs` dictionaries

If an incoming ticket shares any identity key with an existing task, it is **skipped** instead of recreated.

---

## End-to-End Example

```bash
# 1. Start the API under test
python -m my_api &

# 2. Run TestQL validation, create tickets, sync to GitHub
llx plan testql testql-scenarios/api-smoke.testql.toon.yaml --strategy planfile.yaml --sync

# 3. Execute planfile tasks, skipping stale tickets and canceling them
llx plan run planfile.yaml --cancel-stale --format markdown

# 4. Validate remaining tickets are still fresh
llx plan validate planfile.yaml --fail-on-stale
```

---

**LLX TestQL Integration** — Validate APIs, generate tickets, and keep your backlog in sync. 🚀
