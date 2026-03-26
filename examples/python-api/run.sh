#!/usr/bin/env bash
# examples/python-api-full/run.sh
#
# Kompletny workflow: prompt → planfile → kod → uruchomienie → monitoring
# Użycie: bash run.sh ["Opis projektu"]
#
set -e

DESCRIPTION="${1:-Zbuduj REST API do zarządzania listą zadań Todo z FastAPI}"
STRATEGY="strategy.yaml"
PROJECT="./my-api"
PORT=8000

# Locate llx in repo venv
LLX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LLX="${LLX_ROOT}/.venv/bin/llx"
PLANFILE="${LLX_ROOT}/../planfile/.venv/bin/planfile"

echo "═══════════════════════════════════════════"
echo "  Python API — planfile + llx workflow"
echo "═══════════════════════════════════════════"
echo "  Opis : $DESCRIPTION"
echo ""

# ── KROK 1: Generuj planfile ─────────────────────────────────
echo "▶ KROK 1: Generowanie planfile (LLM free tier)"
"$LLX" plan generate . \
    --profile free \
    --sprints 4 \
    --focus api \
    --output "$STRATEGY"

# Walidacja planfile (jeśli planfile jest dostępny)
if [ -x "$PLANFILE" ]; then
    echo ""
    "$PLANFILE" validate "$STRATEGY"
    "$PLANFILE" stats "$STRATEGY"
fi

echo ""

# ── KROK 2: Generuj kod ──────────────────────────────────────
echo "▶ KROK 2: Generowanie kodu Python API (LLM free tier)"
"$LLX" plan code "$STRATEGY" "$PROJECT" --profile free

echo ""

# ── KROK 3: Uruchom aplikację ────────────────────────────────
echo "▶ KROK 3: Uruchamianie API"
echo "  (w osobnym terminalu: llx plan run $PROJECT)"
echo ""
echo "  Aby uruchomić teraz:"
echo "    $LLX plan run $PROJECT"
echo ""
echo "  Aby monitorować (po uruchomieniu):"
echo "    $LLX plan monitor $STRATEGY --url http://localhost:$PORT"
echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ Gotowe! Projekt w: $PROJECT"
echo "═══════════════════════════════════════════"
