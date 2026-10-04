# Hindsight Memory Bank API

Local daemon base URL: `http://127.0.0.1:8888` (systemd unit
`hindsight-api.service`), bank path prefix `/v1/default/banks/{bank_id}`.

## Contract discovery

```bash
curl -s http://127.0.0.1:8888/openapi.json | python3 -c "
import sys,json; d=json.load(sys.stdin)
for p in sorted(d['paths']): print(p, sorted(d['paths'][p].keys()))"
```

## Liveness and version

- `GET /health` → `{"status":"healthy","database":"connected",...}`
- `GET /version` → `{"api_version":"0.10.2","features":{"observations":true,"mcp":true,...}}`
- `GET /metrics`

Compare `api_version` with the client floor in
`~/.hermes/plugins/hindsight/pyproject.toml` (`hindsight-client>=0.10.1`).

## State

- `GET /stats` → `total_nodes`, `total_links`, `total_documents`,
  `nodes_by_fact_type` (`observation` / `world` / `experience`), `total_observations`,
  `pending_operations`, `failed_operations`, `operations_by_status`,
  `last_memory_write_at`.
- `GET /memories/list?limit=N` → `items[]`, each with `id`, `type`, `text`, `tags`.
- `GET /observations/scopes` → tag scopes with counts (useful to see what the
  current session already wrote).
- `GET /llm-requests/stats?period=7d` → per-bucket status + token totals; proves
  whether extraction is succeeding and at what latency.
- `GET /audit-logs`, `GET /audit-logs/stats` — may be empty; absence of entries is
  not evidence retention did not happen.

## Write

```bash
curl -s -X POST "$B/memories" -H 'Content-Type: application/json' \
  -d '{"items":[{"content":"...","tags":["hermes","probe"]}]}'
```

The body requires an `items` array; a top-level `content` key returns
`422 missing body.items`. `retain_async` on the server decides whether extraction
happens inline — expect tens of seconds per item because it is an LLM pass.

## Read

```bash
curl -s -X POST "$B/memories/recall" -H 'Content-Type: application/json' \
  -d '{"query":"...","budget":"low|mid|high","types":["observation"]}'
```

Response `results[]` carries `text`, `type`, `entities`, `tags`, and `scores`:

- `scores.semantic` — embedding similarity, roughly 0.4–0.7 on a small bank.
- `scores.reranker` — cross-encoder score; this is the discriminator.
- `scores.final` — blended ranking score.

A reranker score collapsing to ~1e-5 across all rows means the reranker found
nothing relevant, so result order is not meaningful signal for that query.

`POST /reflect` runs the LLM synthesis loop and returns a composed answer with
`based_on` and `usage`; it is the correct probe for "is the LLM endpoint alive and
can it read this bank".

## Delete — the hazard

`DELETE /memories` is operationId `clear_bank_memories`, summary "Clear memory
bank memories", described as a destructive operation that cannot be undone. Its
only parameter is an optional `?type=` filter. A body such as
`{"memory_ids":[...]}` is accepted and ignored.

There is no per-memory delete, no trash, no recover route. The bank profile
(disposition, background) survives a clear; every memory unit does not.

Backup and restore:

```bash
curl -s "$B/export?format=json" -o bank-$(date +%F).json   # before any clear
curl -s -X POST "$B/import" ...                            # the restore path
```

An export taken from an empty bank returns `{"version":"1","bank":null,...}` —
verify the file is non-trivial before relying on it.

## Mode and LLM ownership

`local_external` means the plugin connects to a daemon someone else started
(systemd unit, container, remote host). The `llm_provider` / `llm_model` /
`llm_base_url` keys in `~/.hermes/hindsight/config.json` are read only in
`local_embedded`; in `local_external` the daemon's own environment decides:

```
HINDSIGHT_API_LLM_PROVIDER=openai
HINDSIGHT_API_LLM_MODEL=myomniroute
HINDSIGHT_API_LLM_BASE_URL=http://127.0.0.1:7777/v1
HINDSIGHT_API_LLM_API_KEY=<gateway key>
```

Provider must be a real provider name (`openai`); `myomniroute` is a *model*
alias resolved by the gateway, not a provider. `api_url` still matters in this
mode — pin it to `http://127.0.0.1:8888` rather than the `localhost` default,
which can resolve to `::1` against an IPv4-bound daemon.

Useful bank-config knobs worth reading via `GET /config` before tuning:
`recall_budget_function` (`fixed` / `adaptive`), `recall_budget_fixed_*`,
`recall_max_tokens`, `recall_include_chunks`, `enable_reranking`,
`enable_auto_consolidation`, `consolidation_llm_batch_size`,
`consolidation_llm_parallelism`, `retain_extraction_mode`.

## Upstream docs

- <https://hindsight.vectorize.io/sdks/integrations/hermes> — config table,
  mode semantics, `recall_types` behavior change, plugin pin/update flow.
- <https://hindsight.vectorize.io/sdks/integrations/skills> — skill installer and
  the local/cloud deployment split.