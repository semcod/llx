# Planfile cleanup, freshness & pruning

This guide explains the **lifecycle** of a ticket inside `planfile.yaml` when
you drive it with `llx`, and the commands that keep it healthy.

```text
                ┌─────────────────────┐
                │  planfile.yaml      │
                │  (tickets + sprints)│
                └─────────┬───────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │  llx plan run  (default flow)    │
        │                                  │
        │  1. pre-flight (prefact scan)    │  ─► classifies tickets:
        │     ├─ current  → keep           │     current / stale / unknown
        │     ├─ stale    → mark canceled  │
        │     └─ unknown  → leave for      │
        │                   manual review  │
        │  2. execute remaining tickets    │
        │     via LLM (skip already        │
        │     resolved ones)               │
        │  3. results → status: done /     │
        │     status: failed in planfile   │
        └──────────────┬───────────────────┘
                       │
                       ▼
                ┌────────────────────────┐
                │  llx plan clean        │
                │  (this command)        │
                └────────────────────────┘
                    │            │
                    ▼            ▼
         planfile.yaml      TODO.md
         (drop tickets)     (drop matching lines)
```

## Quick reference

| Goal                                                    | Command                                                                |
|---------------------------------------------------------|------------------------------------------------------------------------|
| **Run plan**, auto-cancel stale, no file mutation       | `llx plan run`                                                          |
| Run plan and **physically delete stale** tickets         | `llx plan run --prune-stale`                                            |
| Also delete `unknown` (insufficient_data) tickets        | `llx plan run --prune-stale --prune-unknown`                            |
| Validate freshness without executing LLM                 | `llx plan validate`                                                     |
| Validate + delete stale/unknown                          | `llx plan validate --prune-stale --prune-unknown`                       |
| **Remove canceled tickets** from `planfile.yaml` + TODO  | `llx plan clean`                                                        |
| Same, also wipe `done` tickets                           | `llx plan clean --include-done`                                         |
| Preview only (no writes)                                 | `llx plan clean --dry-run`                                              |
| Skip TODO.md sync                                        | `llx plan clean --no-todo-sync`                                         |
| Skip backup files                                        | `llx plan clean --no-backup`                                            |

All mutating commands write `planfile.yaml.bak.<YYYYMMDD-HHMMSS>` (and
`TODO.md.bak.<...>` when applicable) by default. Use `--no-backup` to disable.

## Lifecycle in detail

### 1. Pre-flight (during `llx plan run`)

Every `llx plan run` (and standalone `llx plan validate`) runs a code-truth
scan via [`prefact`](../../prefact/README.md) and compares each ticket's
declared issue (`rule_id` / `files` / `line`) with the actual scan output.
Tickets fall into one of three buckets:

| Bucket    | Meaning                                                          | Default action                                            |
|-----------|------------------------------------------------------------------|-----------------------------------------------------------|
| `current` | The issue still exists in the codebase                           | Pass to LLM for fix                                       |
| `stale`   | prefact no longer reports the issue (it was already fixed/moved) | Skip from LLM run, **mark `status: canceled` in planfile**|
| `unknown` | Not enough metadata (no `rule_id` / no `line`) to verify         | Skip from LLM run, leave untouched                        |

Defaults of `llx plan run` (and `llx plan validate`) since the cleanup
refactor:

- `--validate` (pre-flight) is **on**.
- `--cancel-stale` is **on** — stale tickets are stamped `status: canceled`
  with a timestamped note, but **not deleted**.
- `--prune-stale` and `--prune-unknown` are **off** (opt-in hard delete).

After pre-flight you'll see a hint:

```
Pre-flight: scanner=engine stale=27 unknown=157 current=0
Tip: run llx plan clean later to physically remove canceled tickets from planfile.yaml and TODO.md.
```

### 2. Status-based cleanup (`llx plan clean`)

`llx plan clean` is the **post-run maintenance** command. It does not call
prefact and does not interact with the LLM — it just walks `planfile.yaml`,
finds tickets whose `status` matches a target set, removes those entries
from the planfile, and wipes corresponding lines from `TODO.md`.

```bash
# default: drop everything marked canceled
llx plan clean

# include done items (already-completed work)
llx plan clean --include-done

# preview before committing
llx plan clean --include-done --dry-run

# clean only the planfile, leave TODO.md alone
llx plan clean --no-todo-sync

# explicit TODO path (e.g. multi-doc workspaces)
llx plan clean --todo-path docs/TODO-llx.md

# clean a planfile somewhere else
llx plan clean other-strategy.yaml --project /path/to/project
```

Output is markdown by default with a YAML codeblock summary. Use
`--format yaml` for machine-readable output that's easy to pipe.

### 3. Hard-delete pruning (`--prune-*`)

If you'd rather **not have a separate cleanup step** and want stale tickets
gone immediately during validation/run, use the prune flags:

```bash
# Validate-only with hard delete + backup
llx plan validate --prune-stale --prune-unknown

# Hard delete inline with the LLM run
llx plan run --prune-stale --prune-unknown
```

`--prune-unknown` is more aggressive — it removes tickets that the validator
could not classify (typically because they lack `rule_id` and `line`). Use
it carefully when your planfile is auto-generated and contains many such
entries.

## Recovery

Every mutating operation writes a backup unless you pass `--no-backup`:

- `planfile.yaml.bak.<YYYYMMDD-HHMMSS>`
- `TODO.md.bak.<YYYYMMDD-HHMMSS>` (when TODO sync ran)

Restore is just a copy:

```bash
cp planfile.yaml.bak.20251101-120000 planfile.yaml
cp TODO.md.bak.20251101-120000 TODO.md
```

## Inside a workflow (`llx.yaml`)

All these operations are also exposed as workflow `kind:`s so you can wire
them into a pipeline executed via `llx run [WORKFLOW]`:

```yaml
workflows:
  weekly-cleanup:
    description: "Validate, prune stale code-confirmed tickets, then drop canceled."
    steps:
      - name: validate
        kind: plan-validate
        with:
          strategy: planfile.yaml
          cancel_stale: true
          prune_stale: true            # hard delete stale findings
          backup: true
      - name: clean
        kind: plan-clean
        with:
          strategy: planfile.yaml
          include_done: false          # set true to also drop done items
          update_todo: true
          backup: true
```

Run it with:

```bash
llx run weekly-cleanup
```

## Synthetic entry refs

When tickets in your planfile have **no `id` field**, the validator emits
synthetic identifiers like `sprints[0].task_patterns[42]` (positional refs).
Both `--prune-*` flags and `llx plan clean`'s pruner understand these refs,
so even pathological auto-generated planfiles can be cleaned.

If you'd rather give every entry a stable `id` first (recommended for
manual maintenance), the long-term plan is `llx plan assign-ids` — see the
roadmap section in `README.md`.

## What `prune` will *not* do

- It will not remove tickets that are still marked `current` or `open`.
- It will not call the LLM.
- It will not move tickets into a separate archive — they're deleted.
  Use `git diff` plus the `.bak.<ts>` backup if you need to recover.

## Programmatic API

The same building blocks are importable from `llx`:

```python
from llx.planfile.ticket_freshness import validate_tickets_with_prefact
from llx.planfile.ticket_pruner import prune_planfile_tickets
from llx.planfile.ticket_cleaner import (
    collect_ticket_ids_by_status,
    remove_ticket_lines_from_todo,
    clean_resolved_tickets,
)
```

Each function returns a structured dict, so they're easy to compose in
custom scripts and CI pipelines.

## Output format

All planfile-related commands (`llx plan run`, `llx plan validate`,
`llx plan clean`, `llx run`) emit **markdown** by default with a
syntax-highlighted YAML codeblock. The markdown is rendered with:

- **Colored headings** (`##` → bold cyan, `###` → bold yellow)
- **Bullets** with dim styling and inline marks (`**bold**`, `` `code` ``)
- **Single freshness section** — no duplicate `## Ticket Freshness` panels
- **No null fields** in the embedded YAML (kept clean for readability)
- **No padding** — lines are not padded to terminal width

When piping to a file or non-TTY, the raw markdown source is preserved
so you can parse or save it directly. Use `--format yaml` for pure
machine-readable YAML output (no markdown wrapper).

Example output for a run with freshness enabled:

```markdown
## Execution Summary

- **Strategy:** planfile.yaml
- **Project:** .
- **Timestamp:** 2026-04-26 18:25:24
- **Total Tasks:** 0

_No tasks executed._

## Ticket Freshness

- **Scanner:** subprocess (available)
- **Issues found:** 0
- **Tickets evaluated:** 0 (current=0, stale=0, unknown=0)

### Results Payload

```yaml
strategy: planfile.yaml
project: .
dry_run: false
summary: { total: 0, ... }
freshness:
  scan: { backend: subprocess, issues: 0, ... }
```
```
