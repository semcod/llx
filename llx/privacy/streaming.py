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

from llx.privacy import _streaming_impl as _streaming_impl


AnonymizationContext = _streaming_impl.AnonymizationContext
ProjectAnonymizer = _streaming_impl.ProjectAnonymizer
ProjectAnonymizationResult = _streaming_impl.ProjectAnonymizationResult
SymbolMapping = _streaming_impl.SymbolMapping
ProgressInfo = _streaming_impl.ProgressInfo
ProgressCallback = _streaming_impl.ProgressCallback
ChunkResult = _streaming_impl.ChunkResult
ChunkedProcessor = _streaming_impl.ChunkedProcessor
StreamingProjectAnonymizer = _streaming_impl.StreamingProjectAnonymizer
StreamingProjectDeanonymizer = _streaming_impl.StreamingProjectDeanonymizer
ParallelProjectProcessor = _streaming_impl.ParallelProjectProcessor
anonymize_project_with_progress = _streaming_impl.anonymize_project_with_progress
deanonymize_response_streaming = _streaming_impl.deanonymize_response_streaming

__all__ = list(_streaming_impl.__all__)
