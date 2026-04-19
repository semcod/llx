## Problem

GitHub Push Protection blokuje push do repozytorium gdy wykryje potencjalne wycieki sekretów (klucze API, tokeny, hasła).

### Typowe przyczyny blokady w LLX

1. **Przykłady kodu z fałszywymi kluczami** - dokumentacja i tutoriale często zawierają realistycznie wyglądające klucze
2. **Testowe dane** - mock dane mogą wyglądać jak prawdziwe sekrety
3. **Konfiguracje w YAML/JSON** - placeholder hasła i tokenów

### 1. Pre-push Secret Scanning

Dodaj stage do `pyqual.yaml` przed push:

```yaml
- name: secret-scan
  run: |
    # Sprawdź czy nie ma podejrzanych wzorców
    if command -v git-secrets &> /dev/null; then
      git secrets --scan
    elif command -v trufflehog &> /dev/null; then
      trufflehog git file://. --since-commit HEAD~1
    else
      # Fallback: proste sprawdzenie regex
      grep -rE "(sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL|sk_test_|ghp_|AKIA[0-9A-Z]{16})" . \
        --include="*.py" --include="*.yaml" --include="*.md" \
        --exclude-dir=.git --exclude-dir=.venv 2>/dev/null && \
        echo "WARNING: Potential secrets detected" || true
    fi
  when: always
  optional: true
  timeout: 60
```

### 2. Safe Placeholder Standard

Stwórz konwencję nazewnictwa dla fałszywych sekretów:

```python
# ❌ ZŁE - wygląda jak prawdziwy klucz
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"

# ✅ DOBRE - jasno wskazuje że to placeholder
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
STRIPE_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
STRIPE_KEY = "<YOUR_STRIPE_LIVE_KEY_HERE>"
```

### 3. GitHub Push Protection Bypass (tylko dla pewnych przypadków)

Jeśli masz pewność że fałszywy pozytyw:

```bash
# W pyqual.yaml stage 'push':
git push origin main --push-option=skip-secret-scan
# LUB dla starszych wersji git:
git push origin main --force-with-lease
```

**UWAGA**: Używaj tylko gdy masz 100% pewność że to fałszywy alarm!

# Sprawdź co GitHub wykrył
git push origin main 2>&1 | grep -A5 "secret"

# Lub użyj git log
git show --stat HEAD
```

# Zachowaj aktualny stan
git stash push -m "temp-before-fix"

# Ręcznie edytuj lub użyj sed:
sed -i 's/sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL[a-zA-Z0-9]*/sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL/g' plik.py

# Amend commit (zachowując oryginalną datę i autorstwo)
git commit --amend --no-edit

# Push
if git push origin main; then
  echo "Success!"
else
  # Jeśli nadal nie działa, sprawdź czy są inne pliki
  git stash pop
  echo "Manual fix required"
fi
```

# 1. Znajdź commit z problemem
git log --oneline --all | grep -i "privacy\|secret\|api"

# 2. Interaktywny rebase
COMMIT_HASH="abc123"  # hash PRZED problematycznym commitem
git rebase -i ${COMMIT_HASH}

# 3. Popraw pliki w zatrzymanym commicie
git add -A
git commit --amend --no-edit
git rebase --continue

# 4. Force push (ostrożnie!)
git push origin main --force-with-lease
```

### Scenariusz: Wiele commitów z problemem

Jeśli problem jest rozproszony na wiele commitów:

```bash
# Użyj git-filter-repo (bezpieczniejsze niż filter-branch)
git filter-repo --replace-text <(echo 'sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL[a-zA-Z0-9]*==>sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL')

# Albo dla konkretnych plików
git filter-repo --path examples/privacy/ --force
```

# Nowy moduł: pyqual/secrets_check.py

import re
from pathlib import Path
from typing import List, Tuple

SECRET_PATTERNS = [
    (r'sk_(live|test)_[a-zA-Z0-9]{24,}', 'Stripe API Key'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Token'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'[0-9a-f]{64}', 'Possible SHA/Hex secret'),
]

SAFE_MARKERS = [
    'EXAMPLE',
    'DUMMY',
    'PLACEHOLDER',
    'YOUR_',
    '<',  # <YOUR_KEY_HERE>
]

def check_file_for_secrets(filepath: Path) -> List[Tuple[int, str, str]]:
    """Returns (line_number, match_text, secret_type) for potential secrets."""
    findings = []
    content = filepath.read_text(encoding='utf-8', errors='ignore')
    
    for pattern, secret_type in SECRET_PATTERNS:
        for match in re.finditer(pattern, content):
            match_text = match.group()
            
            # Skip if marked as safe
            if any(marker in match_text for marker in SAFE_MARKERS):
                continue
                
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            findings.append((line_num, match_text[:50], secret_type))
    
    return findings

def pre_push_check(repo_path: Path) -> bool:
    """Run before push. Returns True if safe to proceed."""
    all_findings = []
    
    for py_file in repo_path.rglob('*.py'):
        findings = check_file_for_secrets(py_file)
        all_findings.extend([(py_file, f) for f in findings])
    
    if all_findings:
        print("⚠️  POTENTIAL SECRETS DETECTED:")
        for filepath, (line, text, stype) in all_findings[:10]:
            print(f"  {filepath}:{line} - {stype}")
        return False
    
    return True
```

# pyqual.yaml stage:
- name: sanitize-placeholders
  run: |
    # Auto-convert suspicious strings to safe placeholders
    find examples tests docs -name "*.py" -o -name "*.md" -o -name "*.yaml" 2>/dev/null | \
    xargs sed -i \
      -e 's/sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL[a-zA-Z0-9_]*/sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL/g' \
      -e 's/sk_test_[a-zA-Z0-9_]*/sk_test_EXAMPLE_DUMMY_KEY_NOT_REAL/g' \
      -e 's/ghp_[a-zA-Z0-9]*/ghp_EXAMPLE_DUMMY_TOKEN/g' \
      -e 's/AKIA[0-9A-Z]{16}/AKIAEXAMPLE12345678/g'
    
    git add -A 2>/dev/null || true
  when: always
  optional: true
  timeout: 30
```

## Checklist dla Deweloperów

Przed dodaniem przykładów z "sekretami":

- [ ] Używaj `EXAMPLE`, `DUMMY`, `PLACEHOLDER` w nazwach zmiennych
- [ ] Unikaj realistycznych formatów (np. `sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL...` wygląda jak prawdziwy Stripe)
- [ ] Dodaj komentarz `# This is a dummy/example key, not real`
- [ ] Użyj `<>` dla placeholderów: `<YOUR_API_KEY>`
- [ ] Uruchom `git push --dry-run` jeśli dostępne, lub force-push w PR zamiast bezpośrednio do main

## Linki

- [GitHub Push Protection Docs](https://docs.github.com/code-security/secret-scanning/working-with-secret-scanning-and-push-protection)
- [Git-secrets](https://github.com/awslabs/git-secrets)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)
