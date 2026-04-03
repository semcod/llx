"""Tests for privacy/anonymization module."""

import pytest

from llx.privacy import Anonymizer, AnonymizationResult, quick_anonymize, quick_deanonymize


class TestAnonymizationPatterns:
    """Test detection and masking of sensitive data patterns."""

    def test_email_anonymization(self):
        """Email addresses should be masked with tokens."""
        text = "Contact john.doe@example.com for support."
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert "john.doe@example.com" not in result.text
        assert "[EMAIL_" in result.text
        assert result.mapping
        assert any("@example.com" in v for v in result.mapping.values())

    def test_api_key_anonymization(self):
        """API keys should be masked with tokens."""
        text = "API key: sk-abcdefghijklmnopqrstuv"  # 12+ chars after sk-
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert "sk-abcdefghijklmnopqrstuv" not in result.text
        assert "[APIKEY_" in result.text
        assert result.mapping

    def test_password_anonymization(self):
        """Passwords should be masked with tokens."""
        text = "password: mySecretPassword123"
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert "mySecretPassword123" not in result.text
        assert "[PASSWORD_" in result.text

    def test_phone_anonymization(self):
        """Phone numbers should be masked with tokens."""
        text = "Call me at +1 (555) 123-4567"
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert "(555) 123-4567" not in result.text
        assert "[PHONE_" in result.text

    def test_pesel_anonymization(self):
        """Polish PESEL numbers should be masked."""
        text = "PESEL: 90010112345"  # Valid format: YYMMDDXXXXX
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert "90010112345" not in result.text
        assert "[PESEL_" in result.text

    def test_multiple_sensitive_data_types(self):
        """Multiple sensitive data types should all be masked."""
        text = """
        Contact: admin@company.com
        API Key: sk-abc123def456ghi789jkl012
        Password: secret123
        Phone: +48 123 456 789
        """
        anon = Anonymizer()
        result = anon.anonymize(text)

        # Check all sensitive data is masked
        assert "admin@company.com" not in result.text
        assert "sk-abc123def456ghi789jkl012" not in result.text
        assert "secret123" not in result.text
        assert "123 456 789" not in result.text

        # Check tokens exist
        assert "[EMAIL_" in result.text
        assert "[APIKEY_" in result.text
        assert "[PASSWORD_" in result.text
        assert "[PHONE_" in result.text

        # Stats should track each pattern
        assert result.stats.get("email", 0) >= 1
        assert result.stats.get("api_key", 0) >= 1
        assert result.stats.get("password", 0) >= 1


class TestDeanonymization:
    """Test restoring original values from anonymized text."""

    def test_simple_deanonymization(self):
        """Should restore original email from anonymized text."""
        original = "Email: john@example.com"
        anon = Anonymizer()
        result = anon.anonymize(original)

        # Anonymized text should not have original email
        assert "john@example.com" not in result.text

        # Deanonymize and check original is restored
        restored = result.deanonymize(result.text)
        assert "john@example.com" in restored

    def test_deanonymization_roundtrip(self):
        """Full roundtrip: anonymize then deanonymize should restore original."""
        original = "API: sk-123456789 Contact: user@example.com"
        anon = Anonymizer()
        result = anon.anonymize(original)

        restored = result.deanonymize(result.text)
        assert restored == original

    def test_deanonymization_with_new_text(self):
        """Deanonymize should work on new text containing tokens."""
        original = "Email: admin@company.com"
        anon = Anonymizer()
        result = anon.anonymize(original)

        # Create new text with tokens
        llm_response = f"I sent an email to {result.text.split(': ')[1]}"

        # Deanonymize the LLM response
        restored = result.deanonymize(llm_response)
        assert "admin@company.com" in restored

    def test_empty_mapping_deanonymization(self):
        """Deanonymization with empty mapping should return unchanged."""
        anon = Anonymizer()
        text = "No sensitive data here"
        result = anon.anonymize(text)

        # No changes made
        restored = result.deanonymize(result.text)
        assert restored == text


class TestQuickFunctions:
    """Test convenience functions for one-shot operations."""

    def test_quick_anonymize(self):
        """quick_anonymize should work with defaults."""
        text = "Email: test@example.com"
        result = quick_anonymize(text)

        assert "[EMAIL_" in result.text
        assert result.mapping

    def test_quick_deanonymize(self):
        """quick_deanonymize should restore values."""
        mapping = {"[EMAIL_1234]": "test@example.com"}
        text = "Contact [EMAIL_1234] please"

        restored = quick_deanonymize(text, mapping)
        assert "test@example.com" in restored

    def test_quick_with_salt(self):
        """Salt should make tokens deterministic."""
        text = "Email: test@example.com"

        result1 = quick_anonymize(text, salt="fixed_salt")
        result2 = quick_anonymize(text, salt="fixed_salt")

        # Same salt should produce same tokens
        assert result1.text == result2.text


class TestScanning:
    """Test scanning for sensitive data without anonymizing."""

    def test_scan_finds_patterns(self):
        """scan() should identify sensitive data without modifying."""
        text = "Emails: a@b.com and c@d.com, password: secret123"
        anon = Anonymizer()

        findings = anon.scan(text)

        assert "email" in findings
        assert len(findings["email"]) == 2
        assert "password" in findings

    def test_scan_no_modification(self):
        """scan() should not modify original text."""
        text = "Email: test@example.com"
        anon = Anonymizer()

        anon.scan(text)
        # Original should be unchanged
        assert "test@example.com" in text

    def test_scan_returns_deduplicated(self):
        """scan() should deduplicate findings."""
        text = "Email: test@example.com, same email: test@example.com"
        anon = Anonymizer()

        findings = anon.scan(text)

        # Should only list once even if appears multiple times
        assert len(findings.get("email", [])) == 1


class TestCustomPatterns:
    """Test adding custom patterns."""

    def test_add_custom_pattern(self):
        """Should be able to add custom patterns."""
        anon = Anonymizer()
        anon.add_pattern(
            name="custom_id",
            regex=r"ID:\s*(\d{6})",
            mask_prefix="[ID_",
        )

        text = "User ID: 123456"
        result = anon.anonymize(text)

        assert "123456" not in result.text
        assert "[ID_" in result.text

    def test_disable_pattern(self):
        """Should be able to disable patterns."""
        anon = Anonymizer()
        anon.disable_pattern("email")

        text = "Email: test@example.com"
        result = anon.anonymize(text)

        # Email should NOT be masked (disabled)
        assert "test@example.com" in result.text
        assert "[EMAIL_" not in result.text

    def test_enable_pattern(self):
        """Should be able to re-enable patterns."""
        anon = Anonymizer()
        anon.disable_pattern("email")
        anon.enable_pattern("email")

        text = "Email: test@example.com"
        result = anon.anonymize(text)

        # Should be masked again
        assert "test@example.com" not in result.text
        assert "[EMAIL_" in result.text


class TestAnonymizationResult:
    """Test AnonymizationResult class."""

    def test_result_has_stats(self):
        """Result should contain anonymization statistics."""
        text = "Email: a@b.com, API: sk-123456789012, Password: secret"
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert result.stats
        # Should count each pattern type found
        total_masked = sum(result.stats.values())
        assert total_masked >= 2

    def test_result_has_mapping(self):
        """Result should contain token to original mapping."""
        text = "Email: test@example.com"
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert result.mapping
        assert any("@example.com" in v for v in result.mapping.values())


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_text(self):
        """Should handle empty text gracefully."""
        anon = Anonymizer()
        result = anon.anonymize("")

        assert result.text == ""
        assert result.mapping == {}
        assert result.stats == {}

    def test_no_sensitive_data(self):
        """Should handle text with no sensitive data."""
        text = "The quick brown fox jumps over the lazy dog."
        anon = Anonymizer()
        result = anon.anonymize(text)

        assert result.text == text
        assert result.mapping == {}

    def test_very_long_value(self):
        """Should handle very long values (truncated)."""
        anon = Anonymizer(max_length=20)
        long_key = "sk-" + "a" * 100
        text = f"API key: {long_key}"

        result = anon.anonymize(text)

        # Long key should be masked
        assert long_key not in result.text
        assert "[APIKEY_" in result.text
        # Original in mapping should be truncated
        for original in result.mapping.values():
            assert len(original) <= 23  # max_length + "..."

    def test_overlapping_patterns(self):
        """Should handle overlapping patterns correctly."""
        # This test ensures longer patterns are processed first
        text = "Path: /home/user/secret.txt Password: mypass"
        anon = Anonymizer()
        result = anon.anonymize(text)

        # Both should be masked without interference
        assert "/home/user" not in result.text
        assert "mypass" not in result.text
