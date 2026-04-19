# Machine Learning-Based Privacy Examples

This directory contains advanced ML/NLP-based anonymization examples that go beyond simple regex patterns.

## Overview

These examples demonstrate ML-powered detection of sensitive data using:
- **Entropy Analysis** - Detecting random/high-entropy strings
- **Contextual Analysis** - Understanding code context for password detection
- **Hybrid Systems** - Combining ML + regex for maximum coverage
- **Behavioral Learning** - Learning from codebase patterns over time

### 1. Entropy ML Detection (`01_entropy_ml_detection.py`)

**Techniques**: Shannon entropy, randomness analysis, entropy-based classification

Detects sensitive data by analyzing randomness:
- High-entropy passwords (`p@ssw0rd!#2024Secure`)
- API keys (`sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL`)
- Encryption keys (hex strings)
- Session tokens (random strings)
- UUIDs vs secrets (distinguishing by context)

**Run**:
```bash
python3 01_entropy_ml_detection.py
```

**Output**:
```
Entropy Analysis:
  password123               → 3.28 entropy ✗ (not random enough)
  p@ssw0rd!#2024Secure      → 3.82 entropy ✓ (random)
  sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL        → 4.48 entropy ✓ (highly random)
  x9k#mP2$vL8@nQ4...        → 4.95 entropy ✓ (very random)

ML Detection Results:
  - entropy (api_key): postgresql://admin:p@ssw0rd... (confidence: 0.85)
  - contextual_password: Password: my$ecureP@ss123! (confidence: 0.70)
  - semantic_pii: Dr. John Smith (confidence: 0.80)
```

**Key Classes**:
- `EntropyAnalyzer` - Calculates Shannon entropy and classifies strings
- `MLBasedAnonymizer` - Combines entropy + context + semantic detection

### 2. Hybrid ML + Regex System (`02_hybrid_system.py`)

**Techniques**: Ensemble detection, result merging, multi-method comparison

Combines traditional regex with ML detection:
- Regex for known patterns (emails, phones, API keys)
- ML entropy for random strings regex misses
- ML context for passwords in code
- Smart merging to avoid duplicates

**Run**:
```bash
python3 02_hybrid_system.py
```

**Output**:
```
Detection Comparison:
  Scenario 1: Regex=4, ML=8, Hybrid=9 items
  Breakdown: regex=4, ml_entropy=2, ml_context=3

Method Comparison:
  Regex-only    → Known patterns, fast, precise
  ML-entropy    → Random strings, high entropy
  ML-context    → Contextual passwords
  Hybrid        → Maximum coverage, best of both
```

**Key Classes**:
- `HybridAnonymizer` - Orchestrates regex + ML detection
- `DetectionResult` - Unified result format

### 3. Contextual Password Detection (`03_contextual_passwords.py`)

**Techniques**: NLP pattern matching, context analysis, semantic role detection

Advanced password detection using code context:
- Variable naming patterns (`password`, `pwd`, `secret_key`)
- Assignment contexts (`password = ...`, `password: ...`)
- Dictionary keys (`{"password": "value"}`)
- Instance variables (`self.password = ...`)
- Comment hints (`# password: ...`)
- Function parameters (`def auth(password="default")`)

**Run**:
```bash
python3 03_contextual_passwords.py
```

**Output**:
```
Detected passwords:
  🔴 Variable: password
     Value: SuperSecretDBPass2024!
     Context: dict_key
     Confidence: 100%

  🔴 Variable: api_secret
     Value: a1b2c3d4e5f6789012345678901234567890abcdef
     Context: assignment
     Confidence: 100%

Risk Score: 0.90 (HIGH)
```

**Key Classes**:
- `ContextualPasswordDetector` - NLP-based password detection
- `PasswordCandidate` - Detection result with context

### 4. Behavioral Learning (`04_behavioral_learning.py`)

**Techniques**: Pattern learning, false positive tracking, adaptive confidence

Learns and adapts to your codebase:
- Learns naming conventions (`user_password`, `db_secret`)
- Tracks false positives to reduce them
- Adaptive confidence based on learned patterns
- Persistence across sessions

**Run**:
```bash
python3 04_behavioral_learning.py
```

**Output**:
```
Learning from codebase:
  Files analyzed: 4
  Naming conventions learned: 14
  
  user_password: 2 occurrences
  input_password: 2 occurrences
  db_password: 1 occurrences
  sso_secret: 1 occurrences

Adaptive confidence:
  user_password  base=0.70 → adaptive=0.80 ↑ (learned pattern)
  db_password    base=0.80 → adaptive=0.90 ↑ (learned pattern)
  unknown_var    base=0.50 → adaptive=0.50 = (not learned)

False positive learning:
  'test_password' → FALSE POSITIVE (test function)
  'get_password_hash' → FALSE POSITIVE (function name)
```

**Key Classes**:
- `BehavioralPasswordDetector` - Learns and adapts
- `LearnedPattern` - Stored pattern with examples
- `FalsePositiveRecord` - Tracked false positive

# Shannon entropy calculation
def calculate_entropy(text):
    char_counts = Counter(text)
    length = len(text)
    entropy = 0
    for count in char_counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

# entropy > 4.5  → High randomness (random strings)
```

**Real-world usage**:
```python
analyzer = EntropyAnalyzer()
result = analyzer.analyze_randomness("sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL")
print(f"Entropy: {result.entropy:.2f}")  # 4.48
print(f"Type: {result.likely_type}")      # api_key
```

# Detects based on surrounding code context
detector = ContextualPasswordDetector()
candidates = detector.detect_passwords(code)

### 3. Hybrid Detection

```python
hybrid = HybridAnonymizer()

# Combines multiple methods:
results = hybrid.hybrid_detect(text)

### 4. Behavioral Learning

```python
detector = BehavioralPasswordDetector(learning_file=Path("learning.json"))

# Learn from codebase
detector.learn_from_codebase(project_path)

# Adaptive confidence
confidence = detector.calculate_adaptive_confidence(
    text="secret123",
    var_name="user_password",
    base_confidence=0.7
)
## Detection Method Comparison

| Method | Catches | Misses | False Positives |
|--------|---------|--------|-----------------|
| Regex | Known patterns (email, phone, API key) | Unknown/random strings | Low |
| ML-Entropy | Random strings, high-entropy | Readable passwords | Medium |
| ML-Context | Passwords in code context | Without context indicators | Low |
| **Hybrid** | **Everything** | **Minimal** | **Controlled** |

## Running All ML Examples

```bash
cd /home/tom/github/semcod/llx

# Entropy analysis
python3 examples/privacy/ml/01_entropy_ml_detection.py

# Hybrid system
python3 examples/privacy/ml/02_hybrid_system.py

# Contextual detection
python3 examples/privacy/ml/03_contextual_passwords.py

# Behavioral learning
python3 examples/privacy/ml/04_behavioral_learning.py
```

## Integration with Main Privacy Module

These ML techniques can be integrated with the main `llx.privacy` module:

```python
from llx.privacy import Anonymizer
from llx.privacy.ml import EntropyAnalyzer, HybridAnonymizer

# Option 1: Use standalone ML detector
ml_anon = MLBasedAnonymizer()
findings = ml_anon.analyze_with_ml(text)

# Option 2: Use hybrid approach
hybrid = HybridAnonymizer()
anon_text, detections, mapping, stats = hybrid.hybrid_anonymize(text)

# Option 3: Use with ProjectAnonymizer
ctx = AnonymizationContext(project_path=".")
anonymizer = ProjectAnonymizer(ctx)
result = anonymizer.anonymize_project()

# Additional ML pass on anonymized content
ml = MLBasedAnonymizer()
for file_path, content in result.files.items():
    ml_findings = ml.analyze_with_ml(content)
    print(f"{file_path}: {len(ml_findings)} ML-detected items")
```

### Custom Entropy Thresholds

```python
analyzer = EntropyAnalyzer()
analyzer.HIGH_ENTROPY_THRESHOLD = 5.0  # Stricter
analyzer.MEDIUM_ENTROPY_THRESHOLD = 4.0
```

### Custom Context Patterns

```python
detector = ContextualPasswordDetector()

# Add custom password indicators
detector.PASSWORD_INDICATORS.extend([
    r'my_custom_pass',
    r'company_secret',
])

# Recompile patterns
detector.compiled_patterns = detector._compile_patterns()
```

### Learning from Feedback

```python
detector = BehavioralPasswordDetector(learning_file=Path("learning.json"))

# Report false positive
detector.report_false_positive(
    text="test_password",
    context="def test_password():",
    reason="It's a test function, not a password"
)

# Future detections will have lower confidence for similar patterns
confidence = detector.calculate_adaptive_confidence("test_password", "...", 0.8)
## Performance Considerations

| Method | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| Regex | Fast (~1ms) | High for known | Production, real-time |
| Entropy | Medium (~5ms) | High for random | Deep scanning |
| Context | Medium (~10ms) | High for code | Code analysis |
| Hybrid | Slower (~20ms) | Maximum | Security audits |
| Learning | Slow (one-time) | Adaptive | Long-term improvement |

## Security Notes

⚠️ **ML-based detection is probabilistic**:
- May miss some passwords (false negatives)
- May flag legitimate code (false positives)
- Use hybrid approach for production

✅ **Best practices**:
- Use regex as primary, ML as secondary
- Review ML detections before anonymizing
- Train behavioral detector on your codebase
- Regularly review and report false positives

## Next Steps

1. **Start with basics**: Run `01_entropy_ml_detection.py`
2. **Compare methods**: Run `02_hybrid_system.py`
3. **Explore contextual**: Run `03_contextual_passwords.py`
4. **Try learning**: Run `04_behavioral_learning.py`
5. **Integrate**: Use ML techniques in your project

## Documentation

- Full API docs: `../../docs/PRIVACY.md`
- Basic examples: `../basic/`
- Project examples: `../project/`
- Advanced examples: `../advanced/`
- Tests: `../../../tests/test_privacy*.py`
