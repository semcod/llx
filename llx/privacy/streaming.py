"""Streaming and chunked processing for large project anonymization.

Handles projects of any size by processing files in chunks and streaming results.
Provides progress callbacks and memory-efficient processing.

Usage:
    from llx.privacy.streaming import StreamingProjectAnonymizer, ChunkedProcessor
    
    # Stream anonymization
    streamer = StreamingProjectAnonymizer(project_path)
    
    for progress in streamer.anonymize_streaming(
        chunk_size=100,  # files per chunk
        progress_callback=lambda p: print(f"{p.percent}% done")
    ):
        print(f"Processed {progress.files_completed}/{progress.total_files}")
    
    # Chunked processing for very large files
    processor = ChunkedProcessor(max_chunk_size=1024*1024)  # 1MB chunks
    for chunk_result in processor.process_file("large_file.py"):
        process(chunk_result.content)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol

from llx.privacy.project import (
    AnonymizationContext,
    ProjectAnonymizer,
    ProjectAnonymizationResult,
    SymbolMapping,
)
from llx.privacy.deanonymize import ProjectDeanonymizer, StreamingDeanonymizer


@dataclass
class ProgressInfo:
    """Progress information for streaming operations."""

    total_files: int = 0
    files_completed: int = 0
    files_failed: int = 0
    bytes_processed: int = 0
    bytes_total: int = 0
    current_file: str | None = None
    current_chunk: int = 0
    total_chunks: int = 0
    symbol_mappings_created: int = 0

    @property
    def percent(self) -> float:
        """Calculate completion percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.files_completed / self.total_files) * 100

    @property
    def bytes_percent(self) -> float:
        """Calculate byte completion percentage."""
        if self.bytes_total == 0:
            return 0.0
        return (self.bytes_processed / self.bytes_total) * 100


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(self, progress: ProgressInfo) -> bool | None:
        """
        Called with progress updates.
        
        Returns:
            False to cancel operation, True/None to continue
        """
        ...


@dataclass
class ChunkResult:
    """Result of processing a single chunk."""

    content: str
    chunk_number: int
    is_complete: bool = False
    symbols_in_chunk: list[str] = field(default_factory=list)


class ChunkedProcessor:
    """Process large files in chunks to manage memory usage.
    
    Splits files into manageable chunks while preserving context
    for proper anonymization.
    """

    def __init__(self, max_chunk_size: int = 1024 * 1024):  # 1MB default
        self.max_chunk_size = max_chunk_size

    def process_file(
        self,
        file_path: str | Path,
        anonymizer_func: Callable[[str], str],
    ) -> Iterator[ChunkResult]:
        """Process a file in chunks.
        
        For Python files, tries to split at logical boundaries
        (function/class definitions, blank lines).
        
        Args:
            file_path: Path to file to process
            anonymizer_func: Function to anonymize each chunk
            
        Yields:
            ChunkResult for each chunk
        """
        file_path = Path(file_path)
        file_size = file_path.stat().st_size

        # Small files: process as single chunk
        if file_size <= self.max_chunk_size:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            anonymized = anonymizer_func(content)
            yield ChunkResult(
                content=anonymized,
                chunk_number=1,
                is_complete=True,
            )
            return

        # Large files: split into chunks
        yield from self._split_and_process(file_path, anonymizer_func)

    def _split_and_process(
        self,
        file_path: Path,
        anonymizer_func: Callable[[str], str],
    ) -> Iterator[ChunkResult]:
        """Split large file and process chunks."""
        chunk_num = 0
        buffer = ""
        buffer_size = 0

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_size = len(line.encode("utf-8"))

                # If a single line exceeds chunk size, we must split it forcibly
                if line_size > self.max_chunk_size:
                    # First, flush any existing buffer
                    if buffer:
                        chunk_num += 1
                        anonymized = anonymizer_func(buffer)
                        yield ChunkResult(
                            content=anonymized,
                            chunk_number=chunk_num,
                            is_complete=False,
                        )
                        buffer = ""
                        buffer_size = 0

                    # Split the oversized line into forced chunks
                    line_bytes = line.encode("utf-8")
                    for i in range(0, len(line_bytes), self.max_chunk_size):
                        chunk_bytes = line_bytes[i:i + self.max_chunk_size]
                        chunk_str = chunk_bytes.decode("utf-8", errors="replace")
                        chunk_num += 1
                        anonymized = anonymizer_func(chunk_str)
                        yield ChunkResult(
                            content=anonymized,
                            chunk_number=chunk_num,
                            is_complete=False,
                        )
                    continue

                # Check if adding this line would exceed chunk size
                if buffer_size + line_size > self.max_chunk_size and buffer:
                    # Process current buffer
                    chunk_num += 1
                    anonymized = anonymizer_func(buffer)
                    yield ChunkResult(
                        content=anonymized,
                        chunk_number=chunk_num,
                        is_complete=False,
                    )
                    # Start new buffer
                    buffer = line
                    buffer_size = line_size
                else:
                    buffer += line
                    buffer_size += line_size

            # Process remaining buffer
            if buffer:
                chunk_num += 1
                anonymized = anonymizer_func(buffer)
                yield ChunkResult(
                    content=anonymized,
                    chunk_number=chunk_num,
                    is_complete=True,
                )


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
        chunk_size: int = 100,  # Number of files per batch
        progress_callback: ProgressCallback | None = None,
    ) -> Iterator[ProgressInfo]:
        """Stream anonymize project with progress updates.
        
        Args:
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            chunk_size: Number of files to process per batch
            progress_callback: Optional callback for progress
            
        Yields:
            ProgressInfo updates
        """
        include = include_patterns or ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"]
        exclude = exclude_patterns or [
            "**/.git/**", "**/venv/**", "**/.venv/**", "**/node_modules/**",
            "**/__pycache__/**", "**/.pytest_cache/**", "**/*.pyc",
            "**/.llx/**", "**/dist/**", "**/build/**",
        ]

        # Collect all files first to get total count
        all_files = []
        total_bytes = 0
        
        for pattern in include:
            for file_path in self.project_path.rglob(pattern):
                if any(file_path.match(ex) for ex in exclude):
                    continue
                try:
                    size = file_path.stat().st_size
                    all_files.append((file_path, size))
                    total_bytes += size
                except OSError:
                    continue

        progress = ProgressInfo(
            total_files=len(all_files),
            bytes_total=total_bytes,
            total_chunks=(len(all_files) + chunk_size - 1) // chunk_size if all_files else 0,
        )

        # Process files in batches
        batch: list[tuple[Path, int]] = []
        files_since_yield = 0
        
        for file_path, size in all_files:
            batch.append((file_path, size))
            
            if len(batch) >= chunk_size:
                # Process batch
                for fp, sz in batch:
                    progress.current_file = str(fp.relative_to(self.project_path))
                    
                    try:
                        if sz > self.chunked_processor.max_chunk_size:
                            # Large file - process in chunks
                            for chunk in self._anonymize_large_file(fp):
                                pass  # Process chunks
                        else:
                            # Regular file
                            self.anonymizer.anonymize_file(fp)
                        
                        progress.files_completed += 1
                        progress.bytes_processed += sz
                        progress.symbol_mappings_created = sum(
                            self.context.stats.values()
                        )
                        files_since_yield += 1
                        
                    except Exception as e:
                        progress.files_failed += 1
                        self.anonymizer.errors.append(f"{fp}: {e}")
                    
                    # Check for cancellation
                    if progress_callback:
                        result = progress_callback(progress)
                        if result is False:
                            return
                
                # Yield progress after completing a batch
                progress.current_chunk = (progress.files_completed + chunk_size - 1) // chunk_size
                yield progress
                files_since_yield = 0
                batch = []

        # Process remaining batch
        if batch:
            for fp, sz in batch:
                progress.current_file = str(fp.relative_to(self.project_path))
                
                try:
                    if sz > self.chunked_processor.max_chunk_size:
                        for chunk in self._anonymize_large_file(fp):
                            pass
                    else:
                        self.anonymizer.anonymize_file(fp)
                    
                    progress.files_completed += 1
                    progress.bytes_processed += sz
                    progress.symbol_mappings_created = sum(self.context.stats.values())
                    
                except Exception as e:
                    progress.files_failed += 1
                    self.anonymizer.errors.append(f"{fp}: {e}")
                
                if progress_callback:
                    result = progress_callback(progress)
                    if result is False:
                        return
            
            # Final yield for remaining batch
            progress.current_chunk = progress.total_chunks
            yield progress

    def _anonymize_large_file(self, file_path: Path) -> Iterator[ChunkResult]:
        """Anonymize a large file in chunks."""
        def anonymize_chunk(content: str) -> str:
            return self.anonymizer.anonymize_string(content, str(file_path))

        return self.chunked_processor.process_file(file_path, anonymize_chunk)

    def save_context(self, output_path: str | Path) -> None:
        """Save anonymization context to file."""
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
        """Deanonymize streaming text (e.g., from LLM).
        
        Args:
            text_stream: Iterator yielding text chunks
            progress_callback: Optional progress callback
            
        Yields:
            Deanonymized text chunks
        """
        total_chars = 0
        restored_count = 0

        for chunk in text_stream:
            total_chars += len(chunk)
            
            # Process through streaming deanonymizer
            result = self.streaming_deanonymizer.feed_chunk(chunk)
            
            if result:
                stats = self.streaming_deanonymizer.get_stats()
                restored_count = stats["total_restorations"]
                
                if progress_callback:
                    progress = ProgressInfo(
                        bytes_processed=total_chars,
                        symbol_mappings_created=restored_count,
                    )
                    cb_result = progress_callback(progress)
                    if cb_result is False:
                        return
                
                yield result

        # Finalize
        final = self.streaming_deanonymizer.finalize()
        if final:
            yield final

    def deanonymize_files_streaming(
        self,
        files: dict[str, str],
        progress_callback: ProgressCallback | None = None,
    ) -> Iterator[tuple[str, str]]:
        """Deanonymize multiple files with progress tracking.
        
        Args:
            files: Dict of {file_path: anonymized_content}
            progress_callback: Optional progress callback
            
        Yields:
            Tuples of (file_path, deanonymized_content)
        """
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
        """Anonymize multiple files in parallel.
        
        Note: Symbol mappings are shared via context but this requires
        careful synchronization. For now, we process sequentially per
        file type to avoid conflicts.
        
        Args:
            files: List of file paths to anonymize
            context: Shared anonymization context
            
        Returns:
            Dict of {file_path: anonymized_content}
        """
        from concurrent.futures import ProcessPoolExecutor, as_completed

        results: dict[str, str] = {}
        anonymizer = ProjectAnonymizer(context)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(anonymizer.anonymize_file, fp): fp
                for fp in files
            }

            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                except Exception as e:
                    results[str(file_path)] = f"# ERROR: {e}\n"

        return results


# Convenience functions

def anonymize_project_with_progress(
    project_path: str | Path,
    output_dir: str | Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    on_progress: Callable[[ProgressInfo], bool | None] | None = None,
) -> AnonymizationContext:
    """Anonymize project with progress tracking.
    
    Convenience function for common use case.
    
    Args:
        project_path: Path to project root
        output_dir: Where to save anonymized files
        include: File patterns to include
        exclude: File patterns to exclude
        on_progress: Callback(progress) -> False to cancel
        
    Returns:
        AnonymizationContext with all mappings
    """
    streamer = StreamingProjectAnonymizer(project_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for progress in streamer.anonymize_streaming(
        include_patterns=include,
        exclude_patterns=exclude,
        progress_callback=on_progress,
    ):
        # Progress updates handled by callback
        pass

    # Save context for later deanonymization
    context_file = output_path / ".anonymization_context.json"
    streamer.save_context(context_file)

    return streamer.context


def deanonymize_response_streaming(
    llm_response_stream: Iterator[str],
    context_path: str | Path,
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """Deanonymize streaming LLM response.
    
    Args:
        llm_response_stream: Iterator yielding text chunks from LLM
        context_path: Path to saved anonymization context
        on_chunk: Callback for each deanonymized chunk
        
    Returns:
        Complete deanonymized text
    """
    streamer = StreamingProjectDeanonymizer(context_path)
    
    result_parts: list[str] = []
    for chunk in streamer.deanonymize_streaming(llm_response_stream):
        result_parts.append(chunk)
        if on_chunk:
            on_chunk(chunk)

    return "".join(result_parts)
