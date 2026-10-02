---
name: omniroute
description: OmniRoute free AI gateway over OpenAI REST, 350+ providers with 150+ free tiers. Use when mentioning OmniRoute, OMNIROUTE_URL, auto/best-free, free-tier routing.
metadata:
  tags: []
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

## Discover models

```bash
curl $OMNIROUTE_URL/v1/models          # everything currently routable
omniroute models --free                # free tiers only, via the CLI
```

## Provider keys

Most providers need no key — the free-tier catalogue is what makes the gateway useful out of
the box. Add keys with `omniroute setup` (walks through it and stores them in the database),
or via the dashboard at `http://127.0.0.1:7777`. Both write to `storage.sqlite`, so they need
no edit to `~/.omniroute/.env`.

`STORAGE_ENCRYPTION_KEY` encrypts stored credentials at rest. **Never change it** once
credentials exist — every previously stored key becomes unreadable.

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
