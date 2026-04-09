"""Patch application helpers for `llx.commands.fix`."""

from __future__ import annotations

from pathlib import Path


def _extract_json_from_content(content: str) -> str | None:
    """Extract a JSON array from content, handling ```json fences."""
    import re

    m = re.search(r'```json\s*\n(.*?)```', content, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\[\s*\{.*\}\s*\])', content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _apply_unified_diff(file_path: Path, patch_text: str) -> bool:
    """Apply a unified diff patch to a file using line-level matching."""
    import subprocess as _sp

    original = file_path.read_text()
    original_lines = original.splitlines(keepends=True)

    hunks = _parse_unified_hunks(patch_text)
    if hunks:
        result_lines = list(original_lines)
        offset = 0
        for hunk in hunks:
            old_start, old_count, new_lines_for_hunk, removed_lines = hunk
            pos = _find_hunk_position(result_lines, removed_lines, old_start - 1 + offset)
            if pos is not None:
                del result_lines[pos:pos + len(removed_lines)]
                for i, nl in enumerate(new_lines_for_hunk):
                    result_lines.insert(pos + i, nl)
                offset += len(new_lines_for_hunk) - len(removed_lines)
            else:
                return False
        file_path.write_text(''.join(result_lines))
        return True

    try:
        proc = _sp.run(
            ['patch', '--no-backup-if-mismatch', '-p1', str(file_path)],
            input=patch_text,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0
    except (FileNotFoundError, _sp.TimeoutExpired):
        return False


def _parse_unified_hunks(patch_text: str) -> list[tuple[int, int, list[str], list[str]]]:
    """Parse a unified diff into hunks."""
    import re

    hunks: list[tuple[int, int, list[str], list[str]]] = []
    hunk_header = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@')

    current_old_start = 0
    current_old_count = 0
    new_lines: list[str] = []
    removed_lines: list[str] = []
    in_hunk = False

    for raw_line in patch_text.splitlines():
        m = hunk_header.match(raw_line)
        if m:
            if in_hunk and (new_lines or removed_lines):
                hunks.append((current_old_start, current_old_count, new_lines, removed_lines))
            current_old_start = int(m.group(1))
            current_old_count = int(m.group(2) or '1')
            new_lines = []
            removed_lines = []
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if raw_line.startswith('-') and not raw_line.startswith('---'):
            removed_lines.append(raw_line[1:] + '\n')
        elif raw_line.startswith('+') and not raw_line.startswith('+++'):
            new_lines.append(raw_line[1:] + '\n')
        elif raw_line.startswith(' '):
            removed_lines.append(raw_line[1:] + '\n')
            new_lines.append(raw_line[1:] + '\n')

    if in_hunk and (new_lines or removed_lines):
        hunks.append((current_old_start, current_old_count, new_lines, removed_lines))

    return hunks


def _find_hunk_position(lines: list[str], removed_lines: list[str], hint: int) -> int | None:
    """Find where `removed_lines` appear in `lines`, starting near `hint`."""
    if not removed_lines:
        return max(0, min(hint, len(lines)))

    stripped_removed = [l.rstrip('\n') for l in removed_lines]
    for delta in range(0, 80):
        for candidate in (hint + delta, hint - delta):
            if candidate < 0 or candidate + len(stripped_removed) > len(lines):
                continue
            if all(lines[candidate + i].rstrip('\n') == rl for i, rl in enumerate(stripped_removed)):
                return candidate
    return None
