# llx

Intelligent LLM model router driven by real code metrics — successor to preLLM

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Intent](#intent)

## Metadata

- **name**: `llx`
- **version**: `0.1.57`
- **python_requires**: `>=3.13`
- **license**: MIT
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

## Source Map

- my-api/test_api.py
- my-api/monitoring.py
- my-api/tests/test_my_api.py
- my-api/__init__.py
- my-api/models.py
- my-api/main.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/version.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/cli.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/__init__.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/__main__.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/parser.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/main.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/variables.py
- my-api/.venv/lib/python3.13/site-packages/dotenv/ipython.py
- my-api/.venv/lib/python3.13/site-packages/referencing/exceptions.py
- my-api/.venv/lib/python3.13/site-packages/referencing/retrieval.py
- my-api/.venv/lib/python3.13/site-packages/referencing/tests/test_exceptions.py
- my-api/.venv/lib/python3.13/site-packages/referencing/tests/test_core.py
- my-api/.venv/lib/python3.13/site-packages/referencing/tests/test_referencing_suite.py
- my-api/.venv/lib/python3.13/site-packages/referencing/tests/__init__.py
- my-api/.venv/lib/python3.13/site-packages/referencing/tests/test_retrieval.py
- my-api/.venv/lib/python3.13/site-packages/referencing/tests/test_jsonschema.py
- my-api/.venv/lib/python3.13/site-packages/referencing/_core.py
- my-api/.venv/lib/python3.13/site-packages/referencing/__init__.py
- my-api/.venv/lib/python3.13/site-packages/referencing/jsonschema.py
- my-api/.venv/lib/python3.13/site-packages/referencing/_attrs.py
- my-api/.venv/lib/python3.13/site-packages/referencing/typing.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_api.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/http2.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/interfaces.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/__init__.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/http_proxy.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/connection.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/http11.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/socks_proxy.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_sync/connection_pool.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_utils.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/__init__.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_trace.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_models.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_exceptions.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/auto.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/trio.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/base.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/mock.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/__init__.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/anyio.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_backends/sync.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_synchronization.py
- my-api/.venv/lib/python3.13/site-packages/httpcore/_async/http2.py
