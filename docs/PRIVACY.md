## Overview

The LLX Privacy module provides **reversible anonymization** of sensitive data for secure communication with LLM APIs. It supports both simple text anonymization and complex project-level code anonymization with AST transformation.

### Core Features
- **Text anonymization**: Emails, phone numbers, API keys, passwords, PESEL, credit cards
- **Project-level anonymization**: AST-based code transformation (variables, functions, classes)
- **Full round-trip**: Anonymize → Send to LLM → Receive response → Deanonymize
- **Persistent mapping**: Save/restore anonymization context
- **Streaming support**: Handle large projects efficiently

### Supported Data Types

| Category | Patterns | Example |
|----------|----------|---------|
| Credentials | API keys, tokens, passwords, secrets | `sk-...`, `password: ...` |
| Personal | Emails, phones, PESEL | `user@example.com`, `+48 123 456 789` |
| Financial | Credit cards | `1234-5678-9012-3456` |
| System | Paths, IPs, hostnames | `/home/user`, `192.168.1.1` |
| Code | Variables, functions, classes | `def process_data():` |

### Basic Text Anonymization

```python
from llx.privacy import quick_anonymize, quick_deanonymize

# Anonymize
result = quick_anonymize("Contact: admin@company.com, API: sk-abc123")
print(result.text)
# Deanonymize LLM response
restored = quick_deanonymize(llm_response, result.mapping)
```

### Project-Level Anonymization

```python
from llx.privacy.project import AnonymizationContext, ProjectAnonymizer

# Create context
ctx = AnonymizationContext(project_path="/path/to/project")

# Anonymize
anonymizer = ProjectAnonymizer(ctx)
result = anonymizer.anonymize_project()

# Save context for later
ctx.save("/path/to/context.json")
```

### Deanonymization

```python
from llx.privacy.deanonymize import ProjectDeanonymizer
from llx.privacy.project import AnonymizationContext

# Load context
ctx = AnonymizationContext.load("/path/to/context.json")

# Deanonymize
deanonymizer = ProjectDeanonymizer(ctx)
restored = deanonymizer.deanonymize_chat_response(llm_response)
```

#### `Anonymizer`

Main class for text-based anonymization.

```python
from llx.privacy import Anonymizer

anon = Anonymizer(
    salt="my_salt",  # Optional: for reproducible tokens
    max_length=50,   # Max length of stored values
)

# Anonymize
result = anon.anonymize("text with sensitive data")

# Scan without anonymizing
findings = anon.scan(text)

# Add custom pattern
anon.add_pattern(
    name="project_id",
    regex=r"\bPRJ-\d{4}\b",
    mask_prefix="[PROJECT_",
)
```

#### `AnonymizationContext`

Manages project-wide symbol mappings.

```python
from llx.privacy.project import AnonymizationContext

ctx = AnonymizationContext(project_path="/path/to/project")

# Get or create symbol
anon_name = ctx.get_or_create_symbol(
    original="my_function",
    symbol_type="function",
    file_path="module.py",
    line_number=42,
    scope="MyClass",
)

# Save/Load
ctx.save("context.json")
ctx = AnonymizationContext.load("context.json")
```

#### `ProjectAnonymizer`

Anonymizes entire projects.

```python
from llx.privacy.project import ProjectAnonymizer

anonymizer = ProjectAnonymizer(context=ctx)

# Anonymize entire project
result = anonymizer.anonymize_project(
    include_patterns=["*.py", "*.js"],
    exclude_patterns=["**/node_modules/**"],
    max_file_size=10*1024*1024,  # 10MB
)

# Access anonymized files
for file_path, content in result.files.items():
    print(f"{file_path}: {len(content)} chars")
```

#### `ProjectDeanonymizer`

Restores original values.

```python
from llx.privacy.deanonymize import ProjectDeanonymizer

deanonymizer = ProjectDeanonymizer(context=ctx)

# Deanonymize text
result = deanonymizer.deanonymize_text(anonymized_text)
print(result.text)           # Restored text
print(result.restorations)   # List of (token, original) tuples
print(result.confidence)     # Ratio of tokens restored

# Deanonymize multiple files
files_result = deanonymizer.deanonymize_project_files(
    anonymized_files={"main.py": "def fn_ABC(): pass"},
    output_dir="/restored",
)

# Quick method
restored = deanonymizer.deanonymize_chat_response(llm_response)
```

#### `StreamingProjectAnonymizer`

For large projects with progress tracking.

```python
from llx.privacy.streaming import StreamingProjectAnonymizer

streamer = StreamingProjectAnonymizer(project_path)

# Process with progress updates
for progress in streamer.anonymize_streaming(
    chunk_size=20,  # Files per batch
):
    print(f"{progress.percent}% complete")
    print(f"Files: {progress.files_completed}/{progress.total_files}")
```

#### `StreamingDeanonymizer`

For streaming LLM responses.

```python
from llx.privacy.deanonymize import StreamingDeanonymizer

streamer = StreamingDeanonymizer(context=ctx)

# Process chunks as they arrive
for chunk in llm_response_stream:
    result = streamer.feed_chunk(chunk)
    if result:
        print(result)  # Deanonymized chunk

# Finalize
final = streamer.finalize()
```

## MCP Tools

The privacy module exposes MCP tools for integration:

### `llx_privacy_scan`

Scan text or files for sensitive data.

```json
{
  "text": "Email: user@example.com",
  "anonymize": true
}
```

### `llx_project_anonymize`

Anonymize entire project.

```json
{
  "path": "./my-project",
  "output_dir": "./anonymized",
  "include": ["*.py", "*.js"],
  "exclude": ["**/node_modules/**"]
}
```

### `llx_project_deanonymize`

Deanonymize using saved context.

```json
{
  "context_path": "./anonymized/.anonymization_context.json",
  "text": "<LLM response with anonymized tokens>"
}
```

## Examples

See `examples/privacy/` for complete examples:

### Basic Examples
- `basic/01_text_anonymization.py` - Simple text anonymization
- `basic/02_custom_patterns.py` - Custom patterns for domain-specific data

### Project-Level Examples
- `project/01_anonymize_project.py` - Project-level anonymization with AST transformation
- `project/02_deanonymize_project.py` - Deanonymization workflow

### Streaming Examples
- `streaming/01_streaming_anonymization.py` - Large project handling with progress tracking

### ML-Based Detection Examples
- `ml/01_entropy_ml_detection.py` - Entropy-based password detection
- `ml/02_hybrid_system.py` - Combined regex + ML detection
- `ml/03_contextual_passwords.py` - NLP-based password detection
- `ml/04_behavioral_learning.py` - Learning from user feedback

### MCP Integration
- `mcp/README.md` - MCP tool usage and JSON-RPC examples

# After anonymization
ctx.save("project.anon.json")

# Later, for deanonymization
ctx = AnonymizationContext.load("project.anon.json")
```

# Same salt = same anonymized names
ctx = AnonymizationContext(
    project_path="/project",
    salt="my_project_salt_2024"
)
```

### 3. Review Before Sending

```python
result = anonymizer.anonymize_project()

# Check what was anonymized
print(f"Variables: {len(ctx.variables)}")
print(f"Functions: {len(ctx.functions)}")

# Review a sample file
print(result.files["main.py"][:1000])
```

# For very large responses
streamer = StreamingDeanonymizer(ctx)

for chunk in llm_response_stream:
    result = streamer.feed_chunk(chunk)
    yield result  # Yield deanonymized chunks

# Don't forget to finalize
final = streamer.finalize()
if final:
    yield final
```

# .gitignore
*.anonymization_context.json
*.anon.json
```

### Text Anonymization Tokens

| Pattern | Token Format | Example |
|---------|---------------|---------|
| Email | `[EMAIL_XXXX]` | `[EMAIL_A1B2]` |
| API Key | `[APIKEY_XXXX]` | `[APIKEY_C3D4]` |
| Phone | `[PHONE_XXXX]` | `[PHONE_E5F6]` |
| Password | `[PASSWORD_XXXX]` | `[PASSWORD_G7H8]` |
| PESEL | `[PESEL_XXXX]` | `[PESEL_I9J0]` |

### Project Anonymization Tokens

| Symbol Type | Token Format | Example |
|-------------|--------------|---------|
| Variable | `var_XXXXXX` | `var_a1b2c3` |
| Function | `fn_XXXXXX` | `fn_d4e5f6` |
| Class | `cls_XXXXXX` | `cls_g7h8i9` |
| Module | `mod_XXXXXX` | `mod_j0k1l2` |
| Path | `pth_XXXXXX` | `pth_m3n4o5` |

### Custom AST Transformation

```python
from llx.privacy.project import ASTAnonymizer
import ast

# Parse code
tree = ast.parse("def foo(): pass")

# Transform
transformer = ASTAnonymizer(ctx, "file.py")
result = transformer.visit(tree)

# Generate code
import astor
new_code = astor.to_source(result)
```

### Selective Pattern Enable/Disable

```python
anon = Anonymizer()

# Disable specific patterns
anon.disable_pattern("phone")
anon.disable_pattern("email")

# Enable later
anon.enable_pattern("email")
```

### Chunked Processing

```python
from llx.privacy.streaming import ChunkedProcessor

processor = ChunkedProcessor(max_chunk_size=1024*1024)  # 1MB

for chunk in processor.process_file("large_file.py", anonymize_func):
    process(chunk.content)
```

### Issue: AST parsing fails for Python file

**Solution**: Falls back to regex-based anonymization automatically.

### Issue: Symbols not consistently anonymized across files

**Solution**: Use single `AnonymizationContext` for all files in project.

### Issue: Tokens not restored in deanonymization

**Check**:
1. Context file loaded correctly
2. Same salt used for anonymization
3. Token format matches (check prefixes)

### Issue: Large project runs slowly

**Solution**: Use `StreamingProjectAnonymizer` with chunked processing.

## Security Considerations

1. **Context files contain reverse mappings** - treat as sensitive data
2. **Salt affects token generation** - keep consistent but secure
3. **Anonymized data is not encrypted** - only obfuscated
4. **Review output** before sending to ensure complete anonymization

## Performance

- **Small files (< 1MB)**: Instant processing
- **Medium projects (< 100 files)**: ~1-5 seconds
- **Large projects (1000+ files)**: Use streaming mode
- **Chunked processing**: Handles files of any size

## Contributing

See `tests/test_privacy*.py` for comprehensive test coverage.

## License

Part of LLX - see main project LICENSE.
