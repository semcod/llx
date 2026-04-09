"""Parallel file processing helpers for streaming anonymization."""

from __future__ import annotations

import os
from pathlib import Path

from llx.privacy._project_context import AnonymizationContext
from llx.privacy._project_anonymizer import ProjectAnonymizer


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
