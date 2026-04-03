# LLX Privacy Examples

This directory contains examples demonstrating LLX's privacy and anonymization features.

## Directory Structure

```
privacy/
├── basic/          # Simple text anonymization examples
├── project/        # Project-level code anonymization
├── streaming/      # Large project and streaming examples
└── mcp/            # MCP tool usage documentation
```

## Quick Start

### 1. Basic Text Anonymization

```bash
cd basic
python 01_text_anonymization.py
```

Demonstrates:
- Anonymizing emails, API keys, passwords
- Viewing anonymization mapping
- Deanonymizing LLM responses

### 2. Custom Patterns

```bash
cd basic
python 02_custom_patterns.py
```

Demonstrates:
- Adding custom detection patterns
- Scanning without anonymizing
- Selective pattern application

### 3. Project Anonymization

```bash
cd project
python 01_anonymize_project.py
```

Demonstrates:
- AST-based code transformation
- Anonymizing variables, functions, classes
- Saving anonymization context
- Viewing symbol mappings

### 4. Project Deanonymization

```bash
cd project
python 02_deanonymize_project.py
```

Demonstrates:
- Loading saved context
- Deanonymizing LLM responses
- Restoring original code
- Symbol information lookup

### 5. Streaming Large Projects

```bash
cd streaming
python 01_streaming_anonymization.py
```

Demonstrates:
- Progress tracking for large projects
- Chunked processing
- Streaming LLM response deanonymization

## Common Workflows

### Workflow 1: Anonymize Before LLM

```python
from llx.privacy.project import AnonymizationContext, ProjectAnonymizer

# 1. Create context
ctx = AnonymizationContext(project_path="./my-project")

# 2. Anonymize
anonymizer = ProjectAnonymizer(ctx)
result = anonymizer.anonymize_project()

# 3. Save context
ctx.save("./my-project.anon.json")

# 4. Send anonymized code to LLM...
# 5. Receive anonymized response...

# 6. Deanonymize response
from llx.privacy.deanonymize import ProjectDeanonymizer
deanonymizer = ProjectDeanonymizer(ctx)
restored = deanonymizer.deanonymize_chat_response(llm_response)
```

### Workflow 2: Quick Text Anonymization

```python
from llx.privacy import quick_anonymize, quick_deanonymize

# Anonymize
result = quick_anonymize("Email: user@example.com")

# Later...
restored = quick_deanonymize(llm_response, result.mapping)
```

### Workflow 3: Streaming for Large Projects

```python
from llx.privacy.streaming import StreamingProjectAnonymizer

streamer = StreamingProjectAnonymizer("./large-project")

for progress in streamer.anonymize_streaming(chunk_size=50):
    print(f"{progress.percent:.1f}% complete")
    print(f"Files: {progress.files_completed}/{progress.total_files}")
```

## MCP Tool Examples

See `mcp/README.md` for MCP tool usage examples with JSON requests/responses.

## Documentation

Full documentation: `../../docs/PRIVACY.md`

## Requirements

All examples require:
```bash
pip install -e /path/to/llx
```

Some examples may require additional packages:
```bash
pip install astor  # For AST code generation (optional)
```

## Output

Each example prints:
- Original content
- Anonymized content
- Mapping information
- Deanonymized result
- Statistics and progress

Run any example to see detailed output with explanations.

## Support

For issues or questions:
1. Check full documentation in `docs/PRIVACY.md`
2. Review test files in `tests/test_privacy*.py`
3. See source code in `llx/privacy/`
