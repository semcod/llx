"""Streaming anonymization example.

Demonstrates handling large files and streaming processing.
"""

import tempfile
from pathlib import Path

from llx.privacy.streaming import StreamingProjectAnonymizer, StreamingProjectDeanonymizer
from llx.privacy.project import AnonymizationContext


def create_large_project(base_path: Path, num_files: int = 50):
    """Create a project with many files for streaming demo."""
    src_dir = base_path / "src"
    src_dir.mkdir()
    
    for i in range(num_files):
        (src_dir / f"module_{i:03d}.py").write_text(f"""
def function_{i}_alpha(data):
    return process_{i}(data)

def function_{i}_beta(items):
    return sum(items)

class Class_{i}:
    def method_{i}_a(self):
        return self.value
    
    def method_{i}_b(self, x):
        return x * {i}
""")


def main():
    print("=" * 70)
    print("LLX Privacy: Streaming Anonymization Example")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "large_project"
        project_path.mkdir()
        
        # Create large project
        print("\n1. CREATING LARGE PROJECT (100 files)")
        print("-" * 40)
        create_large_project(project_path, num_files=100)
        print(f"Created {len(list(project_path.rglob('*.py')))} Python files")
        
        # Streaming anonymization with progress
        print("\n2. STREAMING ANONYMIZATION")
        print("-" * 40)
        print("Processing with progress updates...\n")
        
        streamer = StreamingProjectAnonymizer(project_path)
        
        def progress_callback(progress):
            """Called for each progress update."""
            if progress.files_completed % 10 == 0:
                print(f"  Progress: {progress.files_completed}/{progress.total_files} files "
                      f"({progress.percent:.1f}%)")
            return True  # Continue processing
        
        # Process in chunks of 10 files
        for update in streamer.anonymize_streaming(
            include_patterns=["*.py"],
            chunk_size=10,
            progress_callback=progress_callback,
        ):
            pass  # Progress handled by callback
        
        # Save context
        context_path = project_path / "context.json"
        streamer.save_context(context_path)
        
        ctx = streamer.context
        print(f"\nCompleted!")
        print(f"  Total symbols: {sum(ctx.stats.values())}")
        print(f"  Variables: {len(ctx.variables)}")
        print(f"  Functions: {len(ctx.functions)}")
        print(f"  Classes: {len(ctx.classes)}")
        
        # Simulate streaming LLM response
        print("\n3. STREAMING DEANONYMIZATION")
        print("-" * 40)
        print("Simulating chunked LLM response...\n")
        
        # Get some anonymized names
        func_names = list(ctx.functions.keys())[:3]
        anon_names = [ctx.functions[f].anonymized for f in func_names]
        
        # Simulate chunked response
        llm_chunks = [
            f"To optimize {anon_names[0]}, ",
            f"consider refactoring {anon_names[1]} ",
            f"and updating {anon_names[2]}.",
        ]
        
        # Stream deanonymize
        deanon_streamer = StreamingProjectDeanonymizer(ctx)
        
        print("Chunks received:")
        full_response = ""
        for i, chunk in enumerate(llm_chunks):
            result = deanon_streamer.deanonymize_streaming(iter([chunk]))
            for deanon_chunk in result:
                print(f"  Chunk {i+1}: '{deanon_chunk}'")
                full_response += deanon_chunk
        
        print(f"\nFull deanonymized response:")
        print(f"  {full_response}")
        
        # Show stats
        stats = deanon_streamer.streaming_deanonymizer.get_stats()
        print(f"\nStreaming stats:")
        print(f"  Total restorations: {stats['total_restorations']}")
        print(f"  Unique symbols: {stats['unique_symbols_restored']}")
        
        print("\n" + "=" * 70)
        print("Streaming example complete!")
        print("=" * 70)


if __name__ == "__main__":
    main()
