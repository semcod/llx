"""Chunking and progress primitives for streaming anonymization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Protocol

DEFAULT_INCLUDE_PATTERNS = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"]
DEFAULT_EXCLUDE_PATTERNS = [
    "**/.git/**",
    "**/venv/**",
    "**/.venv/**",
    "**/node_modules/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    "**/*.pyc",
    "**/.llx/**",
    "**/dist/**",
    "**/build/**",
]


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
    """Process large files in chunks to manage memory usage."""

    def __init__(self, max_chunk_size: int = 1024 * 1024):
        self.max_chunk_size = max_chunk_size

    def process_file(
        self,
        file_path: str | Path,
        anonymizer_func: Callable[[str], str],
    ) -> Iterator[ChunkResult]:
        file_path = Path(file_path)
        file_size = file_path.stat().st_size

        if file_size <= self.max_chunk_size:
            yield self._process_small_file(file_path, anonymizer_func)
            return

        yield from self._split_and_process(file_path, anonymizer_func)

    def _process_small_file(
        self,
        file_path: Path,
        anonymizer_func: Callable[[str], str],
    ) -> ChunkResult:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        anonymized = anonymizer_func(content)
        return ChunkResult(content=anonymized, chunk_number=1, is_complete=True)

    def _split_and_process(
        self,
        file_path: Path,
        anonymizer_func: Callable[[str], str],
    ) -> Iterator[ChunkResult]:
        chunk_num = 0
        buffer = ""
        buffer_size = 0

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_size = len(line.encode("utf-8"))

                if line_size > self.max_chunk_size:
                    if buffer:
                        chunk_num += 1
                        anonymized = anonymizer_func(buffer)
                        yield ChunkResult(content=anonymized, chunk_number=chunk_num, is_complete=False)
                        buffer = ""
                        buffer_size = 0

                    line_bytes = line.encode("utf-8")
                    for i in range(0, len(line_bytes), self.max_chunk_size):
                        chunk_bytes = line_bytes[i:i + self.max_chunk_size]
                        chunk_str = chunk_bytes.decode("utf-8", errors="replace")
                        chunk_num += 1
                        anonymized = anonymizer_func(chunk_str)
                        yield ChunkResult(content=anonymized, chunk_number=chunk_num, is_complete=False)
                    continue

                if buffer_size + line_size > self.max_chunk_size and buffer:
                    chunk_num += 1
                    anonymized = anonymizer_func(buffer)
                    yield ChunkResult(content=anonymized, chunk_number=chunk_num, is_complete=False)
                    buffer = line
                    buffer_size = line_size
                else:
                    buffer += line
                    buffer_size += line_size

            if buffer:
                chunk_num += 1
                anonymized = anonymizer_func(buffer)
                yield ChunkResult(content=anonymized, chunk_number=chunk_num, is_complete=True)
