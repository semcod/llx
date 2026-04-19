# python-api-full

Kompletny przykład 2-krokowego workflow: **prompt → planfile → kod → uruchomienie → monitoring**.

## Wymagania

```bash
export OPENROUTER_API_KEY=sk-or-v1-...   # FREE konto na openrouter.ai
```

# 1. Wygeneruj planfile (free LLM)
llx plan generate . --profile free --sprints 4 --focus api -o strategy.yaml

# 2. Wygeneruj kod Python API (free LLM, sprint po sprincie)
llx plan code strategy.yaml ./my-api --profile free

# 3. Uruchom aplikację
llx plan run ./my-api

# 4. Monitoruj (health check + quality gates z planfile)
llx plan monitor strategy.yaml --url http://localhost:8000
```

## Lub uruchom cały flow jednym skryptem

```bash
bash run.sh "Zbuduj REST API do zarządzania zamówieniami restauracji"
```

## Co zostaje wygenerowane

```
my-api/
├── main.py           # FastAPI app (CRUD + /health)
├── models.py         # Pydantic models
├── test_api.py       # pytest tests
├── Dockerfile        # python:3.11-slim
├── requirements.txt
└── README.md
```

## Po wygenerowaniu

```bash
cd my-api
pip install -r requirements.txt
uvicorn main:app --reload

## Modele (free tier)

| Krok        | Model                                          |
|-------------|------------------------------------------------|
| plan code   | `openrouter/nvidia/nemotron-3-super-120b-a12b:free` |
| plan generate | `openrouter/nvidia/nemotron-3-super-120b-a12b:free` |

> Darmowe modele dostępne po rejestracji na [openrouter.ai](https://openrouter.ai)
