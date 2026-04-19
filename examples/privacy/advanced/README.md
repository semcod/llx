# Advanced Privacy Examples

This directory contains advanced, real-world examples demonstrating LLX privacy features in complex scenarios.

### 1. API Integration (`01_api_integration.py`)

**Complexity**: ⭐⭐⭐⭐⭐

Demonstrates complete workflow with simulated LLM API:
- Creates realistic e-commerce project with payment processing
- Integrates Stripe API with live keys (simulated)
- Handles PESEL (Polish national ID) and credit cards
- Simulates LLM API request/response cycle
- Shows round-trip anonymization → LLM → deanonymization

**Run**:
```bash
python3 01_api_integration.py
```

**What you'll see**:
```
1. Creating e-commerce project with sensitive data
2. Project structure with config, models, services
3. Detected secrets: API keys, passwords, PESEL
4. Anonymization: 6 files, 55 variables, 18 functions
5. Simulated LLM API call with anonymized code
6. Deanonymized response with original names restored
```

### 2. Multi-Stage Anonymization (`02_multi_stage.py`)

**Complexity**: ⭐⭐⭐⭐

Demonstrates different anonymization levels for different audiences:
- **Level 1: Internal** - Minimal anonymization (secrets only)
- **Level 2: Contractor** - Moderate (AST + secrets)
- **Level 3: Public** - Full anonymization

**Run**:
```bash
python3 02_multi_stage.py
```

**What you'll see**:
```
Level 1 (Internal):     0 symbols - code names preserved
Level 2 (Contractor):   45 symbols - AST + secrets
Level 3 (Public):       45 symbols - full protection

Comparison showing variables/functions/classes per level
```

**Use cases**:
- Internal code review (minimal changes)
- External consultants with NDA (moderate)
- Public forums/LLMs (maximum protection)

### 3. CI/CD Integration (`03_cicd_integration.py`)

**Complexity**: ⭐⭐⭐⭐⭐

Demonstrates integrating privacy into CI/CD pipeline:
- Pre-commit security scanning
- Pre-deployment anonymization
- External security audit workflow
- Automated report generation

**Run**:
```bash
python3 03_cicd_integration.py
```

**What you'll see**:
```
Step 1: Pre-commit scan - detects hardcoded secrets
Step 2: Anonymize for external audit
Step 3: Simulate audit findings with deanonymization
Step 4: Generate compliance report

Integration points for:
- Git pre-commit hooks
- GitHub Actions
- GitLab CI
- Pre-deployment checks
```

## Project Structure Created

Each example creates realistic project structures:

```
ecommerce_platform/           (01_api_integration)
├── config/
│   └── production.yaml        # Database credentials, API keys
├── src/
│   ├── main.py              # Application entry
│   ├── models/
│   │   └── user.py          # PESEL, email, phone
│   ├── services/
│   │   └── payment_service.py  # Stripe integration
│   └── utils/
│       └── helpers.py       # System paths
└── tests/
    └── test_payment.py

business_platform/            (02_multi_stage)
├── src/
│   ├── pricing_engine.py    # Proprietary algorithms
│   └── customer_data.py     # PII handling

webapp/                       (03_cicd_integration)
├── src/app/
│   ├── database.py          # Hardcoded credentials (BAD)
│   ├── customer.py          # SSN, credit cards
│   └── utils.py             # Clean code (GOOD)
└── config/
    └── secrets.yaml         # Production secrets
```

### Credentials
- Stripe API keys (`sk_live_...`)
- Database passwords
- AWS access/secret keys
- SendGrid API keys

### Personal Information (PII)
- Email addresses
- Phone numbers
- PESEL (Polish national ID)
- US Social Security Numbers
- Credit card numbers

### System Information
- Internal hostnames
- Database connection strings
- File paths (`/home/...`, `/var/log/...`)
- Internal API endpoints

### Proprietary Business Logic
- Pricing algorithms
- Margin calculations
- Discount tiers
- Competitor monitoring

# SimulatedLLMAPI class demonstrates:
class SimulatedLLMAPI:
    def send_prompt(self, anonymized_code: str, prompt: str) -> SimulatedLLMResponse:
        # 1. LLM receives only anonymized code (fn_*, var_*)
        # 2. LLM generates suggestions using anonymized names
        # 3. Response is deanonymized before human review
```

# Different protection levels:
levels = {
    "internal": {      # Trust: high → minimal changes
        "enable_ast": False,
        "enable_content": True,
    },
    "contractor": {    # Trust: medium → moderate changes
        "enable_ast": True,
        "enable_content": True,
    },
    "public": {       # Trust: low → maximum protection
        "enable_ast": True,
        "enable_content": True,
    }
}
```

### 3. CI/CD Pipeline Stages

```python
class CICDPrivacyPipeline:
    def step1_pre_commit_scan(self) -> bool:
        # Scan for secrets before allowing commit
        
    def step2_anonymize_for_audit(self, output_dir: Path) -> Path:
        # Create anonymized package for external auditors
        
    def step3_simulate_audit_response(self, findings: str) -> str:
        # Deanonymize audit findings
        
    def step4_generate_report(self, output_path: Path) -> None:
        # Generate compliance report
```

## Comparison with Basic Examples

| Feature | Basic | Advanced |
|---------|-------|----------|
| Code complexity | Simple snippets | Realistic projects |
| Sensitive data | Examples only | Production-like secrets |
| Use case | Learning | Real-world workflows |
| Audience | Individual dev | Teams, CI/CD |
| Integration | Standalone | CI/CD, APIs |
| AST transformation | Basic | Full project |
| Multi-stage | No | Yes (3 levels) |
| Simulated APIs | No | Yes (LLM API) |

## Running All Examples

```bash
cd /home/tom/github/semcod/llx/examples/privacy

# Basic examples
python3 basic/01_text_anonymization.py
python3 basic/02_custom_patterns.py

# Project examples
python3 project/01_anonymize_project.py
python3 project/02_deanonymize_project.py

# Streaming examples
python3 streaming/01_streaming_anonymization.py

# Advanced examples
python3 advanced/01_api_integration.py
python3 advanced/02_multi_stage.py
python3 advanced/03_cicd_integration.py
```

# .git/hooks/pre-commit
#!/bin/bash
python3 << 'EOF'
from llx.privacy import Anonymizer
import sys

anon = Anonymizer()
for file in sys.argv[1:]:
    content = open(file).read()
    findings = anon.scan(content)
    if 'password' in findings or 'api_key' in findings:
        print(f"❌ Secrets found in {file}")
        sys.exit(1)
EOF
```

# 1. Anonymize for external audit
ctx = AnonymizationContext(project_path=".")
anonymizer = ProjectAnonymizer(ctx)
result = anonymizer.anonymize_project()
ctx.save("audit_context.json")

# 3. Receive anonymized findings
findings = "Function fn_ABC123 has security issue..."

# 4. Deanonymize for internal team
deanonymizer = ProjectDeanonymizer(ctx)
restored = deanonymizer.deanonymize_text(findings)
# Before sending to LLM
ctx = AnonymizationContext(project_path=".")
anonymizer = ProjectAnonymizer(ctx)
result = anonymizer.anonymize_project()

# Send anonymized_code to LLM API
llm_response = call_llm_api(result.files["main.py"])

# Deanonymize response
deanonymizer = ProjectDeanonymizer(ctx)
clean_response = deanonymizer.deanonymize_chat_response(llm_response)
```

## Security Considerations

⚠️ **These examples demonstrate what NOT to do**:
- Hardcoding secrets in source code
- Storing production credentials in config files
- Returning sensitive data in API responses

✅ **Best practices demonstrated**:
- Detecting secrets before commit
- Anonymizing before external sharing
- Using environment variables (utils.py example)
- Proper deanonymization workflow

# All examples require
pip install -e /path/to/llx

# Optional (for AST code generation)
pip install astor
```

## Output Files

Examples create temporary directories that are automatically cleaned up. In real usage, you would:

1. Save context files securely (not in git)
2. Store anonymized packages for audit trail
3. Generate reports for compliance

```gitignore
# .gitignore
*.anonymization_context.json
*.audit_context.json
audit_package/
security_report.json
```

## Next Steps

1. **Understand basics**: Run basic examples first
2. **Explore advanced**: Run these examples to see real-world patterns
3. **Adapt to your project**: Modify examples for your use case
4. **Integrate into CI/CD**: Use patterns from `03_cicd_integration.py`
5. **Read documentation**: See `../../docs/PRIVACY.md` for full API reference

## Support

- Full API docs: `../../docs/PRIVACY.md`
- Basic examples: `../basic/` and `../project/`
- MCP tools: `../mcp/README.md`
- Tests: `../../../tests/test_privacy*.py`
