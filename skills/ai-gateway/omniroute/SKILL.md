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

`STORAGE_ENCRYPTION_KEY` encrypts stored credentials at rest. **Never change it** once
credentials exist — every previously stored key becomes unreadable.

### Add a custom OpenAI-compatible provider (e.g. a third-party `api.x` gateway)

A custom provider = one **provider node** (base URL + optional auth headers, stored under
prefix) + one **provider connection** (the API key) + optional **manual model overrides**
(so the models are routable without a discovery call). Three parts:

```bash
# 1. Authenticate a dashboard session (password comes from ~/.omniroute/.env DASHBOARD_PASSWORD).
COOKIE=/tmp/omni-cookies.txt
curl -s -c "$COOKIE" http://127.0.0.1:7777/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"<DASHBOARD_PASSWORD>"}'

# 2a. Create the node (name + prefix are required; pick a short unique prefix).
NODE_ID=$(curl -s -b "$COOKIE" http://127.0.0.1:7777/api/provider-nodes \
  -H 'Content-Type: application/json' \
  -d '{"name":"YJS","prefix":"yjs","apiType":"chat","baseUrl":"https://api.yjs.im/v1","type":"openai-compatible"}' \
  | jq -r .node.id)

# 2b. Attach the API key as a connection, defaulting to a model.
curl -s -b "$COOKIE" http://127.0.0.1:7777/api/providers \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"$NODE_ID\",\"name\":\"yjs.im\",\"apiKey\":\"sk-...\",\"defaultModel\":\"<model-id>\"}"

# 2c. Activate it.
CONN_ID=<connection id from 2b>
curl -s -b "$COOKIE" -X PUT "http://127.0.0.1:7777/api/providers/$CONN_ID" \
  -H 'Content-Type: application/json' -d '{"isActive":true}'

# 3. Add manual model overrides (skips live discovery; safe for free/limited endpoints).
for M in deepseek-v4-flash-0731 deepseek-v4-flash-vision; do
  curl -s -b "$COOKIE" http://127.0.0.1:7777/api/provider-models \
    -H 'Content-Type: application/json' \
    -d "{\"provider\":\"$NODE_ID\",\"modelId\":\"$M\",\"source\":\"manual\",
         \"apiFormat\":\"chat-completions\",\"supportedEndpoints\":[\"chat\"],
         \"max_input_tokens\":65536,\"max_output_tokens\":8192}"
done

# 4. Verify: models appear under the prefix; try one through the gateway.
curl http://127.0.0.1:7777/v1/models -H "Authorization: Bearer $OMNIROUTE_KEY" \
  | jq -r '.data[].id' | grep '^yjs/'
curl http://127.0.0.1:7777/v1/chat/completions \
  -H "Authorization: Bearer $OMNIROUTE_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"yjs/deepseek-v4-flash-0731","messages":[{"role":"user","content":"ok"}]}'
```

Notes:

- Node `baseUrl` must end with `/v1` (the OpenAI-compatible root). Custom HTTP headers can
  be passed on the node (`customHeaders`) instead of the connection's key.
- A bare inference key (`OMNIROUTE_KEY` with only `["self:usage"]` scope) cannot write to
  the management API. Use the dashboard password session, a `manage`-scope key, or the local
  CLI token.
- No daemon restart is needed after node/connection/model writes; the gateway picks them up
  on the next request.

### CLI equivalents (when the wrapper is healthy)

The CLI mirrors the management API, so when the `omniroute` shell wrapper works you can do:

```bash
omniroute providers add yjs --credential sk-... --default-model deepseek-v4-flash-0731
omniroute models add yjs deepseek-v4-flash-0731 --api-format chat-completions
omniroute models add yjs deepseek-v4-flash-vision --api-format chat-completions
omniroute providers test yjs
```

If the `omniroute` shell wrapper errors out (`ModuleNotFoundError: surface_daemon_command`
on some installs), call the real entry directly:

```bash
node "$(npm root -g)/omniroute/bin/omniroute.mjs" <subcommand> ...
```

On this machine that resolves to
`node /home/raka/.local/share/nodejs/node-v24.11.0-linux-x64/lib/node_modules/omniroute/bin/omniroute.mjs`.
The CLI's management calls also 401 without a `manage`-scope key, so fall back to the
dashboard-password `curl` flow above.

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

## Errors

- Port already bound → something else holds 7777; check `ss -ltn | grep 7777`, then change
  `PORT` in `~/.omniroute/.env` and `aa omniroute restart`
- Configs unreadable after an upgrade → `STORAGE_ENCRYPTION_KEY` changed; restore the
  previous `~/.omniroute/.env`. Check `omniroute doctor`
- `omniroute serve` exits immediately → run `omniroute doctor`; the port is the usual cause
