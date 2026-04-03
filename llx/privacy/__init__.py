"""Privacy protection module for LLX — anonymization and deanonymization.

This module provides reversible anonymization of sensitive data before sending
to LLM APIs, and restores original values in responses.

Supported sensitive data types:
- Credentials (passwords, API keys, tokens, secrets)
- Personal Information (emails, phone numbers, names, addresses)
- Financial data (credit cards, bank accounts, IBAN)
- System data (file paths, hostnames, IP addresses)
- Custom patterns via configuration

Project-level features (llx.privacy.project, llx.privacy.deanonymize, llx.privacy.streaming):
- AST-based code anonymization (variables, functions, classes)
- File structure anonymization (paths, imports)
- Project-wide symbol mapping and context
- Streaming/chunked processing for large projects
- Full round-trip anonymization/deanonymization

Quick usage:
    from llx.privacy import quick_anonymize, quick_deanonymize
    
    # Simple text anonymization
    result = quick_anonymize("Contact john@example.com")
    print(result.text)  # "Contact [EMAIL_1]"
    
    # Project-level
    from llx.privacy.project import ProjectAnonymizer, AnonymizationContext
    ctx = AnonymizationContext("/path/to/project")
    anon = ProjectAnonymizer(ctx)
    result = anon.anonymize_project()
    
    # Deanonymize LLM response
    from llx.privacy.deanonymize import ProjectDeanonymizer
    deanonymizer = ProjectDeanonymizer(ctx)
    restored = deanonymizer.deanonymize_chat_response(llm_response)
"""

from __future__ import annotations

from llx.privacy.__core import (
    AnonymizationPattern,
    AnonymizationResult,
    Anonymizer,
    quick_anonymize,
    quick_deanonymize,
)

__all__ = [
    # Core anonymization
    "Anonymizer",
    "AnonymizationResult",
    "AnonymizationPattern",
    "quick_anonymize",
    "quick_deanonymize",
]
