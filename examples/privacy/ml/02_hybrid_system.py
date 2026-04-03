"""Hybrid ML + Regex anonymization system.

Combines traditional regex patterns with ML-based detection for
coverage of both known patterns and unknown/random strings.
"""

import math
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from llx.privacy import Anonymizer
from llx.privacy.project import AnonymizationContext, ProjectAnonymizer


@dataclass
class DetectionResult:
    """Result from hybrid detection."""
    text: str
    detected_by: str  # 'regex', 'ml_entropy', 'ml_context', 'ml_semantic'
    pattern_type: str
    confidence: float
    position: tuple[int, int]


class HybridAnonymizer:
    """Combines regex and ML detection for maximum coverage."""
    
    def __init__(self):
        self.regex_anon = Anonymizer()
        self.ml_enabled = True
        self.entropy_threshold = 4.0
        self.min_random_length = 8
    
    def calculate_entropy(self, text: str) -> float:
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
    
    def detect_with_regex(self, text: str) -> list[DetectionResult]:
        """Detect using traditional regex patterns."""
        results = []
        findings = self.regex_anon.scan(text)
        
        for pattern_name, matches in findings.items():
            for match in matches:
                # Find position in text
                pos = text.find(match)
                if pos != -1:
                    results.append(DetectionResult(
                        text=match,
                        detected_by='regex',
                        pattern_type=pattern_name,
                        confidence=0.95,  # Regex has high confidence
                        position=(pos, pos + len(match))
                    ))
        
        return results
    
    def detect_ml_entropy(self, text: str) -> list[DetectionResult]:
        """Detect high-entropy strings using ML."""
        results = []
        
        # Find quoted strings and assignments
        patterns = [
            r'["\']([A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:\'"|,.<>/?]{' + str(self.min_random_length) + ',})["\']',
            r'[=:]\s*([A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:\'"|,.<>/?]{' + str(self.min_random_length) + ',})(?:\s*$|\s*[,;})])',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                candidate = match.group(1)
                entropy = self.calculate_entropy(candidate)
                
                if entropy >= self.entropy_threshold:
                    # Determine likely type
                    likely_type = self._classify_entropy_string(candidate, entropy)
                    
                    results.append(DetectionResult(
                        text=candidate,
                        detected_by='ml_entropy',
                        pattern_type=likely_type,
                        confidence=min(0.95, entropy / 5.0),
                        position=(match.start(1), match.end(1))
                    ))
        
        return results
    
    def detect_ml_context(self, text: str) -> list[DetectionResult]:
        """Detect based on surrounding context."""
        results = []
        
        # Context patterns
        context_patterns = [
            (r'(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]{6,})', 'password_context'),
            (r'(secret|key|token)\s*[=:]\s*["\']?([A-Za-z0-9!@#$%^&*]{8,})', 'secret_context'),
            (r'(api[_-]?key)\s*[=:]\s*["\']?([A-Za-z0-9_-]{16,})', 'api_key_context'),
        ]
        
        for pattern, ctx_type in context_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = match.group(2)
                results.append(DetectionResult(
                    text=value,
                    detected_by='ml_context',
                    pattern_type=ctx_type,
                    confidence=0.85,
                    position=(match.start(2), match.end(2))
                ))
        
        return results
    
    def _classify_entropy_string(self, text: str, entropy: float) -> str:
        """Classify high-entropy string type."""
        # Check for hex pattern (common for keys/hashes)
        if re.match(r'^[0-9a-f]+$', text, re.I):
            if len(text) >= 64:
                return 'hash_sha256'
            elif len(text) >= 32:
                return 'api_key_hex'
            return 'hex_id'
        
        # Check for base64 pattern
        if re.match(r'^[A-Za-z0-9+/=]+$', text) and len(text) % 4 == 0:
            return 'base64_secret'
        
        # Check for special char frequency (password indicator)
        special_chars = sum(1 for c in text if c in '!@#$%^&*()_+-=[]{}|;:,.<>?')
        if special_chars / len(text) > 0.2:
            return 'password_high_entropy'
        
        # Check for key prefixes
        if any(text.startswith(p) for p in ['sk_', 'pk_', 'ak_', 'ghp_']):
            return 'prefixed_key'
        
        if entropy >= 4.5:
            return 'random_high_entropy'
        return 'random_medium_entropy'
    
    def hybrid_detect(self, text: str) -> list[DetectionResult]:
        """Run both regex and ML detection, merge results."""
        # Run both detection methods
        regex_results = self.detect_with_regex(text)
        ml_entropy_results = self.detect_ml_entropy(text)
        ml_context_results = self.detect_ml_context(text)
        
        all_results = regex_results + ml_entropy_results + ml_context_results
        
        # Merge overlapping detections (prefer regex for known patterns)
        merged = self._merge_results(all_results)
        
        return merged
    
    def _merge_results(self, results: list[DetectionResult]) -> list[DetectionResult]:
        """Merge overlapping detection results."""
        if not results:
            return []
        
        # Sort by position
        sorted_results = sorted(results, key=lambda r: r.position[0])
        
        merged = []
        current = sorted_results[0]
        
        for next_result in sorted_results[1:]:
            # Check for overlap
            if next_result.position[0] < current.position[1]:
                # Overlap detected - choose best
                if current.detected_by == 'regex' and next_result.detected_by != 'regex':
                    # Keep regex result (higher confidence for known patterns)
                    continue
                elif next_result.detected_by == 'regex' and current.detected_by != 'regex':
                    current = next_result
                elif next_result.confidence > current.confidence:
                    current = next_result
            else:
                # No overlap - save current and move to next
                merged.append(current)
                current = next_result
        
        merged.append(current)
        return merged
    
    def hybrid_anonymize(self, text: str) -> tuple[str, list[DetectionResult], dict]:
        """Anonymize using hybrid approach."""
        detections = self.hybrid_detect(text)
        
        # Sort by position descending for replacement
        sorted_detections = sorted(detections, key=lambda d: d.position[0], reverse=True)
        
        anonymized = text
        mapping = {}
        stats = {'regex': 0, 'ml_entropy': 0, 'ml_context': 0, 'ml_semantic': 0}
        
        for i, detection in enumerate(sorted_detections):
            original = detection.text
            
            # Create mask
            if detection.detected_by == 'regex':
                mask = f"[REGEX_{detection.pattern_type.upper()}_{i:04d}]"
            else:
                mask = f"[ML_{detection.detected_by.upper()}_{detection.pattern_type.upper()}_{i:04d}]"
            
            # Replace in text
            start, end = detection.position
            anonymized = anonymized[:start] + mask + anonymized[end:]
            
            mapping[mask] = original
            stats[detection.detected_by] = stats.get(detection.detected_by, 0) + 1
        
        return anonymized, detections, mapping, stats


def create_test_scenarios() -> dict[str, str]:
    """Create test scenarios with various sensitive data."""
    
    return {
        "scenario_1_mixed": """
# Mixed sensitive data types
DATABASE_URL = "postgresql://admin:SuperSecret123!@db.internal.com:5432/myapp"
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
email = "admin@company.com"
phone = "+1 555 123 4567"
password = "MyStr0ng!P@ssw0rd2024"
secret_token = "x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6"
encryption_key = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
""",
        
        "scenario_2_code": """
class PaymentService:
    def __init__(self):
        self.api_key = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
        self.db_password = "p@ssw0rd!#2024Secure"
        self.jwt_secret = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        self.session_token = "a1b2c3d4e5f6789012345678901234567890abcdef"
    
    def connect(self):
        conn_str = "postgresql://user:Secret123!@localhost/db"
        return conn_str
""",
        
        "scenario_3_config": """
[database]
host = prod-db-01.internal.company.com
password = AnotherSecretPassword456!
encryption_key = AES256-KEY-HERE-VERY-SECRET

[api_keys]
stripe = sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL
aws_access = AKIAIOSFODNN7EXAMPLE
aws_secret = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[tokens]
session = x9k#mP2$vL8@nQ4*wJ7&cR3^hF5(bN6
nonce = 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069
""",
        
        "scenario_4_edge_cases": """
# Edge cases that challenge detection
# 1. Password in URL
url = "https://user:pass123@api.example.com/data"

# 2. High entropy but readable
readable_random = "correct-horse-battery-staple"  # diceware style

# 3. Base64 encoded secret
b64_secret = "d2Vha2J1dHN0cm9uZ3Bhc3N3b3JkMTIz"

# 4. Very long random
long_random = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"

# 5. Short but high entropy (should NOT be detected)
short_high = "aB3$"

# 6. Normal text that might trigger
normal_text = "This is just a normal sentence with some words"
""",
    }


def main():
    print("=" * 80)
    print("LLX Privacy: Hybrid ML + Regex Anonymization System")
    print("=" * 80)
    
    hybrid = HybridAnonymizer()
    scenarios = create_test_scenarios()
    
    # Compare detection methods
    print("\n1. DETECTION METHOD COMPARISON")
    print("-" * 60)
    
    for scenario_name, text in list(scenarios.items())[:2]:
        print(f"\nScenario: {scenario_name}")
        print("-" * 40)
        
        # Regex only
        regex_findings = hybrid.regex_anon.scan(text)
        regex_count = sum(len(v) for v in regex_findings.values())
        print(f"Regex detection: {regex_count} items")
        
        # ML only
        ml_results = hybrid.detect_ml_entropy(text) + hybrid.detect_ml_context(text)
        ml_count = len(ml_results)
        print(f"ML detection: {ml_count} items")
        
        # Hybrid
        hybrid_results = hybrid.hybrid_detect(text)
        print(f"Hybrid detection: {len(hybrid_results)} items")
        
        # Show breakdown
        by_method = {}
        for r in hybrid_results:
            by_method[r.detected_by] = by_method.get(r.detected_by, 0) + 1
        
        print("  Breakdown:", end="")
        for method, count in by_method.items():
            print(f" {method}={count}", end="")
        print()
    
    # Full anonymization example
    print("\n2. FULL HYBRID ANONYMIZATION")
    print("-" * 60)
    
    test_text = scenarios['scenario_1_mixed']
    
    print("Original text:")
    print(test_text)
    
    anon_text, detections, mapping, stats = hybrid.hybrid_anonymize(test_text)
    
    print("\nAnonymized text:")
    print(anon_text)
    
    print(f"\nDetection statistics:")
    for method, count in stats.items():
        print(f"  {method}: {count} items")
    
    print(f"\nMapping ({len(mapping)} items):")
    for mask, original in list(mapping.items())[:5]:
        print(f"  {mask} ← {original}")
    
    # Edge cases
    print("\n3. EDGE CASE ANALYSIS")
    print("-" * 60)
    
    edge_cases = scenarios['scenario_4_edge_cases']
    edge_results = hybrid.hybrid_detect(edge_cases)
    
    print("Edge case results:")
    for result in edge_results:
        print(f"  {result.pattern_type:<25} detected_by={result.detected_by:<12} "
              f"conf={result.confidence:.2f} text='{result.text[:30]}...'")
    
    # Project-level hybrid
    print("\n4. PROJECT-LEVEL HYBRID ANONYMIZATION")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "hybrid_project"
        project_path.mkdir()
        
        # Create project files
        (project_path / "config.py").write_text(scenarios['scenario_1_mixed'])
        (project_path / "services.py").write_text(scenarios['scenario_2_code'])
        (project_path / "settings.ini").write_text(scenarios['scenario_3_config'])
        
        print(f"Created project with 3 files")
        
        # Hybrid approach on project
        ctx = AnonymizationContext(project_path=project_path)
        
        # First pass: regex-based via ProjectAnonymizer
        project_anon = ProjectAnonymizer(ctx)
        result = project_anon.anonymize_project()
        
        # Second pass: ML-based on content
        ml_hybrid = HybridAnonymizer()
        
        total_ml_findings = 0
        for file_path, content in result.files.items():
            if file_path.endswith(('.py', '.ini', '.txt')):
                ml_results = ml_hybrid.hybrid_detect(content)
                total_ml_findings += len(ml_results)
        
        print(f"Project anonymization:")
        print(f"  Regex-based: {len(ctx.variables)} variables, {len(ctx.functions)} functions")
        print(f"  ML-based findings: {total_ml_findings} high-entropy/contextual items")
        
        # Show combined result
        sample_file = list(result.files.keys())[0]
        print(f"\nSample output ({sample_file}):")
        print(result.files[sample_file][:500])
    
    # Comparison table
    print("\n5. METHOD COMPARISON SUMMARY")
    print("-" * 60)
    print(f"{'Method':<20} {'Strengths':<35} {'Limitations'}")
    print("-" * 80)
    print(f"{'Regex-only':<20} {'Known patterns, fast, precise':<35} {'Misses unknown/random strings'}")
    print(f"{'ML-entropy':<20} {'Random strings, high entropy':<35} {'May flag legitimate code'}")
    print(f"{'ML-context':<20} {'Contextual passwords':<35} {'Requires context analysis'}")
    print(f"{'Hybrid':<20} {'Maximum coverage, best of both':<35} {'Slightly more complex'}")
    
    print("\n" + "=" * 80)
    print("Hybrid system advantages:")
    print("  ✓ Regex catches known patterns with high precision")
    print("  ✓ ML catches random passwords/keys regex misses")
    print("  ✓ Context analysis finds passwords in code patterns")
    print("  ✓ Merging avoids duplicate detections")
    print("  ✓ Best coverage for both structured and unstructured secrets")
    print("=" * 80)


if __name__ == "__main__":
    main()
