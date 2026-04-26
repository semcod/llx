from __future__ import annotations

import importlib

from llx.planfile.executor.base import TaskResult
from llx.planfile.executor.task import _parse_llm_response


def test_parse_llm_response_ignores_no_changes_inside_code_blocks() -> None:
    response = (
        "```python:llx/cli/app.py\n"
        "def f():\n"
        "    console.print(\"No changes needed\")\n"
        "```\n"
    )

    parsed = _parse_llm_response(response)

    assert parsed["issue_not_found"] is False
    assert parsed["changes_made"] is True
    assert parsed["message"] == "LLM reports changes made"


def test_persist_failed_results_skips_synthetic_ticket_ids(tmp_path, monkeypatch) -> None:
    app_mod = importlib.import_module("llx.cli.app")
    calls: list[tuple[str, str, str, str]] = []
    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text("tasks:\n  - id: Q01\n", encoding="utf-8")

    def fake_update(planfile_path: str, task_id: str, status: str, comment: str) -> bool:
        calls.append((planfile_path, task_id, status, comment))
        return True

    monkeypatch.setattr("llx.planfile.executor.strategy._update_task_in_planfile", fake_update)

    app_mod._persist_failed_results(
        [
            TaskResult(
                ticket_id="task-abc123",
                task_name="Fix issue",
                status="no_changes",
                model_used="m",
                response="",
                validation_message="No changes needed: No action needed.",
            )
        ],
        str(strategy_path),
    )

    assert calls == []


def test_persist_failed_results_updates_top_level_q_tickets(tmp_path, monkeypatch) -> None:
    app_mod = importlib.import_module("llx.cli.app")
    calls: list[tuple[str, str, str, str]] = []
    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text("tasks:\n  - id: Q01\n", encoding="utf-8")

    def fake_update(planfile_path: str, task_id: str, status: str, comment: str) -> bool:
        calls.append((planfile_path, task_id, status, comment))
        return True

    monkeypatch.setattr("llx.planfile.executor.strategy._update_task_in_planfile", fake_update)

    app_mod._persist_failed_results(
        [
            TaskResult(
                ticket_id="Q01",
                task_name="Fix issue",
                status="no_changes",
                model_used="m",
                response="",
                validation_message="No changes needed: No action needed.",
            )
        ],
        str(strategy_path),
    )

    assert len(calls) == 1
    assert calls[0][1] == "Q01"
    # 'no_changes' result status maps to 'canceled' ticket status (issue not found)
    assert calls[0][2] == "canceled"


def test_build_results_markdown_embeds_yaml_codeblock_with_ticket_ids() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    payload = {
        "strategy": "planfile.yaml",
        "project": ".",
        "sprint": None,
        "ticket_id": None,
        "tier": None,
        "dry_run": False,
        "timestamp": "2026-04-26 16:50:00",
        "summary": {
            "success": 1,
            "failed": 0,
            "invalid": 0,
            "not_found": 0,
            "already_fixed": 0,
            "no_changes": 0,
            "skipped": 0,
            "total": 1,
        },
        "results": [
            {
                "ticket_id": "Q01",
                "task_name": "Add markdown stdout output",
                "status": "success",
                "model_used": "openrouter/qwen",
                "response": "ok",
                "error": None,
                "execution_time": 0.42,
                "file_changed": True,
                "validation_message": None,
            }
        ],
    }

    markdown = app_mod._build_results_markdown(payload)

    assert "## Execution Summary" in markdown
    assert "```yaml" in markdown
    assert "ticket_id: Q01" in markdown
    assert "status: success" in markdown


def test_build_results_markdown_handles_empty_results() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    payload = {
        "strategy": "planfile.yaml",
        "project": ".",
        "summary": {"total": 0},
        "results": [],
    }
    markdown = app_mod._build_results_markdown(payload)
    assert "## Execution Summary" in markdown
    assert "**Total Tasks:** 0" in markdown


def test_map_to_ticket_status_covers_all_known_statuses() -> None:
    from llx.planfile.executor.base import map_to_ticket_status

    assert map_to_ticket_status("success", True) == "done"
    assert map_to_ticket_status("success", False) == "done"
    assert map_to_ticket_status("no_changes", False) == "canceled"
    assert map_to_ticket_status("failed", False) == "blocked"
    assert map_to_ticket_status("invalid", False) == "open"
    assert map_to_ticket_status("not_found", False) == "canceled"
    assert map_to_ticket_status("already_fixed", False) == "done"
    assert map_to_ticket_status("dry_run", False) == "open"
    assert map_to_ticket_status("skipped", False) == "open"
    assert map_to_ticket_status("unknown_status", False) == "open"


def test_build_results_markdown_truncates_long_response_fields() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    long_blob = "X" * 4000
    payload = {
        "strategy": "planfile.yaml",
        "project": ".",
        "summary": {"total": 1, "success": 1},
        "results": [
            {
                "ticket_id": "Q01",
                "task_name": "Big response",
                "status": "success",
                "model_used": "openrouter/qwen",
                "response": long_blob,
                "error": None,
                "execution_time": 1.0,
                "file_changed": True,
                "validation_message": None,
            }
        ],
    }

    markdown = app_mod._build_results_markdown(payload)

    assert "truncated" in markdown
    # The original 4000-char string must not appear verbatim in markdown.
    assert long_blob not in markdown
    # Exact-truncation count of 'X' chars should not exceed the limit.
    assert markdown.count("X") <= app_mod._MARKDOWN_TRUNCATE_LIMIT


def test_truncate_long_strings_does_not_mutate_payload() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    long_blob = "Y" * 1000
    payload = {
        "results": [
            {"response": long_blob, "ticket_id": "Q01"},
        ]
    }

    compact = app_mod._truncate_long_strings_for_markdown(payload)
    assert compact["results"][0]["response"] != long_blob
    # Original untouched
    assert payload["results"][0]["response"] == long_blob


def test_results_markdown_skips_status_table_when_all_zero() -> None:
    """No row should appear if every status count is 0; show a one-liner instead."""
    app_mod = importlib.import_module("llx.cli.app")
    payload = {
        "strategy": "planfile.yaml",
        "project": ".",
        "summary": {
            "success": 0, "failed": 0, "invalid": 0, "not_found": 0,
            "already_fixed": 0, "no_changes": 0, "skipped": 0, "total": 0,
        },
        "results": [],
    }
    md = app_mod._build_results_markdown(payload)

    # Empty status table is suppressed
    assert "### Status Counts" not in md
    assert "| Status | Count |" not in md
    # Friendly placeholder is shown instead
    assert "_No tasks executed._" in md


def test_results_markdown_strips_null_fields_from_yaml_payload() -> None:
    """sprint/ticket_id/tier=None should not appear in the markdown YAML codeblock."""
    app_mod = importlib.import_module("llx.cli.app")
    payload = {
        "strategy": "planfile.yaml",
        "project": ".",
        "sprint": None,
        "ticket_id": None,
        "tier": None,
        "summary": {"total": 0},
        "results": [],
    }
    md = app_mod._build_results_markdown(payload)

    assert "sprint: null" not in md
    assert "ticket_id: null" not in md
    assert "tier: null" not in md


def test_results_markdown_embeds_freshness_section_when_provided() -> None:
    """Freshness data must appear once as a compact section (not as duplicated YAML panel)."""
    app_mod = importlib.import_module("llx.cli.app")
    payload = {
        "strategy": "planfile.yaml",
        "project": ".",
        "summary": {"total": 0},
        "results": [],
        "freshness": {
            "total": 3,
            "current": 1,
            "stale": 2,
            "unknown": 0,
            "stale_ticket_ids": ["A", "B"],
            "review_needed_ticket_ids": [],
            "scan": {"available": True, "backend": "engine", "issues": 5},
        },
    }
    md = app_mod._build_results_markdown(payload)

    # Inline freshness summary present
    assert "## Ticket Freshness" in md
    assert "engine (available)" in md
    assert "current=1, stale=2, unknown=0" in md
    assert "`A`" in md and "`B`" in md
    # No standalone "Freshness Payload" header — single YAML at the end.
    assert "### Freshness Payload" not in md
    assert md.count("```yaml") == 1


def test_render_markdown_inline_styles_bold_italic_code() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    text = app_mod._render_markdown_inline("plain **bold** _italic_ `code` end")

    assert text.plain == "plain bold italic code end"
    # Verify each marked span carried a style (bold / italic / cyan).
    span_styles = {(text.plain[s.start:s.end], str(s.style)) for s in text.spans}
    style_for = {token: style for token, style in span_styles}
    assert "bold" in style_for["bold"]
    assert "italic" in style_for["italic"]
    assert "cyan" in style_for["code"]


def test_print_markdown_with_yaml_pipe_keeps_raw_text() -> None:
    """Non-TTY targets must keep the markdown source intact (no ANSI)."""
    import io
    from rich.console import Console as RichConsole
    app_mod = importlib.import_module("llx.cli.app")

    buf = io.StringIO()
    console = RichConsole(file=buf, force_terminal=False, color_system=None)
    md = "## Heading\n\n- **k:** v\n\n```yaml\na: 1\n```\n"
    app_mod._print_markdown_with_yaml(md, console)
    out = buf.getvalue()
    assert "## Heading" in out
    assert "**k:**" in out
    assert "```yaml" in out
    assert "\x1b[" not in out  # no ANSI escapes


def test_print_markdown_with_yaml_tty_emits_ansi_for_headings() -> None:
    """TTY targets must color headings (no leading '##' literal)."""
    import io
    from rich.console import Console as RichConsole
    app_mod = importlib.import_module("llx.cli.app")

    buf = io.StringIO()
    console = RichConsole(file=buf, force_terminal=True, color_system="truecolor", width=80)
    md = "## Execution Summary\n\n- **Strategy:** planfile.yaml\n\n```yaml\nkey: value\n```\n"
    app_mod._print_markdown_with_yaml(md, console)
    out = buf.getvalue()
    # Heading text is rendered without the literal '##'
    assert "Execution Summary" in out
    assert "## Execution Summary" not in out
    # ANSI escape present (Rich emitted styled output)
    assert "\x1b[" in out


def test_split_markdown_around_codeblock_isolates_yaml() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    md = (
        "## Header\n\n"
        "- bullet\n\n"
        "```yaml\n"
        "key: value\n"
        "key2: 123\n"
        "```\n"
        "after\n"
    )
    prefix, code, suffix = app_mod._split_markdown_around_codeblock(md)
    assert "## Header" in prefix
    assert "- bullet" in prefix
    assert code == "key: value\nkey2: 123"
    assert "after" in suffix


def test_truncate_only_targets_whitelisted_fields() -> None:
    app_mod = importlib.import_module("llx.cli.app")
    long_blob = "Z" * 500
    payload = {
        "task_name": long_blob,        # not whitelisted -> kept as-is
        "ticket_id": long_blob,        # not whitelisted -> kept as-is
        "response": long_blob,         # whitelisted -> truncated
    }

    compact = app_mod._truncate_long_strings_for_markdown(payload)
    assert compact["task_name"] == long_blob
    assert compact["ticket_id"] == long_blob
    assert compact["response"] != long_blob
