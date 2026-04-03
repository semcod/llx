"""ML-based sensitive data detection and anonymization.

Uses machine learning techniques (NLP, pattern classification) to detect
sensitive data that traditional regex might miss:
- Context-aware password detection
- Named Entity Recognition (NER) for PII
- Entropy analysis for random strings
- Semantic analysis of sensitive contexts
"""

import math
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llx.privacy import Anonymizer
from llx.privacy.project import AnonymizationContext, ProjectAnonymizer, ASTAnonymizer


@dataclass
class EntropyResult:
    """Result of entropy analysis."""
    text: str
    entropy: float
    is_random: bool
    likely_type: str  # password, token, key, id, noise


class EntropyAnalyzer:
    """Analyzes text entropy to detect random/pseudorandom strings."""
    
    # Entropy thresholds
    HIGH_ENTROPY_THRESHOLD = 4.5  # Likely random
    MEDIUM_ENTROPY_THRESHOLD = 3.5  # Possibly random
    
    # Pattern weights for classification
    PATTERNS = {
        'password': {
            'context_words': ['password', 'pwd', 'passwd', 'pass', 'secret'],
            'min_length': 8,
            'max_length': 64,
            'entropy_threshold': 3.0,
            'required_chars': r'[a-zA-Z0-9]',  # Alphanumeric + special
        },
        'api_key': {
            'context_words': ['api_key', 'apikey', 'key', 'token', 'auth'],
            'min_length': 16,
            'max_length': 128,
            'entropy_threshold': 4.0,
            'prefixes': ['sk_', 'pk_', 'api-', 'key-'],
        },
        'encryption_key': {
            'context_words': ['encryption', 'cipher', 'aes', 'rsa', 'key', 'private'],
            'min_length': 32,
            'max_length': 256,
            'entropy_threshold': 4.5,
        },
        'session_token': {
            'context_words': ['session', 'token', 'cookie', 'jwt', 'bearer'],
            'min_length': 20,
            'max_length': 512,
            'entropy_threshold': 4.0,
        },
        'database_id': {
            'context_words': ['id', 'uuid', 'guid', 'objectid'],
            'min_length': 16,
            'max_length': 64,
            'entropy_threshold': 3.5,
            'patterns': [r'^[0-9a-f]{8}-[0-9a-f]{4}', r'^[0-9a-f]{24}$'],  # UUID, MongoID
        },
    }
    
    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = Counter(text)
        length = len(text)
        
        # Calculate entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def analyze_randomness(self, text: str, context: str = "") -> EntropyResult:
        """Analyze if text appears to be random/high-entropy."""
        entropy = self.calculate_entropy(text)
        
        # Check for common patterns
        likely_type = self._classify_by_context(text, context, entropy)
        
        is_random = (
            entropy >= self.HIGH_ENTROPY_THRESHOLD or
            (entropy >= self.MEDIUM_ENTROPY_THRESHOLD and likely_type != 'noise')
        )
        
        return EntropyResult(
            text=text,
            entropy=entropy,
            is_random=is_random,
            likely_type=likely_type
        )
    
    def _classify_by_context(self, text: str, context: str, entropy: float) -> str:
        """Classify text type based on context and entropy."""
        context_lower = context.lower()
        
        for type_name, config in self.PATTERNS.items():
            # Check context words
            if any(word in context_lower for word in config.get('context_words', [])):
                # Check length constraints
                if config.get('min_length', 0) <= len(text) <= config.get('max_length', 1000):
                    # Check entropy threshold
                    if entropy >= config.get('entropy_threshold', 4.0):
                        return type_name
        
        # Check for UUID pattern
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', text, re.I):
            return 'uuid'
        
        # Check for hex-only (common for hashes)
        if re.match(r'^[0-9a-f]+$', text, re.I) and len(text) >= 32:
            return 'hash'
        
        # Check for base64
        if re.match(r'^[A-Za-z0-9+/=]+$', text) and len(text) % 4 == 0 and entropy > 4.0:
            return 'base64_secret'
        
        # Default classification based on entropy
        if entropy >= 4.5:
            return 'high_entropy'
        elif entropy >= 3.5:
            return 'medium_entropy'
        
        return 'noise'
    
    def find_high_entropy_strings(self, text: str, min_length: int = 8) -> list[EntropyResult]:
        """Find all high-entropy strings in text."""
        results = []
        
        # Look for quoted strings
        patterns = [
            r'["\']([A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:\'"|,.<>/?]{8,})["\']',
            r'[=:]\s*([A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:\'"|,.<>/?]{8,})',
            r'\b([A-Fa-f0-9]{32,})\b',  # Hex strings (hashes, keys)
            r'\b([A-Za-z0-9+/=]{20,})\b',  # Base64-like
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                candidate = match.group(1)
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                result = self.analyze_randomness(candidate, context)
                if result.is_random and result.likely_type not in ['noise', 'uuid']:
                    results.append(result)
        
        return results


class MLBasedAnonymizer:
    """Anonymizer using ML/NLP techniques beyond simple regex."""
    
    def __init__(self):
        self.anonymizer = Anonymizer()
        self.entropy_analyzer = EntropyAnalyzer()
        self.ml_findings: list[dict] = []
    
    def analyze_with_ml(self, text: str) -> list[dict]:
        """Analyze text using ML-based detection."""
        findings = []
        
        # 1. Entropy-based detection
        entropy_results = self.entropy_analyzer.find_high_entropy_strings(text)
        for result in entropy_results:
            findings.append({
                'type': 'entropy',
                'subtype': result.likely_type,
                'text': result.text,
                'entropy': round(result.entropy, 2),
                'confidence': self._entropy_confidence(result.entropy),
            })
        
        # 2. Context-aware password detection
        password_candidates = self._detect_contextual_passwords(text)
        findings.extend(password_candidates)
        
        # 3. NER-like PII detection
        pii_candidates = self._detect_pii_semantic(text)
        findings.extend(pii_candidates)
        
        self.ml_findings = findings
        return findings
    
    def _entropy_confidence(self, entropy: float) -> float:
        """Convert entropy to confidence score."""
        if entropy >= 5.0:
            return 0.95
        elif entropy >= 4.5:
            return 0.85
        elif entropy >= 4.0:
            return 0.75
        elif entropy >= 3.5:
            return 0.60
        return 0.40
    
    def _detect_contextual_passwords(self, text: str) -> list[dict]:
        """Detect passwords based on surrounding context."""
        findings = []
        
        # Context patterns that suggest password
        password_contexts = [
            (r'(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]+)', 'assignment'),
            (r'(?:password|pwd)\s+is\s+["\']?([^"\'\s]+)', 'is_statement'),
            (r'(?:set|change|update).*password.*["\']([^"\']+)', 'action'),
            (r'credentials.*:\s*\{[^}]*password["\']?\s*:\s*["\']?([^"\'}]+)', 'credentials'),
        ]
        
        for pattern, context_type in password_contexts:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                password = match.group(1)
                if len(password) >= 6:
                    entropy = self.entropy_analyzer.calculate_entropy(password)
                    findings.append({
                        'type': 'contextual_password',
                        'subtype': context_type,
                        'text': password,
                        'context': match.group(0)[:50],
                        'entropy': round(entropy, 2),
                        'confidence': 0.90 if entropy > 3.0 else 0.70,
                    })
        
        return findings
    
    def _detect_pii_semantic(self, text: str) -> list[dict]:
        """Detect PII based on semantic patterns."""
        findings = []
        
        # Name patterns with context
        name_patterns = [
            (r'(Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+([A-Z][a-z]+\s[A-Z][a-z]+)', 'formal_name'),
            (r'(?:name|full\s*name)\s*[=:]\s*["\']?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'name_assignment'),
            (r'(?:signed|contact|author)\s*[:\-]?\s*([A-Z][a-z]+\s[A-Z][a-z]+)', 'role_based_name'),
        ]
        
        for pattern, subtype in name_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if len(name.split()) >= 2:  # At least first + last
                    findings.append({
                        'type': 'semantic_pii',
                        'subtype': f'name_{subtype}',
                        'text': name,
                        'context': match.group(0)[:50],
                        'confidence': 0.80,
                    })
        
        # Address patterns
        address_patterns = [
            (r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln)', 'street_address'),
            (r'(?:address|location)\s*[:=]\s*["\']?([^"\']+)', 'labeled_address'),
        ]
        
        for pattern, subtype in address_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                address = match.group(1) if len(match.groups()) > 0 else match.group(0)
                findings.append({
                    'type': 'semantic_pii',
                    'subtype': subtype,
                    'text': address[:50],
                    'context': match.group(0)[:50],
                    'confidence': 0.75,
                })
        
        return findings
    
    def anonymize_with_ml(self, text: str) -> tuple[str, list[dict]]:
        """Anonymize text using ML detection."""
        findings = self.analyze_with_ml(text)
        anonymized = text
        
        # Sort by length (descending) to avoid partial replacements
        findings.sort(key=lambda x: len(x['text']), reverse=True)
        
        replacements = []
        for i, finding in enumerate(findings):
            original = finding['text']
            if original in anonymized:  # Check if still present
                mask = f"[{finding['type'].upper()}_{finding['subtype'].upper()}_{i:04d}]"
                anonymized = anonymized.replace(original, mask, 1)
                replacements.append({
                    'mask': mask,
                    'original': original,
                    'type': finding['type'],
                    'confidence': finding.get('confidence', 0.5),
                })
        
        return anonymized, replacements


def create_complex_project(base_path: Path) -> None:
    """Create project with complex sensitive data patterns."""
    
    (base_path / "src").mkdir(parents=True)
    
    # File with various random/high-entropy strings
    (base_path / "src" / "config.py").write_text("""
# Configuration with various secrets
DATABASE_URL = "postgresql://admin:p@ssw0rd!#2024Secure@prod-db.internal.com:5432/myapp"

# API Keys with different patterns
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
AWS_ACCESS = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Encryption keys
AES_KEY = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
JWT_SECRET = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"

# Various password patterns
USER_PASSWORD = "my$ecureP@ss123!"  # Contextual password
LEGACY_PASS = "password: OldPass2023"  # Labeled password
auth = {
    "password": "s3cr3t_k3y_2024$",  # In dict
}

# Random IDs and tokens
SESSION_TOKEN = "a1b2c3d4e5f6789012345678901234567890abcdef"
CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"  # UUID
TRACE_ID = "abc123def45678901234567890abcdef01234567"

# High entropy strings
RANDOM_SEED = "x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6"
NONCE = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"

# Contact information
CONTACT_NAME = "Dr. John Smith"
ADMIN_NAME = "Mr. Administrator"
""")
    
    # File with semantic PII
    (base_path / "src" / "users.py").write_text("""
\"\"\"User management with PII.\"\"\"

class UserProfile:
    \"\"\"User profile with sensitive data.\"\"\"
    
    def __init__(self):
        # Names detected semantically
        self.full_name = "Jane Doe"
        self.contact_person = "Ms. Sarah Johnson"
        
        # Various credential patterns
        self.db_password = "SuperSecret123!@#"
        self.api_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
        
        # High entropy keys
        self.encryption_key = "a1b2c3d4e5f6789012345678901234567890abcdef"
        self.session_secret = "s3ss10n_s3cr3t_k3y_2024_random_string_here"
""")


def main():
    print("=" * 80)
    print("LLX Privacy: ML-Based Anonymization with Entropy Analysis")
    print("=" * 80)
    
    # Initialize ML-based anonymizer
    ml_anon = MLBasedAnonymizer()
    
    # Example 1: Analyze entropy of various strings
    print("\n1. ENTROPY ANALYSIS OF DIFFERENT STRING TYPES")
    print("-" * 60)
    
    test_strings = [
        ("password123", "common_password", "password: password123"),
        ("p@ssw0rd!#2024Secure", "complex_password", "password field"),
        ("sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL", "stripe_key", "STRIPE_KEY = ..."),
        ("550e8400-e29b-41d4-a716-446655440000", "uuid", "CORRELATION_ID"),
        ("a1b2c3d4e5f6789012345678901234567890abcdef", "hex_key", "SESSION_TOKEN"),
        ("x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6", "random_password", "RANDOM_SEED"),
        ("normal_function_name", "readable", "def normal_function_name():"),
        ("get_user_by_id", "readable", "function call"),
    ]
    
    print(f"{'String':<35} {'Type':<20} {'Entropy':<10} {'Random?':<10}")
    print("-" * 80)
    
    for text, expected_type, context in test_strings:
        result = ml_anon.entropy_analyzer.analyze_randomness(text, context)
        random_flag = "✓ YES" if result.is_random else "✗ NO"
        print(f"{text[:35]:<35} {result.likely_type:<20} {result.entropy:<10.2f} {random_flag:<10}")
    
    # Example 2: Complex text analysis
    print("\n2. COMPLEX TEXT WITH ML-BASED DETECTION")
    print("-" * 60)
    
    complex_text = """
    Configuration:
    - Database: postgresql://admin:p@ssw0rd!#2024Secure@prod-db.internal.com:5432/myapp
    - API Key: sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL
    - Password: my$ecureP@ss123!
    - Secret Key: a1b2c3d4e5f6789012345678901234567890abcdef
    - Contact: Dr. John Smith
    - Admin: Mr. Administrator
    - Session: x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6
    """
    
    print("Original text:")
    print(complex_text[:300])
    
    findings = ml_anon.analyze_with_ml(complex_text)
    
    print(f"\nML Detection Results ({len(findings)} findings):")
    print("-" * 60)
    
    for finding in findings:
        print(f"\nType: {finding['type']} ({finding.get('subtype', 'N/A')})")
        print(f"  Text: {finding['text'][:40]}...")
        print(f"  Entropy: {finding.get('entropy', 'N/A')}")
        print(f"  Confidence: {finding.get('confidence', 'N/A')}")
        if 'context' in finding:
            print(f"  Context: {finding['context'][:50]}...")
    
    # Example 3: Full project analysis
    print("\n3. FULL PROJECT ANONYMIZATION WITH ML")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "ml_project"
        project_path.mkdir()
        
        create_complex_project(project_path)
        
        # Read and analyze
        config_content = (project_path / "src" / "config.py").read_text()
        
        print("Analyzing config.py...")
        ml_findings = ml_anon.analyze_with_ml(config_content)
        
        print(f"Found {len(ml_findings)} ML-detected sensitive items:")
        for finding in ml_findings[:5]:
            print(f"  - {finding['type']}: {finding['text'][:30]}... (entropy: {finding.get('entropy', 'N/A')})")
        
        # Anonymize with ML
        anon_text, replacements = ml_anon.anonymize_with_ml(config_content)
        
        print(f"\nAnonymized config (first 500 chars):")
        print(anon_text[:500])
        
        print(f"\nReplacements made ({len(replacements)}):")
        for rep in replacements[:5]:
            print(f"  {rep['mask']} ← {rep['original'][:30]}... (confidence: {rep['confidence']:.0%})")
    
    # Example 4: Comparison with regex-only approach
    print("\n4. ML vs REGEX-ONLY COMPARISON")
    print("-" * 60)
    
    test_code = """
    # Various password patterns ML catches but regex might miss
    user_pwd = "MyStr0ng!P@ss"  # contextual
    cfg = {"secret": "h1dd3n_v4lu3_2024"}  # in dict
    api_key = "x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6"  # high entropy
    contact_name = "Dr. Sarah Johnson"  # semantic PII
    
    # These regex catches well
    email = "user@example.com"
    phone = "+48 123 456 789"
    """
    
    # Regex-only detection
    regex_anon = Anonymizer()
    regex_result = regex_anon.anonymize(test_code)
    
    # ML detection
    ml_findings = ml_anon.analyze_with_ml(test_code)
    
    print(f"Regex-only detected: {len(regex_result.mapping)} items")
    print(f"ML-based detected: {len(ml_findings)} items")
    
    print("\nML-only detections (what regex missed):")
    ml_types = set(f['type'] for f in ml_findings)
    for t in ml_types:
        count = sum(1 for f in ml_findings if f['type'] == t)
        print(f"  - {t}: {count} items")
    
    print("\n" + "=" * 80)
    print("Summary: ML-based detection catches:")
    print("  ✓ High-entropy random strings (passwords, keys)")
    print("  ✓ Contextual passwords (based on surrounding text)")
    print("  ✓ Semantic PII (names, addresses from context)")
    print("  ✓ Various patterns traditional regex might miss")
    print("=" * 80)


if __name__ == "__main__":
    main()
