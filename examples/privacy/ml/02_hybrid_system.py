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
            '["\\\']([A-Za-z0-9!@#$%^&*()_+\\-=\\[\\]{};:\\\'\\"|,.<>/?]{' + str(self.min_random_length) + ',})["\\\']',
            '[=:]\\s*([A-Za-z0-9!@#$%^&*()_+\\-=\\[\\]{};:\\\'\\"|,.<>/?]{' + str(self.min_random_length) + ',})(?:\\s*$|\\s*[,;})])',
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
            (r'(password|passwd|pwd)\\s*[=:] \\s*["\']?([^"\'\\s]{6,})', 'password_context'),
            (r'(secret|key|token)\\s*[=:] \\s*["\']?([A-Za-z0-9!@#$%^&*]{8,})', 'secret_context'),
            (r'(api[_-]?key)\\s*[=:] \\s*["\']?([A-Za-z0-9_-]{16,})', 'api_key_context'),
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
    
    def sort_detections(self, detections: list[DetectionResult]) -> list[DetectionResult]:
        """Sort detections by position in descending order for replacement."""
        return sorted(detections, key=lambda d: d.position[0], reverse=True)
    
    def create_anonymization_mask(self, detection: DetectionResult, index: int) -> str:
        """Create an anonymization mask for a detection."""
        if detection.detected_by == 'regex':
            mask = f"[REGEX_{detection.pattern_type.upper()}_{index:04d}]"
        else:
            mask = f"[ML_{detection.detected_by.upper()}_{index:04d}]"
        return mask
    
    def perform_anonymization(self, text: str, detections: list[DetectionResult]) -> tuple[str, dict]:
        """Perform anonymization by replacing detected text with masks."""
        anonymized = text
        mapping = {}
        for i, detection in enumerate(detections):
            original = detection.text
            mask = self.create_anonymization_mask(detection, i)
            start, end = detection.position
            anonymized = anonymized[:start] + mask + anonymized[end:]
            mapping[mask] = original
        return anonymized, mapping
    
    def collect_anonymization_stats(self, detections: list[DetectionResult]) -> dict:
        """Collect statistics on detections by type."""
        stats = {'regex': 0, 'ml_entropy': 0, 'ml_context': 0, 'ml_semantic': 0}
        for detection in detections:
            stats[detection.detected_by] += 1
        return stats
    
    def hybrid_anonymize(self, text: str) -> tuple[str, list[DetectionResult], dict]:
        """Anonymize using hybrid approach."""
        detections = self.hybrid_detect(text)
        sorted_detections = self.sort_detections(detections)
        anonymized, mapping = self.perform_anonymization(text, sorted_detections)
        stats = self.collect_anonymization_stats(detections)
        return anonymized, detections, stats