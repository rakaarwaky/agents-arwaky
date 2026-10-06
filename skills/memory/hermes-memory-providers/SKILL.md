---
name: hermes-memory-providers
description: Configures Hindsight memory for Hermes Agent. Use when setting LLM-learned agent memory provider.
metadata:
  tags:
    - hermes
    - memory
    - hindsight
    - plugins
    - setup
  related_skills:
    - hindsight
    - hermes-agent
    - agent-harness-connectors
---

# Hindsight — Hermes Memory Provider

Hindsight is an LLM-learning memory layer for AI agents. When deployed as a
Hermes memory provider, it replaces the built-in MEMORY.md/USER.md system with
knowledge-graph + entity-resolution + multi-strategy retrieval
(semantic / keyword / graph / temporal), consolidated "observations", and an
optional reflect agent loop that returns a synthesized answer.

Runs 100% locally: embedded PostgreSQL (pg0), local embedding + reranking
models. The one external dependency is an LLM endpoint (any
OpenAI-compatible — e.g. OmniRoute on 127.0.0.1:7777) used for fact
extraction and reflection.

## What It Gives You

- **System prompt injection** — relevant memories prefetched before each LLM call
- **Retain** — conversation turns auto-stored; LLM extracts facts, entities,
  reasoning, and emotions (not just raw strings)
- **Observations** — deduplicated, evidence-grounded consolidated beliefs with
  proof counts and freshness flags, refined as new facts arrive
- **Recall** — four parallel strategies: semantic, keyword, entity graph,
  temporal
- **Reflect** — LLM agent loop that returns a synthesized *answer* (not just
  data), weighing observations against raw facts
- **Tools** auto-injected into the model's tool surface: the
  `hindsight_*` tool family plus per-turn auto capture. Read
  `hindsight-integrations/hermes/plugin.yaml` in the vendor checkout for the
  authoritative list.
- **Auto per-turn capture** — enabled via `auto_retain` / `auto_recall`

All without touching Hermes core — deployed purely through the plugin
directory (`~/.hermes/plugins/hindsight`).

## Quick Check

```bash
hermes memory status
```

## Install

### Step 1 — Install the plugin from the Hermes catalog

```bash
hermes plugins install hindsight --enable
```

This clones `vectorize-io/hindsight` (subdir `hindsight-integrations/hermes`)
into `~/.hermes/plugins/hindsight` and installs `hindsight-client` +
`hindsight-embed` into Hermes' venv.

### Step 2 — Choose the mode

Config lives in `~/.hermes/hindsight/config.json` + `~/.hermes/.env`.

| Mode | When | Needs |
|------|------|-------|
| `local_embedded` | fully local; pg0 + local embeddings on host | LLM API key (any OpenAI-compatible) |
| `local_external` | self-hosted Hindsight server | API URL + LLM key |
| `cloud` | Hindsight Cloud (Vectorize) | API key |

`local_embedded` with OmniRoute as the LLM:

```json
{
  "mode": "local_embedded",
  "bank_id": "raka",
  "memory_mode": "hybrid",
  "auto_retain": true,
  "auto_recall": true,
  "recall_budget": "mid",
  "recall_types": "observation,world,experience",
  "llm_provider": "openai_compatible",
  "llm_base_url": "http://127.0.0.1:7777/v1",
  "llm_model": "auto/best-fast"
}
```

```bash
# ~/.hermes/.env
HINDSIGHT_LLM_API_KEY=<your-omniroute-key>
```

The embedded daemon starts on first use (spawns the `hindsight-api` process
against pg0) and stops after ~5 min idle. Set `HINDSIGHT_NO_AUTOSTOP=true` to
keep it resident.

### Step 3 — Activate

```bash
hermes config set memory.provider hindsight
```

### Step 4 — (Optional) Disable built-in memory

Hindsight is additive by default. To make it the sole memory system:

```yaml
memory:
  memory_enabled: false
  user_profile_enabled: false
```

### Step 5 — Verify

```bash
hermes memory status   # Should show "Provider: hindsight"
```

Test in a conversation:

```bash
hermes chat -q "Remember that I love apples. What do I love?"
```

## MCP

Hindsight ships a local MCP server (`hindsight-local-mcp`, entry point in the
`hindsight-api` workspace member) exposing the `hindsight_*` tool family —
usable with any MCP-compatible client. For Hermes, prefer the provider plugin
(deeper integration: pre-LLM injection, auto capture, hooks); MCP is the
generic fallback.

From the `agents-arwaky` repo the launcher is installed with
`aa tool install hindsight` (writes `~/.local/bin/hindsight-local-mcp`).

## Switching Back

```bash
hermes config set memory.provider memory   # back to built-in
```

Then restart Hermes.

## Data Location

- Embedded pg0 instance: `~/.pg0/instances/hindsight-embed-<profile>/`
- Profile env: `~/.hindsight/profiles/<profile>.env`
- Hermes plugin config: `~/.hermes/hindsight/config.json`

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| Plugin listed but `unavailable` | Missing `hindsight-client`/`hindsight-embed` in Hermes venv; re-run `hermes plugins install hindsight`. |
| Retain/recall returns nothing | Needs at least one retain cycle; extraction is an LLM call — check `HINDSIGHT_LLM_API_KEY` + `llm_base_url` reachability. |
| LLM JSON decode errors on retain | Weak routed model; set `HINDSIGHT_API_LLM_STRICT_SCHEMA=true` or point `llm_model` at a stronger OmniRoute combo. |
| Daemon won't start | `hindsight-api` not on PATH; it falls back to `uvx hindsight-api` (first run downloads deps). Install permanently for speed. |

## References

- `hermes-agent` skill — general Hermes setup, config, and plugin system.
- `agent-harness-connectors` skill — how `aa connect` registers MCP servers
  and injects `OMNIROUTE_*` env for each harness.
- `vendor/hindsight` submodule — upstream source (uv workspace; entry
  points `hindsight-api`, `hindsight-local-mcp` in the `hindsight-api` member).
