---
name: omniroute
description: OmniRoute free AI gateway over OpenAI REST, 350+ providers with 150+ free tiers. Use when mentioning OmniRoute, OMNIROUTE_URL, auto/best-free, free-tier routing, checking a model context length (ctx) on the gateway, or building a model tier list / ranking the gateway model catalog. 9router (port 20128) is the second supported gateway vendor alongside OmniRoute.
when-to-use: "Use when asking about OmniRoute, OMNIROUTE_URL, OMNIROUTE_KEY, auto/best-free or other combo routing, free-tier routing, adding a custom OpenAI-compatible provider, managing the OmniRoute daemon (status, restart, logs), fixing OmniRoute errors, or building a model tier list / ranking the gateway's model catalog."
argument-hint: "[setup | models [--free] [--search <q> | --json] | combo <list|switch|create|delete|suggest> | providers <add|list|test|edit|remove|test-all> | aa omniroute <status|restart|logs|models|service-install> | doctor | keys | cost]"
metadata:
  tags:
    - ai-gateway
    - model-catalog
    - tierlist
---

# OmniRoute

Free-first AI gateway exposing OpenAI-compatible REST. Hundreds of providers, most with a
free tier, plus combo routing that picks a model per task shape.

Host-native — no Docker, no container. Installed from npm, pinned by `vendor/omniroute`.

## Setup

```bash
export OMNIROUTE_URL="http://127.0.0.1:7777"      # dashboard and API share one port
export OMNIROUTE_KEY="sk-..."                      # from the dashboard, or `omniroute keys`
```

All requests: `${OMNIROUTE_URL}/v1/...` with header `Authorization: Bearer ${OMNIROUTE_KEY}`.

Verify: `curl $OMNIROUTE_URL/v1/models -H "Authorization: Bearer $OMNIROUTE_KEY"`

### Config lives in `~/.omniroute/.env`

OmniRoute owns its own working directory — `~/.omniroute/` holds `.env`, `storage.sqlite`,
and `logs/`. This is **not** the repo's `~/.config/<tool>/` layout, and it is deliberate:
upstream reads `.env` from its working directory, so pointing the unit anywhere else
silently loses the settings.

`STORAGE_ENCRYPTION_KEY` in that file encrypts every provider credential in
`storage.sqlite`. **Never rotate it and never let a tool regenerate it** — the database
becomes unreadable while still looking healthy. Edit the file by hand; the `aa` verbs never
write to it.

Override the port with `OMNIROUTE_PORT`, or edit `PORT` in `~/.omniroute/.env` and restart.

## Combo routing

The reason to use OmniRoute over a plain provider list — combos pick a model by task shape
instead of you naming one:

```bash
curl $OMNIROUTE_URL/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"auto/best-free","messages":[{"role":"user","content":"hi"}]}'
```

| Combo | Use for |
|---|---|
| `auto/best-free` | only free tiers — cheapest and safest |
| `auto/best-coding` | coding tasks |
| `auto/best-fast` | low-latency replies |
| `auto/best-chat` | general conversation |

## Reference sub-scenarios

- [`references/model-tier-list.md`](references/model-tier-list.md) — build a model
  tier list / capability ranking from the OmniRoute `/v1/models` catalog (the
  "Discover models" data task against this gateway).
- [`references/omniroute-models-shape.md`](references/omniroute-models-shape.md) —
  the concrete `GET /v1/models` response shape and the full dedupe suffix list.

## Discover models

```bash
curl $OMNIROUTE_URL/v1/models          # everything currently routable
omniroute models --free                # free tiers only, via the CLI
```

To **rank or tier** the models returned by `/v1/models` into a capability
table (a model inventory / tier list), follow
[`references/model-tier-list.md`](references/model-tier-list.md).

## Provider keys

Most providers need no key — the free-tier catalogue is what makes the gateway useful out of
the box. Add keys with `omniroute setup` (walks through it and stores them in the database),
or via the dashboard at `http://127.0.0.1:7777`. Both write to `storage.sqlite`, so they need
no edit to `~/.omniroute/.env`.

`STORAGE_ENCRYPTION_KEY` encrypts stored credentials at rest. **Never change it**
once credentials exist; see Setup for the full warning.

[`references/custom-provider.md`](references/custom-provider.md) — add a custom
OpenAI-compatible provider, with management API and CLI examples.

## Manage the daemon

```bash
aa omniroute status            # process, systemd, ports, API readiness
aa omniroute restart           # needed after any env edit
aa omniroute logs              # journalctl tail
aa omniroute models            # /v1/models through the gateway
aa omniroute service-install   # 24/7 systemd user unit + enable-linger
```

Also upstream, for settings the `aa` verbs do not cover:

```bash
omniroute doctor              # environment + config diagnostics
omniroute keys                # mint/revoke API keys
omniroute cost                # spend report
omniroute status              # upstream's own view
```

## 9router sync

9router (port 20128) stores its runtime data in SQLite at `~/.9router/db/data.sqlite`
(not the JSON export files). The JSON files in `config/` are exports/backups.

When syncing OmniRoute providers/models/combos into 9router's SQLite:

- The `combos` table has a `kind` column that must be `'llm'` (not null). A null
  `kind` crashes the dashboard combos page with `t.includes is not a function`.
- Combo `models` is stored as a JSON string in the `models` column.
- Provider connections in 9router share the same IDs as OmniRoute's, so sync by
  updating existing rows rather than inserting duplicates.
- 9router requires a restart (`systemctl --user restart 9router`) after DB edits.

**Frontend crash with models present:** Even with `kind='llm'`, the combos page
may still crash (`t.includes is not a function`) when any combo has models. The
root cause is in the pre-built Next.js frontend (`page-*.js`), not the data.
The frontend is a compiled bundle in `.next-cli-build/` — it cannot be patched
without the source. If the page breaks after a sync, remove models from combos
(temporarily set `models='[]'`) to restore dashboard access, then investigate
the frontend separately.

**Never delete `.next-cli-build/`:** The 9router app requires this pre-built
cache to start. Deleting it causes `Could not find a production build`. Restore
by reinstalling: `npm install -g 9router` (recreates the cache).

## Errors

- Port already bound → something else holds 7777; check `ss -ltn | grep 7777`, then change
  `PORT` in `~/.omniroute/.env` and `aa omniroute restart`
- Configs unreadable after an upgrade → `STORAGE_ENCRYPTION_KEY` changed; restore the
  previous `~/.omniroute/.env`. Check `omniroute doctor`
- `omniroute serve` exits immediately → run `omniroute doctor`; the port is the usual cause
