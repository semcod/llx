"""Advanced contextual password detection using NLP techniques.

Detects passwords based on:
- Variable naming patterns (password_var, pwd, etc.)
- Assignment contexts (password = ..., password:, etc.)
- Semantic role in code (authentication, encryption)
- Surrounding comments and documentation
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from llx.privacy import Anonymizer


@dataclass
class PasswordCandidate:
    """Candidate password detection result."""
    text: str
    context_type: str  # assignment, parameter, dict_key, comment_hint
    confidence: float
    variable_name: str = ""
    surrounding_context: str = ""


class ContextualPasswordDetector:
    """Detects passwords based on code context and NLP patterns."""
    
    # Password-related variable name patterns
    PASSWORD_INDICATORS = [
        r'password', r'passwd', r'pwd', r'pass', r'secret',
        r'credential', r'cred', r'auth', r'authentication',
        r'token', r'key', r'secret_key', r'private_key',
        r'api_secret', r'api_key', r'access_token',
        r'master_pass', r'admin_pass', r'root_pass',
        r'encryption_pass', r'keystore_pass', r'truststore_pass',
    ]
    
    # Assignment patterns that suggest password
    ASSIGNMENT_PATTERNS = [
        # Python: password = "value"
        r'({})\s*=\s*["\']([^"\']+)["\']',
        # Python dict: "password": "value"
        r'["\']?({})["\']?\s*:\s*["\']([^"\']+)["\']',
        # Config: password = value
        r'({})\s*=\s*([^\s#;]+)',
        # Function param: password="value"
        r'({})=(["\'][^"\']+["\']|[^,)\s]+)',
    ]
    
    # Context words that indicate sensitive authentication
    AUTH_CONTEXT = [
        'login', 'authenticate', 'signin', 'signup', 'register',
        'verify', 'validate', 'check', 'confirm',
        'encrypt', 'decrypt', 'cipher', 'hash',
        'sudo', 'su', 'ssh', 'ftp', 'telnet',
    ]
    
    def __init__(self):
        self.anonymizer = Anonymizer()
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> list[tuple]:
        """Compile regex patterns for efficiency."""
        compiled = []
        
        indicators = '|'.join(self.PASSWORD_INDICATORS)
        
        # Pattern 1: Variable assignment
        pattern1 = re.compile(
            rf'\b({indicators})\b\s*=\s*["\']?([^"\'\s#;]+)',
            re.IGNORECASE
        )
        compiled.append(('assignment', pattern1))
        
        # Pattern 2: Dictionary key
        pattern2 = re.compile(
            rf'["\']?({indicators})["\']?\s*:\s*["\']?([^"\'}}\]\s]+)',
            re.IGNORECASE
        )
        compiled.append(('dict_key', pattern2))
        
        # Pattern 3: Function parameter
        pattern3 = re.compile(
            rf'\b({indicators})\s*=\s*["\']([^"\']+)["\']',
            re.IGNORECASE
        )
        compiled.append(('parameter', pattern3))
        
        # Pattern 4: Constructor/init
        pattern4 = re.compile(
            rf'self\.({indicators})\s*=\s*["\']?([^"\'\s]+)',
            re.IGNORECASE
        )
        compiled.append(('instance_variable', pattern4))
        
        # Pattern 5: Comment hint followed by password
        pattern5 = re.compile(
            rf'#.*(?:password|secret|key).*:?\s*["\']?([^"\'\s#;]+)',
            re.IGNORECASE
        )
        compiled.append(('comment_hint', pattern5))
        
        return compiled
    
    def detect_passwords(self, code: str) -> list[PasswordCandidate]:
        """Detect passwords in code context."""
        candidates = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check each pattern
            for pattern_type, pattern in self.compiled_patterns:
                for match in pattern.finditer(line):
                    if pattern_type == 'comment_hint':
                        password = match.group(1)
                        variable_name = 'from_comment'
                    else:
                        variable_name = match.group(1).lower()
                        password = match.group(2)
                    
                    # Filter out non-password values
                    if self._is_likely_password(password, variable_name, line):
                        # Get surrounding context (3 lines before and after)
                        start = max(0, line_num - 3)
                        end = min(len(lines), line_num + 2)
                        context = '\n'.join(lines[start:end])
                        
                        confidence = self._calculate_confidence(
                            password, variable_name, pattern_type, context
                        )
                        
                        candidates.append(PasswordCandidate(
                            text=password,
                            context_type=pattern_type,
                            confidence=confidence,
                            variable_name=variable_name,
                            surrounding_context=context
                        ))
        
        # Remove duplicates (same password value)
        seen = set()
        unique = []
        for c in candidates:
            if c.text not in seen:
                seen.add(c.text)
                unique.append(c)
        
        return unique
    
    def _is_likely_password(self, value: str, var_name: str, context: str) -> bool:
        """Filter out obvious non-passwords."""
        # Too short
        if len(value) < 4:
            return False
        
        # Common false positives
        false_positives = [
            'password', 'secret', 'key', 'none', 'null', 'true', 'false',
            'example', 'sample', 'test', 'default', 'change', 'your',
            'placeholder', 'xxx', '***', '...', '???',
        ]
        if value.lower() in false_positives:
            return False
        
        # Environment variable reference
        if value.startswith('$') or value.startswith('%'):
            return False
        
        # Function call (not a literal)
        if '(' in value and ')' in value:
            return False
        
        # File path
        if value.startswith('/') or value.startswith('./') or value.startswith('../'):
            return False
        
        # URL (not a password itself)
        if value.startswith('http://') or value.startswith('https://'):
            return False
        
        return True
    
    def _calculate_confidence(
        self, 
        password: str, 
        var_name: str, 
        context_type: str,
        context: str
    ) -> float:
        """Calculate confidence score for password detection."""
        confidence = 0.5  # Base confidence
        
        # Variable name strength
        if any(x in var_name for x in ['password', 'passwd', 'pwd', 'secret']):
            confidence += 0.3
        elif any(x in var_name for x in ['key', 'token', 'auth']):
            confidence += 0.2
        
        # Context type
        if context_type == 'assignment':
            confidence += 0.1
        elif context_type == 'instance_variable':
            confidence += 0.15
        elif context_type == 'dict_key':
            confidence += 0.1
        
        # Password complexity (higher complexity = more likely real password)
        complexity = self._calculate_password_complexity(password)
        confidence += complexity * 0.2
        
        # Surrounding context analysis
        if any(word in context.lower() for word in self.AUTH_CONTEXT):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_password_complexity(self, password: str) -> float:
        """Calculate password complexity score (0-1)."""
        score = 0.0
        
        # Length contribution
        if len(password) >= 12:
            score += 0.3
        elif len(password) >= 8:
            score += 0.2
        elif len(password) >= 6:
            score += 0.1
        
        # Character variety
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        variety_count = sum([has_lower, has_upper, has_digit, has_special])
        score += variety_count * 0.15
        
        # Entropy contribution
        entropy = self._calculate_entropy(password)
        if entropy >= 4.0:
            score += 0.2
        elif entropy >= 3.0:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy."""
        if not text:
            return 0.0
        char_counts = Counter(text)
        length = len(text)
        entropy = 0.0
        for count in char_counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy
    
    def analyze_code(self, code: str) -> dict[str, Any]:
        """Full analysis of code for passwords."""
        candidates = self.detect_passwords(code)
        
        # Group by context type
        by_type = {}
        for c in candidates:
            by_type.setdefault(c.context_type, []).append(c)
        
        # Calculate statistics
        total = len(candidates)
        high_confidence = sum(1 for c in candidates if c.confidence >= 0.8)
        medium_confidence = sum(1 for c in candidates if 0.5 <= c.confidence < 0.8)
        
        return {
            'candidates': candidates,
            'by_type': by_type,
            'total': total,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'risk_score': min(1.0, (high_confidence * 0.3 + medium_confidence * 0.1)),
        }


def create_test_code_samples() -> dict[str, str]:
    """Create various code samples with hidden passwords."""
    
    return {
        "python_config": '''
# Database configuration - PRODUCTION
db_config = {
    "host": "prod-db.company.com",
    "password": "SuperSecretDBPass2024!",  # Change quarterly
    "username": "app_user"
}

# API credentials
STRIPE_SECRET_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
INTERNAL_API_KEY = "x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6"

# Legacy system
def connect_legacy():
    passwd = "old_system_pass_2023"
    return login("admin", passwd)
''',
        
        "class_init": '''
class DatabaseConnection:
    """Database connection manager."""
    
    def __init__(self):
        self.db_password = "p@ssw0rd!#2024Secure"
        self.api_secret = "a1b2c3d4e5f6789012345678901234567890abcdef"
        self.encryption_key = "AES256-GCM-KEY-HERE-VERY-SECRET-DONT-SHARE"
        
    def connect(self, password=None):
        """Connect to database."""
        if password is None:
            password = "fallback_password_123"
        return self._authenticate(password)
    
    def _authenticate(self, pwd):
        # Authenticate with password
        return hash(pwd) == hash(self.db_password)
''',
        
        "comments_hints": '''
# Production password: Pr0dP@ssw0rd!2024
# Admin secret key: admin_secret_key_xyz123
# TODO: Change default password before deployment

# Authentication
def login():
    # password: default123  # REMOVE BEFORE PROD
    credentials = {
        "username": "admin",
        "secret": "hidden_password_in_dict"
    }
    return credentials
''',
        
        "various_patterns": '''
# Various password patterns
user_pwd = "MyUserPassword123"
credential_password = "CredentialPass456!"
secret_key = "SecretKey789#"
auth_token = "AuthTokenXYZ123"

# Constructor patterns
class Service:
    def __init__(self):
        self.password = "instance_password_here"
        self.passwd = "another_instance_pass"
        
# Function parameters
def authenticate(password="default_pass"):
    return check(password)

def connect(username, secret_key="default_secret"):
    return db_connect(username, secret_key)
''',
    }


def main():
    print("=" * 80)
    print("LLX Privacy: Advanced Contextual Password Detection (NLP)")
    print("=" * 80)
    
    detector = ContextualPasswordDetector()
    samples = create_test_code_samples()
    
    # Analyze each sample
    for sample_name, code in samples.items():
        print(f"\n{'='*60}")
        print(f"SAMPLE: {sample_name}")
        print("=" * 60)
        
        print("\nCode:")
        print(code[:500] + "..." if len(code) > 500 else code)
        
        analysis = detector.analyze_code(code)
        
        print(f"\n📊 Analysis Results:")
        print(f"  Total candidates: {analysis['total']}")
        print(f"  High confidence (≥0.8): {analysis['high_confidence']}")
        print(f"  Medium confidence (0.5-0.8): {analysis['medium_confidence']}")
        print(f"  Risk score: {analysis['risk_score']:.2f}")
        
        print(f"\n🔍 Detected passwords:")
        for candidate in analysis['candidates']:
            confidence_emoji = "🔴" if candidate.confidence >= 0.8 else "🟡" if candidate.confidence >= 0.5 else "🟢"
            print(f"\n  {confidence_emoji} Variable: {candidate.variable_name}")
            print(f"     Value: {candidate.text}")
            print(f"     Context: {candidate.context_type}")
            print(f"     Confidence: {candidate.confidence:.0%}")
            print(f"     Complexity: {detector._calculate_password_complexity(candidate.text):.2f}")
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY: Contextual vs Regex Detection")
    print("=" * 80)
    
    all_passwords = []
    for code in samples.values():
        analysis = detector.analyze_code(code)
        all_passwords.extend(analysis['candidates'])
    
    # Regex detection for comparison
    regex_anon = Anonymizer()
    regex_found = 0
    for code in samples.values():
        findings = regex_anon.scan(code)
        regex_found += sum(len(v) for v in findings.values())
    
    print(f"\nDetection comparison across all samples:")
    print(f"  Contextual detection (NLP): {len(all_passwords)} passwords")
    print(f"  Regex detection: {regex_found} items (not all are passwords)")
    
    print(f"\nContextual detection advantages:")
    print("  ✓ Understands variable naming conventions")
    print("  ✓ Detects passwords in dictionaries")
    print("  ✓ Finds instance variables (self.password)")
    print("  ✓ Recognizes comment hints")
    print("  ✓ Filters false positives by context")
    print("  ✓ Calculates confidence based on multiple factors")
    
    print("\n" + "=" * 80)
    print("Integration with Anonymizer:")
    print("=" * 80)
    
    # Show integration
    sample_code = samples['python_config']
    
    print("\nOriginal code:")
    print(sample_code)
    
    # Detect and mask
    analysis = detector.analyze_code(sample_code)
    masked = sample_code
    
    for i, candidate in enumerate(analysis['candidates']):
        mask = f"[PASSWORD_CTX_{i:04d}]"
        masked = masked.replace(candidate.text, mask, 1)
    
    print("\nMasked code:")
    print(masked)
    
    print("\nMapping:")
    for i, candidate in enumerate(analysis['candidates']):
        mask = f"[PASSWORD_CTX_{i:04d}]"
        print(f"  {mask} ← {candidate.text}")
    
    print("\n" + "=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
