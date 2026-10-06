# Hindsight repo & dev context

Upstream: `vendor/hindsight` (git submodule, uv workspace, pinned to an
explicit commit).

## Layout

- `hindsight-api/` — workspace member; entry points `hindsight-api`,
  `hindsight-worker`, `hindsight-local-mcp` (local MCP server), `hindsight-admin`.
- `hindsight-api-slim/` — core API without ML models (pair with hosted
  embeddings/reranker or ONNX local backend).
- `hindsight-all/` / `hindsight-all-slim/` — bundles incl. local ML.
- `hindsight-embed/` — embedded daemon manager (pg0). Entry point
  `hindsight-embed`.
- `hindsight-clients/python/` — `hindsight-client` + `hindsight-client-api`.
- `hindsight-integrations/hermes/` — the Hermes plugin (installed from the
  catalog by `hermes plugins install hindsight`).

## Data & storage

- Embedded Postgres: `~/.pg0/instances/hindsight-embed-<profile>/`
- Profile env: `~/.hindsight/profiles/<profile>.env`
- Config: `~/.hermes/hindsight/config.json` (mode, bank_id, llm_* keys)
- LLM key: `~/.hermes/.env` → `HINDSIGHT_LLM_API_KEY`

## Modes

| mode | storage | needs |
|------|---------|-------|
| `local_embedded` | pg0 + local embed/rerank | LLM API key |
| `local_external` | self-hosted server | API URL + LLM key |
| `cloud` | Vectorize cloud | API key |

## LLM

Retain/reflect/observation consolidation consume an LLM endpoint. Any
OpenAI-compatible gateway works. For this repo: OmniRoute on
127.0.0.1:7777 (see `omniroute` skill), `llm_provider=openai_compatible`,
`llm_model=auto/best-fast` (route to a stronger combo for strict JSON).

## Hermes provider lifecycle

- Plugin installed from catalog → `~/.hermes/plugins/hindsight`
- `hermes config set memory.provider hindsight` activates
- Embedded daemon auto-starts on first use, stops after ~5 min idle
  (`HINDSIGHT_NO_AUTOSTOP=true` to keep resident)
- Tools: `hindsight_*` family + per-turn auto capture (auto_retain/auto_recall)
