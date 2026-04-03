"""Basic text anonymization example.

Demonstrates simple anonymization of sensitive data in text.
"""

from llx.privacy import quick_anonymize, quick_deanonymize


def main():
    print("=" * 60)
    print("LLX Privacy: Basic Text Anonymization Example")
    print("=" * 60)
    
    # Example text with various sensitive data
    original_text = """
    Contact Information:
    - Name: John Doe
    - Email: john.doe@example.com
    - Phone: +48 123 456 789
    - PESEL: 90010112345
    
    API Credentials:
    - API Key: sk-abcdefghijklmnopqrstuv
    - Password: mySecretPassword123
    
    System Info:
    - Server: prod-server-01.internal.company.com
    - Path: /home/johndoe/project/config
    - IP: 192.168.1.100
    """
    
    print("\n1. ORIGINAL TEXT:")
    print("-" * 40)
    print(original_text)
    
    # Anonymize
    print("\n2. ANONYMIZING...")
    print("-" * 40)
    
    result = quick_anonymize(original_text)
    
    print(f"Anonymized text:")
    print(result.text)
    
    print(f"\nMapping (for deanonymization):")
    for token, original in result.mapping.items():
        print(f"  {token} -> {original}")
    
    print(f"\nStatistics:")
    for pattern_type, count in result.stats.items():
        print(f"  {pattern_type}: {count} found")
    
    # Simulate LLM response (referencing anonymized tokens)
    print("\n3. SIMULATED LLM RESPONSE:")
    print("-" * 40)
    
    llm_response = f"""
    I've reviewed your configuration. The email [EMAIL_...] should be verified.
    The API key starting with sk-... should be rotated immediately.
    Consider moving the config from /home/... to a standard location.
    """
    print(llm_response)
    
    # Deanonymize LLM response
    print("\n4. DEANONYMIZED RESPONSE:")
    print("-" * 40)
    
    restored = quick_deanonymize(llm_response, result.mapping)
    print(restored)
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
