# MCP Tool Usage Examples

This directory contains examples of using LLX privacy features via MCP tools.

### `llx_privacy_scan`

Scan text or files for sensitive data.

**Example usage:**
```json
{
  "text": "Contact: john@example.com, API: sk-abcdefghijklmnopqrstuv"
}
```

**Response:**
```json
{
  "findings": {
    "email": ["john@example.com"],
    "api_key": ["sk-abcdefghijklmnopqrstuv"]
  },
  "anonymized": "Contact: [EMAIL_ABCD], API: [APIKEY_1234]",
  "mapping": {
    "[EMAIL_ABCD]": "john@example.com",
    "[APIKEY_1234]": "sk-abcdefghijklmnopqrstuv"
  }
}
```

### `llx_project_anonymize`

Anonymize entire project directory.

**Example usage:**
```json
{
  "path": "/home/user/my-project",
  "output_dir": "/tmp/anonymized",
  "include": ["*.py", "*.js", "*.ts"],
  "exclude": ["**/__pycache__/**", "**/node_modules/**"]
}
```

**Response:**
```json
{
  "success": true,
  "output_dir": "/tmp/anonymized",
  "files_processed": 42,
  "context_file": "/tmp/anonymized/.anonymization_context.json",
  "stats": {
    "variables": 156,
    "functions": 89,
    "classes": 23,
    "modules": 12,
    "paths": 8
  }
}
```

### `llx_project_deanonymize`

Deanonymize LLM response or project files.

**Example usage - LLM response:**
```json
{
  "context_path": "/tmp/anonymized/.anonymization_context.json",
  "text": "Use fn_ABC123 to process data with var_XYZ789"
}
```

**Response:**
```json
{
  "deanonymized_text": "Use process_data to process data with user_input",
  "restorations": 2,
  "confidence": 1.0
}
```

**Example usage - Project files:**
```json
{
  "context_path": "/tmp/anonymized/.anonymization_context.json",
  "input_dir": "/tmp/anonymized",
  "output_dir": "/tmp/restored"
}
```

### Example 1: Anonymize Before Sending to LLM

1. Scan your code for sensitive data:
```bash
# Via MCP tool
{
  "tool": "llx_privacy_scan",
  "arguments": {
    "path": "src/main.py",
    "anonymize": true
  }
}
```

2. Anonymize entire project:
```bash
{
  "tool": "llx_project_anonymize",
  "arguments": {
    "path": "./my-project",
    "output_dir": "./anonymized"
  }
}
```

3. Send anonymized code to LLM
4. Receive anonymized response
5. Deanonymize response:
```bash
{
  "tool": "llx_project_deanonymize",
  "arguments": {
    "context_path": "./anonymized/.anonymization_context.json",
    "text": "<LLM response>"
  }
}
```

### Example 2: Streaming Large Projects

For projects with 100+ files, use streaming mode:

```python
from llx.privacy.streaming import StreamingProjectAnonymizer

streamer = StreamingProjectAnonymizer(project_path)

for progress in streamer.anonymize_streaming(chunk_size=20):
    print(f"{progress.percent}% complete")
```

### Example 3: Custom Patterns

Add custom patterns for your domain:

```python
from llx.privacy import Anonymizer

anon = Anonymizer()
anon.add_pattern(
    name="internal_id",
    regex=r"\bINT-\d{6}\b",
    mask_prefix="[INTID_"
)

result = anon.anonymize(text)
```

## Best Practices

1. **Always save the context file** after anonymization - you'll need it for deanonymization
2. **Use consistent salt** if you need reproducible anonymization
3. **Test your patterns** on sample data before production use
4. **Review anonymized output** to ensure sensitive data is properly masked
5. **Store context files securely** - they contain the mapping to restore original data

## Security Notes

- The `.anonymization_context.json` file contains the reverse mapping
- Keep this file secure and do not commit it to version control
- Add `*.anonymization_context.json` to your `.gitignore`
