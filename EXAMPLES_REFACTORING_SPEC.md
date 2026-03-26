# LLX Examples Refactoring Specification

## Cel
Uproszczenie wszystkich przykładów w `examples/*` do jednolitej, prostej postaci opartej na komendach LLX.

## Obecny stan
- Przykłady używają rozbudowanych skryptów bash
- Każdy przykład ma własną logikę i konfigurację
- Brak spójności między przykładami

## Docelowy stan
- Wszystkie przykłady używają prostych skryptów (max 30 linii)
- Cała logika jest w LLX, nie w skryptach
- Spójny interfejs i użytkowanie

## Specyfikacja uproszczonego przykładu

### 1. Struktura katalogu
```
examples/[example-name]/
├── run.sh              # Prosty skrypt uruchomieniowy (max 30 linii)
├── README.md           # Dokumentacja przykładu
├── QUICKSTART.md       # Krótki przewodnik (opcjonalnie)
├── setup-aliases.sh    # Alias dla powłoki (opcjonalnie)
└── [example-files]     # Pliki specyficzne dla przykładu
```

### 2. Skrypt run.sh (wymagany)
Maksymalnie 30 linii, zawiera:
```bash
#!/bin/bash
# Simple LLX workflow - all logic handled by LLX

set -e
# Kolory i zmienne
DESCRIPTION="${1:-}"
# Użycie llx plan all lub prostych komend LLX
```

### 3. Wymagania dotyczące LLX

#### 3.1. Komenda `llx plan all`
Musi obsługiwać:
- Dowolny typ projektu (nie tylko API)
- Konfigurację przez zmienne środowiskowe
- Różne profile modeli
- Opcjonalne uruchomienie i monitorowanie

#### 3.2. Konfiguracja domyślna
Wszystkie przykłady powinny używać:
```bash
LLX_DEFAULT_PROFILE=cheap
LLX_DEFAULT_SPRINTS=8
LLX_DEFAULT_FOCUS=[typ-zależny-od-przykładu]
```

#### 3.3. Elastyczność parametrów
Komendy LLX muszą akceptować:
- Różne typy generowanych projektów
- Konfigurację specyficzną dla przykładu
- Opcjonalne parametry przez CLI lub .env

## Kategoria przykładów i wymagania

### Kategoria 1: API Examples
- `python-api/` (już zrefaktoryzowany)
- `fastapi-crud/`
- `graphql-api/`
- `microservice/`

Wymagania:
- Domyślny focus: `api`
- 8 sprintów (projekt, CRUD, testy, deployment, CI/CD, monitoring, docs, optymalizacja)
- Generowanie: FastAPI, Express, etc.

### Kategoria 2: Web App Examples
- `react-app/`
- `vue-dashboard/`
- `nextjs-blog/`

Wymagania:
- Domyślny focus: `webapp`
- 6 sprintów (setup, components, routing, state, deployment, optimization)
- Generowanie: React, Vue, Next.js

### Kategoria 3: CLI/Tool Examples
- `cli-tool/`
- `data-processor/`
- `automation-script/`

Wymagania:
- Domyślny focus: `cli`
- 4 sprinty (setup, core logic, cli interface, packaging)
- Generowanie: Python Click, Node.js commander, etc.

### Kategoria 4: Data/ML Examples
- `data-pipeline/`
- `ml-model/`
- `analytics-dashboard/`

Wymagania:
- Domyślny focus: `data` lub `ml`
- 6-8 sprintów (data ingestion, processing, model, validation, deployment, monitoring)
- Generowanie: Pandas, Scikit-learn, TensorFlow, etc.

## Implementacja w LLX

### 1. Rozszerzenie `llx plan all`
```python
@plan_app.command("all")
def plan_all(
    description: str,
    output_dir: str = "./my-project",
    profile: str = "cheap",
    project_type: Optional[str] = None,  # NOWE!
    framework: Optional[str] = None,     # NOWE!
    # ... istniejące parametry
):
```

### 2. Konfiguracja typów projektów
Nowy plik: `llx/configs/project_types.yaml`
```yaml
project_types:
  api:
    default_focus: "api"
    default_sprints: 8
    frameworks: ["fastapi", "express", "flask", "django"]
  webapp:
    default_focus: "webapp"
    default_sprints: 6
    frameworks: ["react", "vue", "nextjs", "angular"]
  cli:
    default_focus: "cli"
    default_sprints: 4
    frameworks: ["click", "commander", "clap"]
  data:
    default_focus: "data"
    default_sprints: 6
    frameworks: ["pandas", "polars", "spark"]
```

### 3. Szablony generowania
Rozszerzenie `llx/configs/planfile_config.yaml`:
```yaml
code:
  templates:
    api:
      sprint_files:
        1: {file: "main.py", prompt: "..."}
        # ...
    webapp:
      sprint_files:
        1: {file: "App.jsx", prompt: "..."}
        # ...
```

### 4. Wykrywanie typu projektu
Automatyczne wykrywanie na podstawie:
- Nazwy katalogu (`*-api`, `*-app`, `*-cli`)
- Zawartości plików (package.json, requirements.txt)
- Konfiguracji w `.llx-project-type`

## Plan migracji

### Faza 1: Przygotowanie LLX (tydzień 1)
1. Rozszerzyć `llx plan all` o parametry `project_type` i `framework`
2. Dodać konfigurację typów projektów
3. Zaktualizować szablony generowania
4. Testy jednostkowe

### Faza 2: Migracja przykładów (tydzień 2)
1. Stworzyć listę wszystkich przykładów
2. Skategoryzować każdy przykład
3. Zrefaktoryzować po 2-3 przykłady dziennie
4. Testy integracyjne

### Faza 3: Dokumentacja i finalizacja (tydzień 3)
1. Zaktualizować dokumentację
2. Stworzyć przewodnik dla twórców przykładów
3. Code review wszystkich zmian
4. Wersja 1.0 uproszczonych przykładów

## Kryteria sukcesu

### Techniczne
- [ ] Wszystkie przykłady mają run.sh < 30 linii
- [ ] 100% przykładów używa `llx plan all`
- [ ] Brak logiki biznesowej w skryptach
- [ ] Wszystkie konfiguracje w .env lub LLX

### Użytkowe
- [ ] Spójny interfejs we wszystkich przykładach
- [ ] Łatwe dodawanie nowych przykładów
- [ ] Czytelna dokumentacja
- [ ] Przykłady działają "out of the box"

## Przykład refaktoryzacji

### Przed (python-api/run.sh - 100+ linii):
```bash
#!/bin/bash
# Complex script with:
# - Interactive prompts
# - Tool selection
# - Environment setup
# - Custom monitoring
# - Error handling
# - 100+ lines of code
```

### Po (python-api/run.sh - 25 linii):
```bash
#!/bin/bash
# Simple LLX workflow
set -e
DESCRIPTION="${1:-}"
if [ -n "$DESCRIPTION" ]; then
    llx plan all "$DESCRIPTION" --run
else
    echo "Usage: $0 \"description\""
fi
```

## Ryzyka i mitygacje

### Ryzyko 1: Utrata funkcjonalności
- Mitygacja: Wszystkie funkcje przenoszone do LLX
- Testy: Porównanie output przed/po refaktoryzacji

### Ryzyko 2: Zbyt duże zmiany w LLX
- Mitygacja: Iteracyjne wprowadzanie zmian
- Testy: Comprehensive test suite

### Ryzyko 3: Niekompatybilność wsteczna
- Mitygacja: Zachowanie stych komend jako deprecated
- Dokumentacja: Przewodnik migracji

## Podsumowanie

Refaktoryzacja do uproszczonej postaci zapewni:
1. **Spójność** - wszystkie przykłady działają tak samo
2. **Prostota** - łatwe zrozumienie i modyfikacja
3. **Skalowalność** - łatwo dodawać nowe przykłady
4. **Utrzymanie** - cała logika w LLX, nie w skryptach

Kluczowe jest przeniesienie logiki ze skryptów do LLX i zapewnienie, że `llx plan all` obsługuje wszystkie potrzebne przypadki użycia.
