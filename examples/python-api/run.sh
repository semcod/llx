#!/usr/bin/env bash
# python-api example: 2-step workflow
# Krok 1: planfile generuje plan YAML
# Krok 2: llx plan apply wykonuje plan krok po kroku

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Resolve llx ───────────────────────────────────────────────
if ! command -v llx &>/dev/null; then
    LLX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    if [ -x "$LLX_ROOT/.venv/bin/llx" ]; then
        shopt -s expand_aliases
        alias llx="$LLX_ROOT/.venv/bin/llx"
    else
        export PYTHONPATH="$LLX_ROOT"
        shopt -s expand_aliases
        alias llx="$LLX_ROOT/.venv/bin/python3 -m llx"
    fi
fi

# ── Resolve planfile ──────────────────────────────────────────
if ! command -v planfile &>/dev/null; then
    PF_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../planfile" && pwd)"
    if [ -x "$PF_ROOT/.venv/bin/planfile" ]; then
        shopt -s expand_aliases
        alias planfile="$PF_ROOT/.venv/bin/planfile"
    else
        export PYTHONPATH="$PF_ROOT:$PYTHONPATH"
        shopt -s expand_aliases
        alias planfile="$PF_ROOT/.venv/bin/python3 -m planfile"
    fi
fi

OUTPUT_STRATEGY="api-strategy.yaml"
PROJECT_DIR="./my-api"

echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Python API — 2-krokowy Workflow planfile + llx  ${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"

# ─────────────────────────────────────────────────────────────
# KROK 1: planfile generuje strategię
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}━━━ KROK 1: Generowanie planu (planfile) ━━━${NC}"

if [ -f "$OUTPUT_STRATEGY" ]; then
    echo -e "  Używam istniejącego pliku: ${OUTPUT_STRATEGY}"
else
    echo -e "  Generuję szablon dla projektu API..."
    planfile template api backend --output "$OUTPUT_STRATEGY"
    echo -e "  ${GREEN}✓ Wygenerowano: ${OUTPUT_STRATEGY}${NC}"
fi

echo -e "\n  Walidacja strategii..."
planfile validate "$OUTPUT_STRATEGY"
echo -e "  ${GREEN}✓ Strategia jest poprawna${NC}"

echo -e "\n  Statystyki planu:"
planfile stats "$OUTPUT_STRATEGY"

# ─────────────────────────────────────────────────────────────
# KROK 2: llx wykonuje plan krok po kroku
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}━━━ KROK 2: Wykonanie planu (llx plan apply) ━━━${NC}"
echo -e "  Tryb: ${BLUE}dry-run${NC} (usuń --dry-run aby realnie wykonać)"
echo ""

mkdir -p "$PROJECT_DIR"

llx plan apply "$OUTPUT_STRATEGY" "$PROJECT_DIR" --dry-run

echo ""
echo -e "${GREEN}✅ Przykład ukończony!${NC}"
echo ""
echo -e "${BLUE}Następne kroki:${NC}"
echo "  1. Przejrzyj plan: planfile review $OUTPUT_STRATEGY"
echo "  2. Uruchom realnie: llx plan apply $OUTPUT_STRATEGY $PROJECT_DIR"
echo "  3. Sprawdź sprint 1: llx plan apply $OUTPUT_STRATEGY $PROJECT_DIR --sprint 1"
