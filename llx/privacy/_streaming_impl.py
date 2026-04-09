"""Streaming and chunked processing for large project anonymization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterator

from llx.privacy._project_anonymizer import (
    ProjectAnonymizationResult as _ProjectAnonymizationResult,
    ProjectAnonymizer,
)
from llx.privacy._project_context import (
    AnonymizationContext,
    SymbolMapping as _SymbolMapping,
)
from llx.privacy._streaming_chunking import (
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_INCLUDE_PATTERNS,
    ChunkResult,
    ChunkedProcessor,
    ProgressCallback,
    ProgressInfo,
)
from llx.privacy.deanonymize import ProjectDeanonymizer, StreamingDeanonymizer


__all__ = [
    "AnonymizationContext",
    "ProjectAnonymizer",
    "ProjectAnonymizationResult",
    "SymbolMapping",
    "ProgressInfo",
    "ProgressCallback",
    "ChunkResult",
    "ChunkedProcessor",
    "StreamingProjectAnonymizer",
    "StreamingProjectDeanonymizer",
    "ParallelProjectProcessor",
    "anonymize_project_with_progress",
    "deanonymize_response_streaming",
]

ProjectAnonymizationResult = _ProjectAnonymizationResult
SymbolMapping = _SymbolMapping


class StreamingProjectAnonymizer:
    """Stream-process large projects with progress tracking.

    Memory-efficient processing that yields progress updates
    and handles cancellation gracefully.
    """

    def __init__(
        self,
        project_path: str | Path,
        context: AnonymizationContext | None = None,
    ):
        self.project_path = Path(project_path)
        self.context = context or AnonymizationContext(project_path)
        self.anonymizer = ProjectAnonymizer(self.context)
        self.chunked_processor = ChunkedProcessor()

    def anonymize_streaming(
        self,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        chunk_size: int = 100,
        progress_callback: ProgressCallback | None = None,
    ) -> Iterator[ProgressInfo]:
        """Stream anonymize project with progress updates."""
        include, exclude = self._resolve_patterns(include_patterns, exclude_patterns)
        all_files, total_bytes = self._collect_files(include, exclude)
        progress = self._build_progress(all_files, total_bytes, chunk_size)

        if not all_files:
            return

        for current_chunk, batch in enumerate(self._iter_batches(all_files, chunk_size), start=1):
            if not self._process_batch(batch, progress, progress_callback):
                return

            progress.current_chunk = current_chunk
            yield progress

    def _resolve_patterns(
        self,
        include_patterns: list[str] | None,
        exclude_patterns: list[str] | None,
    ) -> tuple[list[str], list[str]]:
        include = include_patterns or DEFAULT_INCLUDE_PATTERNS
        exclude = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
        return include, exclude

    def _collect_files(
        self,
        include_patterns: list[str],
        exclude_patterns: list[str],
    ) -> tuple[list[tuple[Path, int]], int]:
        all_files: list[tuple[Path, int]] = []
        total_bytes = 0

        for pattern in include_patterns:
            for file_path in self.project_path.rglob(pattern):
                if self._is_excluded(file_path, exclude_patterns):
                    continue
                try:
                    size = file_path.stat().st_size
                except OSError:
                    continue
                all_files.append((file_path, size))
                total_bytes += size

        return all_files, total_bytes

    def _is_excluded(self, file_path: Path, exclude_patterns: list[str]) -> bool:
        return any(file_path.match(pattern) for pattern in exclude_patterns)

    def _build_progress(
        self,
        all_files: list[tuple[Path, int]],
        total_bytes: int,
        chunk_size: int,
    ) -> ProgressInfo:
        total_files = len(all_files)
        total_chunks = (total_files + chunk_size - 1) // chunk_size if all_files else 0
        return ProgressInfo(
            total_files=total_files,
            bytes_total=total_bytes,
            total_chunks=total_chunks,
        )

    def _iter_batches(
        self,
        items: list[tuple[Path, int]],
        batch_size: int,
    ) -> Iterator[list[tuple[Path, int]]]:
        batch: list[tuple[Path, int]] = []
        for item in items:
            batch.append(item)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _process_batch(
        self,
        batch: list[tuple[Path, int]],
        progress: ProgressInfo,
        progress_callback: ProgressCallback | None,
    ) -> bool:
        for fp, size in batch:
            self._process_file(fp, size, progress)
            if progress_callback:
                result = progress_callback(progress)
                if result is False:
                    return False
        return True

    def _process_file(self, file_path: Path, size: int, progress: ProgressInfo) -> None:
        progress.current_file = str(file_path.relative_to(self.project_path))

        try:
            if size > self.chunked_processor.max_chunk_size:
                for _chunk in self._anonymize_large_file(file_path):
                    pass
            else:
                self.anonymizer.anonymize_file(file_path)

            progress.files_completed += 1
            progress.bytes_processed += size
            progress.symbol_mappings_created = sum(self.context.stats.values())
        except Exception as e:
            progress.files_failed += 1
            self.anonymizer.errors.append(f"{file_path}: {e}")

    def _anonymize_large_file(self, file_path: Path) -> Iterator[ChunkResult]:
        def anonymize_chunk(content: str) -> str:
            return self.anonymizer.anonymize_string(content, str(file_path))

        return self.chunked_processor.process_file(file_path, anonymize_chunk)

    def save_context(self, output_path: str | Path) -> None:
        self.context.save(output_path)


class StreamingProjectDeanonymizer:
    """Stream-process large deanonymization operations.

    Efficiently restores original values from large LLM outputs
    or project files with progress tracking.
    """

    def __init__(
        self,
        context: AnonymizationContext | str | Path,
    ):
        if isinstance(context, (str, Path)):
            self.context = AnonymizationContext.load(context)
        else:
            self.context = context

        self.deanonymizer = ProjectDeanonymizer(self.context)
        self.streaming_deanonymizer = StreamingDeanonymizer(self.context)

    def deanonymize_streaming(
        self,
        text_stream: Iterator[str],
        progress_callback: ProgressCallback | None = None,
    ) -> Iterator[str]:
        """Deanonymize streaming text (e.g., from LLM)."""
        total_chars = 0

        for chunk in text_stream:
            total_chars += len(chunk)
            result = self.streaming_deanonymizer.feed_chunk(chunk)

            if not result:
                continue

            if progress_callback:
                stats = self.streaming_deanonymizer.get_stats()
                progress = ProgressInfo(
                    bytes_processed=total_chars,
                    symbol_mappings_created=stats["total_restorations"],
                )
                cb_result = progress_callback(progress)
                if cb_result is False:
                    return

            yield result

        final = self.streaming_deanonymizer.finalize()
        if final:
            yield final

    def deanonymize_files_streaming(
        self,
        files: dict[str, str],
        progress_callback: ProgressCallback | None = None,
    ) -> Iterator[tuple[str, str]]:
        """Deanonymize multiple files with progress tracking."""
        total = len(files)

        for i, (file_path, content) in enumerate(files.items()):
            result = self.deanonymizer.deanonymize_file(content, file_path)

            if progress_callback:
                progress = ProgressInfo(
                    total_files=total,
                    files_completed=i + 1,
                    current_file=file_path,
                    symbol_mappings_created=len(result.restorations),
                )
                cb_result = progress_callback(progress)
                if cb_result is False:
                    return

            yield (file_path, result.text)


class ParallelProjectProcessor:
    """Process multiple files in parallel for speed.

    Uses multiprocessing for CPU-bound anonymization tasks.
    """

    def __init__(
        self,
        project_path: str | Path,
        max_workers: int | None = None,
    ):
        self.project_path = Path(project_path)
        self.max_workers = max_workers or os.cpu_count() or 4

    def anonymize_parallel(
        self,
        files: list[str | Path],
        context: AnonymizationContext,
    ) -> dict[str, str]:
        """Anonymize multiple files in parallel."""
        from concurrent.futures import ProcessPoolExecutor, as_completed

        results: dict[str, str] = {}
        anonymizer = ProjectAnonymizer(context)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(anonymizer.anonymize_file, fp): fp
                for fp in files
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                except Exception as e:
                    results[str(file_path)] = f"# ERROR: {e}\n"

        return results


def anonymize_project_with_progress(
    project_path: str | Path,
    output_dir: str | Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    on_progress: Callable[[ProgressInfo], bool | None] | None = None,
) -> AnonymizationContext:
    """Anonymize project with progress tracking."""
    streamer = StreamingProjectAnonymizer(project_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for progress in streamer.anonymize_streaming(
        include_patterns=include,
        exclude_patterns=exclude,
        progress_callback=on_progress,
    ):
        pass

    context_file = output_path / ".anonymization_context.json"
    streamer.save_context(context_file)

    return streamer.context


def deanonymize_response_streaming(
    llm_response_stream: Iterator[str],
    context_path: str | Path,
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """Deanonymize streaming LLM response."""
    streamer = StreamingProjectDeanonymizer(context_path)

    result_parts: list[str] = []
    for chunk in streamer.deanonymize_streaming(llm_response_stream):
        result_parts.append(chunk)
        if on_chunk:
            on_chunk(chunk)

    return "".join(result_parts)
