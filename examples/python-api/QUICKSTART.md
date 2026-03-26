# LLX Quick Start Guide

## Szybki start z LLX

### 1. Konfiguracja
```bash
# Skopiuj plik konfiguracyjny
cp .env.example .env

# Uzupełnij klucze API (minimum jeden)
# OpenRouter jest polecany dla darmowych modeli
nano .env
```

### 2. Generowanie projektu API
```bash
# Interaktywny tryb (z podpowiedziami)
./run.sh

# Lub bezpośrednio z opisem
./run.sh "Zbuduj REST API do zarządzania zamówieniami restauracji"
```

### 3. Zarządzanie projektem
```bash
# Uruchom aplikację
llx plan run ./my-api

# Monitoruj w innym terminalu
llx plan monitor strategy.yaml

# Generuj ponownie kod
llx plan code strategy.yaml ./my-api-v2 --profile cheap
```

### 4. Dostępne narzędzia
- **llx** - wbudowane narzędzie (domyślne)
- **aider** - AI pair programming
- **cursor** - IDE z integracją AI

### 5. Środowiska
- **local** - lokalny development (domyślny)
- **docker** - konteneryzacja
- **cloud** - deployment do chmury

### 6. Profile modeli
- **free** - darmowe modele (ograniczone)
- **cheap** - tanie modele (polecane)
- **balanced** - zbalansowane
- **premium** - najlepsze modele

## Przykład wygenerowanego projektu

```
my-api/
├── main.py              # Główna aplikacja FastAPI
├── models.py            # Modele Pydantic
├── test_api.py          # Testy jednostkowe i integracyjne
├── Dockerfile           # Konfiguracja kontenera
├── docker-compose.yml   # Kompletny stack z bazą danych
├── .github/workflows/   # CI/CD pipeline
├── monitoring.py        # Konfiguracja monitoringu
├── docs/api.md          # Dokumentacja API
├── requirements.txt     # Zależności Python
└── README.md           # Instrukcja uruchomienia
```

## Wskazówki
- Używaj profilu **cheap** dla lepszej jakości
- Opis projektu wpływa na wygenerowany kod
- Wszystkie ustawienia są w .env
- Monitorowanie działa automatycznie w tle

## Skróty i Aliasy

### Szybka instalacja aliasów
```bash
# Dodaj aliasy do powłoki
./setup-aliases.sh

# Załaduj aliasy
source ~/.bashrc  # lub ~/.zshrc
```

### Dostępne aliasy
```bash
llx-gen      # Generuj strategię (8 sprintów, cheap)
llx-code     # Generuj kod
llx-run      # Uruchom API
llx-mon      # Monitoruj aplikację
llx-api      # Szybki start z uvicorn
llx-new      # Nowa strategia API
```

### Przykładowy workflow z aliasami
```bash
# 1. Generuj strategię z opisem
llx-gen --description "API do zarządzania zadaniami"

# 2. Generuj kod
llx-code

# 3. Uruchom
llx-run

# 4. Monitoruj w innym terminalu
llx-mon
```
