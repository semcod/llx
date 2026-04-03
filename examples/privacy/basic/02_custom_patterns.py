"""Custom pattern example.

Demonstrates adding custom anonymization patterns.
"""

from llx.privacy import Anonymizer


def main():
    print("=" * 60)
    print("LLX Privacy: Custom Pattern Example")
    print("=" * 60)
    
    # Create anonymizer with custom patterns
    anon = Anonymizer()
    
    # Add custom patterns for specific use cases
    # Pattern for internal project codes (e.g., PRJ-1234)
    anon.add_pattern(
        name="project_code",
        regex=r"\bPRJ-\d{4}\b",
        mask_prefix="[PROJECT_",
    )
    
    # Pattern for employee IDs
    anon.add_pattern(
        name="employee_id",
        regex=r"\bEMP\d{5}\b",
        mask_prefix="[EMPLOYEE_",
    )
    
    # Pattern for database connection strings
    anon.add_pattern(
        name="db_connection",
        regex=r"postgresql://[^\s]+",
        mask_prefix="[DBCONN_",
    )
    
    # Example text
    text = """
    Project Details:
    - Project Code: PRJ-2045
    - Lead: EMP12345 (John Doe)
    
    Database:
    - Connection: postgresql://user:pass@db.internal:5432/production
    
    Contact:
    - Email: john.doe@company.com
    - Phone: +1 555 123 4567
    """
    
    print("\n1. ORIGINAL TEXT:")
    print("-" * 40)
    print(text)
    
    # Scan for sensitive data
    print("\n2. SCANNING FOR SENSITIVE DATA:")
    print("-" * 40)
    
    findings = anon.scan(text)
    for pattern_name, matches in findings.items():
        print(f"\n{pattern_name}:")
        for match in matches:
            print(f"  - {match}")
    
    # Anonymize
    print("\n3. ANONYMIZING:")
    print("-" * 40)
    
    result = anon.anonymize(text)
    print(result.text)
    
    print("\n4. RESTORING ORIGINAL VALUES:")
    print("-" * 40)
    
    restored = anon.deanonymize(result.text, result.mapping)
    print(restored)
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
