"""Behavioral analysis for password pattern learning.

Learns from user code patterns to improve detection over time:
- Learns common variable naming conventions
- Tracks false positives to reduce them
- Builds custom patterns based on codebase style
- Adaptive confidence thresholds
"""

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LearnedPattern:
    """A pattern learned from user code."""
    pattern: str
    pattern_type: str
    occurrences: int
    confidence: float
    examples: list[str] = field(default_factory=list)


@dataclass
class FalsePositiveRecord:
    """Record of a false positive for learning."""
    text: str
    context: str
    reason: str
    timestamp: str


class BehavioralPasswordDetector:
    """Learns and adapts to user coding patterns."""
    
    def __init__(self, learning_file: Path = None):
        self.learning_file = learning_file
        self.learned_patterns: list[LearnedPattern] = []
        self.false_positives: list[FalsePositiveRecord] = []
        self.user_naming_conventions: dict[str, int] = defaultdict(int)
        self.context_entropy: dict[str, float] = {}
        
        if learning_file and learning_file.exists():
            self._load_learning()
    
    def _load_learning(self) -> None:
        """Load learned patterns from file."""
        try:
            data = json.loads(self.learning_file.read_text())
            for p in data.get('patterns', []):
                self.learned_patterns.append(LearnedPattern(**p))
            for fp in data.get('false_positives', []):
                self.false_positives.append(FalsePositiveRecord(**fp))
            self.user_naming_conventions = defaultdict(
                int, 
                data.get('naming_conventions', {})
            )
        except Exception:
            pass  # Start fresh if loading fails
    
    def _save_learning(self) -> None:
        """Save learned patterns to file."""
        if not self.learning_file:
            return
        
        data = {
            'patterns': [
                {
                    'pattern': p.pattern,
                    'pattern_type': p.pattern_type,
                    'occurrences': p.occurrences,
                    'confidence': p.confidence,
                    'examples': p.examples[:5],  # Keep only recent examples
                }
                for p in self.learned_patterns
            ],
            'false_positives': [
                {
                    'text': fp.text,
                    'context': fp.context,
                    'reason': fp.reason,
                    'timestamp': fp.timestamp,
                }
                for fp in self.false_positives[-100:]  # Keep last 100
            ],
            'naming_conventions': dict(self.user_naming_conventions),
        }
        
        self.learning_file.parent.mkdir(parents=True, exist_ok=True)
        self.learning_file.write_text(json.dumps(data, indent=2))
    
    def learn_from_codebase(self, codebase_path: Path) -> dict[str, Any]:
        """Analyze entire codebase to learn patterns."""
        stats = {
            'files_analyzed': 0,
            'patterns_found': 0,
            'naming_conventions': defaultdict(int),
            'common_password_vars': [],
        }
        
        for py_file in codebase_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                self._analyze_file(content, stats)
                stats['files_analyzed'] += 1
            except Exception:
                continue
        
        # Update learned patterns
        self._update_learned_patterns(stats)
        self._save_learning()
        
        return stats
    
    def _analyze_file(self, content: str, stats: dict) -> None:
        """Analyze single file for patterns."""
        # Find password-related variable names
        password_vars = re.finditer(
            r'\b(\w*(?:password|passwd|pwd|secret|key|token|auth)\w*)\b',
            content,
            re.IGNORECASE
        )
        
        for match in password_vars:
            var_name = match.group(1).lower()
            stats['naming_conventions'][var_name] += 1
        
        # Find assignment patterns
        assignments = re.finditer(
            r'(\w+)\s*=\s*["\']([^"\']+)["\']',
            content
        )
        
        for match in assignments:
            var_name = match.group(1).lower()
            value = match.group(2)
            
            # If variable name suggests password, learn the value pattern
            if any(x in var_name for x in ['password', 'pwd', 'secret', 'key']):
                if len(value) >= 8:
                    stats['common_password_vars'].append((var_name, value))
    
    def _update_learned_patterns(self, stats: dict) -> None:
        """Update learned patterns from stats."""
        # Find most common naming conventions
        sorted_conventions = sorted(
            stats['naming_conventions'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for convention, count in sorted_conventions[:20]:
            self.user_naming_conventions[convention] = count
    
    def report_false_positive(
        self, 
        text: str, 
        context: str, 
        reason: str,
        timestamp: str = None
    ) -> None:
        """Report a false positive to improve future detection."""
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
        
        self.false_positives.append(FalsePositiveRecord(
            text=text,
            context=context,
            reason=reason,
            timestamp=timestamp
        ))
        
        self._save_learning()
    
    def is_false_positive(self, text: str, context: str) -> bool:
        """Check if a detection matches known false positive patterns."""
        # Check exact matches
        for fp in self.false_positives[-50:]:  # Check recent ones
            if text == fp.text:
                return True
            if text in fp.text or fp.text in text:
                return True
        
        # Check if text matches common non-password patterns
        non_password_patterns = [
            r'^\$\w+',  # Environment variables
            r'^function\s+\w+',  # Function definitions
            r'^[A-Z][a-z]+[A-Z]',  # CamelCase (likely class/function)
            r'^test_',  # Test functions
            r'^get_|^set_',  # Getters/setters
        ]
        
        for pattern in non_password_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def calculate_adaptive_confidence(
        self, 
        text: str, 
        var_name: str, 
        base_confidence: float
    ) -> float:
        """Adjust confidence based on learned patterns."""
        confidence = base_confidence
        
        # Boost confidence for known naming conventions
        if var_name.lower() in self.user_naming_conventions:
            convention_count = self.user_naming_conventions[var_name.lower()]
            if convention_count > 5:
                confidence += 0.1
            if convention_count > 20:
                confidence += 0.1
        
        # Reduce confidence if similar to false positives
        if self.is_false_positive(text, ""):
            confidence -= 0.3
        
        # Adjust based on text entropy vs learned patterns
        entropy = self._calculate_entropy(text)
        if entropy > 4.5:
            confidence += 0.05
        elif entropy < 2.5:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
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
    
    def generate_custom_patterns(self) -> list[str]:
        """Generate custom regex patterns based on learning."""
        patterns = []
        
        # Top naming conventions become patterns
        top_conventions = sorted(
            self.user_naming_conventions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for convention, count in top_conventions:
            if count >= 3:  # Only if seen multiple times
                # Create pattern from convention
                pattern = rf'\b{re.escape(convention)}\b\s*=\s*["\']([^"\']+)'
                patterns.append(pattern)
        
        return patterns
    
    def get_learning_stats(self) -> dict[str, Any]:
        """Get statistics about learned patterns."""
        return {
            'total_patterns_learned': len(self.learned_patterns),
            'false_positives_recorded': len(self.false_positives),
            'naming_conventions_tracked': len(self.user_naming_conventions),
            'top_naming_conventions': sorted(
                self.user_naming_conventions.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'recent_false_positives': [
                {'text': fp.text, 'reason': fp.reason}
                for fp in self.false_positives[-5:]
            ],
        }


def create_sample_codebase(base_path: Path) -> None:
    """Create sample codebase for learning demonstration."""
    
    (base_path / "src" / "auth").mkdir(parents=True)
    (base_path / "src" / "db").mkdir(parents=True)
    
    # File with consistent naming
    (base_path / "src" / "auth" / "login.py").write_text('''
class Authenticator:
    def __init__(self):
        self.user_password = "secret123"
        self.api_key = "key456"
    
    def verify(self, input_password):
        return input_password == self.user_password
''')
    
    (base_path / "src" / "auth" / "sso.py").write_text('''
class SSOService:
    def __init__(self):
        self.sso_secret = "sso_secret_value"
        self.auth_token = "token123"
''')
    
    (base_path / "src" / "db" / "connection.py").write_text('''
class DBConnection:
    def __init__(self):
        self.db_password = "db_pass_here"
        self.connection_string = "postgresql://..."
''')
    
    # File with different naming (to show learning)
    (base_path / "src" / "legacy.py").write_text('''
# Legacy code with different patterns
LEGACY_PASSWD = "legacy123"
OLD_SECRET_KEY = "old_key_value"
''')


def main():
    print("=" * 80)
    print("LLX Privacy: Behavioral Analysis & Pattern Learning")
    print("=" * 80)
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        codebase_path = Path(tmpdir) / "sample_project"
        learning_file = Path(tmpdir) / "learning_data.json"
        
        # Create sample codebase
        print("\n1. CREATING SAMPLE CODEBASE")
        print("-" * 60)
        create_sample_codebase(codebase_path)
        
        print("Codebase structure:")
        for f in codebase_path.rglob("*.py"):
            print(f"  {f.relative_to(codebase_path)}")
        
        # Initialize behavioral detector
        print("\n2. INITIALIZING BEHAVIORAL DETECTOR")
        print("-" * 60)
        
        detector = BehavioralPasswordDetector(learning_file)
        
        print("Initial state:")
        stats = detector.get_learning_stats()
        print(f"  Patterns learned: {stats['total_patterns_learned']}")
        print(f"  False positives: {stats['false_positives_recorded']}")
        print(f"  Naming conventions: {stats['naming_conventions_tracked']}")
        
        # Learn from codebase
        print("\n3. LEARNING FROM CODEBASE")
        print("-" * 60)
        
        learn_stats = detector.learn_from_codebase(codebase_path)
        
        print(f"Analysis complete:")
        print(f"  Files analyzed: {learn_stats['files_analyzed']}")
        print(f"  Patterns found: {learn_stats['patterns_found']}")
        
        print("\nDetected naming conventions:")
        for name, count in sorted(
            learn_stats['naming_conventions'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {name}: {count} occurrences")
        
        # Show learned state
        print("\n4. POST-LEARNING STATE")
        print("-" * 60)
        
        stats = detector.get_learning_stats()
        print(f"Naming conventions tracked: {stats['naming_conventions_tracked']}")
        print("\nTop conventions learned:")
        for name, count in stats['top_naming_conventions']:
            print(f"  {name}: {count} times")
        
        # Demonstrate adaptive confidence
        print("\n5. ADAPTIVE CONFIDENCE CALCULATION")
        print("-" * 60)
        
        test_cases = [
            ("user_password", "secret123", 0.7),
            ("random_var", "password_value", 0.5),
            ("db_password", "db_secret", 0.8),
            ("unknown_var", "some_value", 0.5),
        ]
        
        print("Testing adaptive confidence:")
        for var_name, value, base_conf in test_cases:
            adaptive = detector.calculate_adaptive_confidence(
                value, var_name, base_conf
            )
            adjustment = "↑" if adaptive > base_conf else "↓" if adaptive < base_conf else "="
            print(f"  {var_name:<20} base={base_conf:.2f} → adaptive={adaptive:.2f} {adjustment}")
        
        # Demonstrate false positive learning
        print("\n6. FALSE POSITIVE LEARNING")
        print("-" * 60)
        
        # Report some false positives
        detector.report_false_positive(
            text="test_password",
            context="def test_password():",
            reason="It's a test function, not a password",
        )
        
        detector.report_false_positive(
            text="get_password_hash",
            context="def get_password_hash(password):",
            reason="Function name, not a password value",
        )
        
        print("Reported false positives:")
        for fp in detector.false_positives:
            print(f"  - '{fp.text}': {fp.reason}")
        
        # Check if detector recognizes them
        print("\nChecking if detector recognizes false positives:")
        check_cases = [
            "test_password",
            "get_password_hash",
            "real_secret_123",
        ]
        
        for case in check_cases:
            is_fp = detector.is_false_positive(case, "")
            status = "✓ FALSE POSITIVE" if is_fp else "✗ Likely real password"
            print(f"  '{case}': {status}")
        
        # Generate custom patterns
        print("\n7. GENERATED CUSTOM PATTERNS")
        print("-" * 60)
        
        custom_patterns = detector.generate_custom_patterns()
        print(f"Generated {len(custom_patterns)} custom patterns:")
        for i, pattern in enumerate(custom_patterns[:5], 1):
            print(f"  {i}. {pattern[:60]}...")
        
        # Save and reload demonstration
        print("\n8. PERSISTENCE DEMONSTRATION")
        print("-" * 60)
        
        detector._save_learning()
        
        print(f"Learning data saved to: {learning_file}")
        print(f"File size: {learning_file.stat().st_size} bytes")
        
        # Create new detector from saved data
        new_detector = BehavioralPasswordDetector(learning_file)
        
        print("\nReloaded detector stats:")
        new_stats = new_detector.get_learning_stats()
        print(f"  Patterns: {new_stats['total_patterns_learned']}")
        print(f"  Naming conventions: {new_stats['naming_conventions_tracked']}")
        print(f"  False positives: {new_stats['false_positives_recorded']}")
        
        # Show learning data content
        print("\nLearning data sample:")
        data = json.loads(learning_file.read_text())
        print(f"  Top naming convention: {list(data['naming_conventions'].items())[0]}")
    
    print("\n" + "=" * 80)
    print("Behavioral Analysis Benefits:")
    print("  ✓ Learns from your specific codebase patterns")
    print("  ✓ Reduces false positives over time")
    print("  ✓ Adapts confidence based on context")
    print("  ✓ Generates custom patterns for your conventions")
    print("  ✓ Persists learning across sessions")
    print("=" * 80)


if __name__ == "__main__":
    main()
