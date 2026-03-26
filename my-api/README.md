# Smoketest project v3

Improve API performance - Enhance API scalability

## Run
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Test
```bash
pytest test_api.py -v
```

## Docker
```bash
docker compose up --build
```
