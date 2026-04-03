"""Core anonymization classes for LLX privacy module."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Pattern


@dataclass
class AnonymizationPattern:
    """Definition of a sensitive data pattern."""

    name: str
    regex: Pattern[str]
    mask_prefix: str
    mask_suffix: str = ""
    enabled: bool = True
    description: str = ""


@dataclass
class AnonymizationResult:
    """Result of anonymization operation with mapping for deanonymization."""

    text: str
    mapping: dict[str, str] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=dict)

    def deanonymize(self, text: str) -> str:
        """Restore original values from anonymized text."""
        result = text
        for token, original in self.mapping.items():
            result = result.replace(token, original)
        return result


class Anonymizer:
    """Reversible anonymization engine for sensitive data.

    Usage:
        anon = Anonymizer()
        result = anon.anonymize("Contact john@example.com for API key: sk-12345")
        print(result.text)  # "Contact [EMAIL_1] for API key: [APIKEY_1]"

        # Later, restore original values in LLM response
        restored = result.deanonymize(response_text)
    """

    # Default patterns for common sensitive data
    DEFAULT_PATTERNS: list[tuple[str, str, str]] = [
        # Credentials
        ("api_key", r"\b(sk-[a-zA-Z0-9]{12,}|api[_-]?key[_-]?[\"']?[:=\s]+[a-zA-Z0-9\-_]{8,})", "[APIKEY_"),
        ("token", r"\b([a-zA-Z0-9_\-]*token[a-zA-Z0-9_\-]*[:=\s]+[\"']?[a-zA-Z0-9\-_/+=]{8,})", "[TOKEN_"),
        ("password", r"\b(password|passwd|pwd)[\s]*[:=\s]+[\"']?[^\s\"']{3,}", "[PASSWORD_"),
        ("secret", r"\b([a-zA-Z_]*secret[a-zA-Z_]*[:=\s]+[\"']?[a-zA-Z0-9\-_/+=]{6,})", "[SECRET_"),
        # Personal Information
        ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_"),
        # Phone: requires country code (+) or area code in parentheses
        ("phone", r"(?:\+\d{1,3}[-.\s]?)(?:\(?\d{1,4}\)?[-.\s]?)?(?:\d{3}[-.\s]?){1,2}\d{3,4}|(?:\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4})", "[PHONE_"),
        ("ssn_pl", r"\b\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{5}\b", "[PESEL_"),  # Polish PESEL (with date validation)
        ("credit_card", r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CC_"),
        # System paths
        ("home_path", r"/home/[a-zA-Z0-9_]+", "[HOMEPATH_"),
        ("user_path", r"/Users/[a-zA-Z0-9_\-]+", "[USERPATH_"),
        ("ip_address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_"),
        ("hostname", r"\b[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}\b", "[HOST_"),
    ]

    def __init__(
        self,
        patterns: list[AnonymizationPattern] | None = None,
        salt: str | None = None,
        max_length: int = 50,
    ):
        """Initialize anonymizer.

        Args:
            patterns: Custom patterns (uses defaults if None)
            salt: Salt for token generation (defaults to random UUID)
            max_length: Maximum length of masked value to store
        """
        self.salt = salt or str(uuid.uuid4())[:8]
        self.max_length = max_length
        self.patterns = patterns or self._default_patterns()
        self._compiled: dict[str, Pattern[str]] = {}
        self._compile_patterns()
        self._last_anonymization_mapping: dict[str, str] = {}

    def _default_patterns(self) -> list[AnonymizationPattern]:
        """Build default anonymization patterns."""
        patterns = []
        for name, regex, prefix in self.DEFAULT_PATTERNS:
            try:
                patterns.append(
                    AnonymizationPattern(
                        name=name,
                        regex=re.compile(regex, re.IGNORECASE),
                        mask_prefix=prefix,
                        mask_suffix="]",
                        description=f"Masks {name} patterns",
                    )
                )
            except re.error:
                continue
        return patterns

    def _compile_patterns(self) -> None:
        """Pre-compile all regex patterns."""
        for p in self.patterns:
            if p.enabled:
                self._compiled[p.name] = p.regex

    def anonymize(self, text: str, context: str | None = None) -> AnonymizationResult:
        """Anonymize sensitive data in text.

        Args:
            text: Input text to anonymize
            context: Optional context identifier for token uniqueness

        Returns:
            AnonymizationResult with anonymized text and mapping
        """
        mapping: dict[str, str] = {}
        stats: dict[str, int] = {}
        result = text

        # Sort patterns by specificity (longer patterns first to avoid nested matches)
        sorted_patterns = sorted(
            self.patterns,
            key=lambda p: len(p.regex.pattern),
            reverse=True,
        )

        for pattern in sorted_patterns:
            if not pattern.enabled:
                continue

            compiled = self._compiled.get(pattern.name)
            if not compiled:
                continue

            count = 0
            matches = list(compiled.finditer(result))

            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                original = match.group(0)
                if len(original) > self.max_length:
                    original = original[: self.max_length] + "..."

                # Generate unique token
                token = self._generate_token(pattern, original, context, count)

                # Replace in result
                start, end = match.span()
                result = result[:start] + token + result[end:]

                mapping[token] = original
                count += 1

            if count > 0:
                stats[pattern.name] = count

        self._last_anonymization_mapping = mapping
        return AnonymizationResult(text=result, mapping=mapping, stats=stats)

    def _generate_token(
        self, pattern: AnonymizationPattern, value: str, context: str | None, index: int
    ) -> str:
        """Generate unique anonymization token."""
        # Create deterministic but unique token
        base = f"{self.salt}:{pattern.name}:{value}:{context or ''}:{index}"
        hash_suffix = hashlib.md5(base.encode()).hexdigest()[:4].upper()
        return f"{pattern.mask_prefix}{hash_suffix}{pattern.mask_suffix}"

    def deanonymize(self, text: str, mapping: dict[str, str]) -> str:
        """Deanonymize text using provided mapping.

        Args:
            text: Anonymized text (e.g., from LLM response)
            mapping: Token -> original value mapping from anonymize()

        Returns:
            Text with original values restored
        """
        result = text
        # Sort by length descending to avoid partial replacements
        for token, original in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
            result = result.replace(token, original)
        return result

    def scan(self, text: str) -> dict[str, list[str]]:
        """Scan text for sensitive data without anonymizing.

        Returns:
            Dictionary mapping pattern names to list of found values
        """
        results: dict[str, list[str]] = {}

        for pattern in self.patterns:
            if not pattern.enabled:
                continue

            compiled = self._compiled.get(pattern.name)
            if not compiled:
                continue

            matches = compiled.findall(text)
            if matches:
                # Deduplicate while preserving order
                seen = set()
                unique = []
                for m in matches:
                    if isinstance(m, tuple):
                        m = m[0]  # Take first group if tuple
                    if m not in seen:
                        seen.add(m)
                        unique.append(m)
                results[pattern.name] = unique

        return results

    def add_pattern(
        self,
        name: str,
        regex: str | Pattern[str],
        mask_prefix: str,
        mask_suffix: str = "]",
        enabled: bool = True,
    ) -> None:
        """Add a custom anonymization pattern."""
        if isinstance(regex, str):
            regex = re.compile(regex, re.IGNORECASE)

        pattern = AnonymizationPattern(
            name=name,
            regex=regex,
            mask_prefix=mask_prefix,
            mask_suffix=mask_suffix,
            enabled=enabled,
        )
        self.patterns.append(pattern)
        self._compiled[name] = regex

    def disable_pattern(self, name: str) -> None:
        """Disable a pattern by name."""
        for p in self.patterns:
            if p.name == name:
                p.enabled = False
                self._compiled.pop(name, None)
                break

    def enable_pattern(self, name: str) -> None:
        """Enable a pattern by name."""
        for p in self.patterns:
            if p.name == name:
                p.enabled = True
                self._compiled[name] = p.regex
                break


def quick_anonymize(text: str, salt: str | None = None) -> AnonymizationResult:
    """One-shot anonymization with default settings.

    Args:
        text: Text to anonymize
        salt: Optional salt for deterministic tokens

    Returns:
        AnonymizationResult with masked text and mapping
    """
    anon = Anonymizer(salt=salt)
    return anon.anonymize(text)


def quick_deanonymize(text: str, mapping: dict[str, str]) -> str:
    """One-shot deanonymization.

    Args:
        text: Anonymized text
        mapping: Token -> original mapping from quick_anonymize()

    Returns:
        Text with original values restored
    """
    # Create temporary anonymizer just for deanonymization
    anon = Anonymizer()
    return anon.deanonymize(text, mapping)
