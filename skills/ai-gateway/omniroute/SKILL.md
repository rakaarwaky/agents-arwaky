---
name: omniroute
description: OmniRoute free AI gateway over OpenAI REST, 350+ providers with 150+ free tiers. Use when mentioning OmniRoute, OMNIROUTE_URL, auto/best-free, free-tier routing, checking a model context length (ctx) on the gateway, or building a model tier list / ranking the gateway model catalog. 9router (port 20128) is the second supported gateway vendor alongside OmniRoute.
when-to-use: "Use when asking about OmniRoute, OMNIROUTE_URL, OMNIROUTE_KEY, auto/best-free or other combo routing, free-tier routing, adding a custom OpenAI-compatible provider, managing the OmniRoute daemon (status, restart, logs), fixing OmniRoute errors, or building a model tier list / ranking the gateway model catalog."
argument-hint: "[setup | models [--free] [--search <q> | --json] | combo <list|switch|create|delete|suggest> | providers <add|list|test|edit|remove|test-all> | aa omniroute <status|restart|logs|models|service-install> | doctor | keys | cost]"
metadata:
  tags:
    - ai-gateway
    - model-catalog
    - tierlist
---

# OmniRoute

Free-first AI gateway exposing OpenAI-compatible REST. Hundreds of providers, most with a
free tier, plus combo routing that picks a model by task shape.

Host-native — no Docker, no container. Installed from npm, pinned by `vendor/omniroute`.

## Global rules

- Default API/dashboard root: `http://127.0.0.1:7777`. Every inference request uses
  `Authorization: Bearer ${OMNIROUTE_KEY}` against `${OMNIROUTE_URL}/v1/...`.
- Working directory is `~/.omniroute/` (`.env`, `storage.sqlite`, `logs/`). Upstream
  reads `.env` from this directory; do not relocate it.
- `STORAGE_ENCRYPTION_KEY` in `.env` encrypts every provider credential at rest.
  **Never rotate it** and never let a tool regenerate it. If configs become unreadable
  after an upgrade, restore the previous `.env`.
- Combo aliases (`auto/*`) pick a model by task shape instead of naming one directly.
- 9router (port 20128) is the second supported gateway vendor alongside OmniRoute.

## Routing

| Reference | Purpose |
| --------- | ------- |
| [`references/setup.md`](references/setup.md) | Environment setup, config layout, port override, verification. |
| [`references/combos.md`](references/combos.md) | Combo routing aliases and curl example. |
| [`references/providers.md`](references/providers.md) | Provider keys, dashboard, custom provider addition, and daemon management. |
| [`references/models.md`](references/models.md) | Discover models via `/v1/models` and the CLI. |
| [`references/sync.md`](references/sync.md) | Sync providers/models/combos into 9router SQLite. |
| [`references/errors.md`](references/errors.md) | Common OmniRoute errors and fixes. |
| [`references/model-tier-list.md`](references/model-tier-list.md) | Build a model tier list / capability ranking from the catalog. |
| [`references/omniroute-models-shape.md`](references/omniroute-models-shape.md) | `GET /v1/models` response shape and dedupe suffix list. |
| [`references/custom-provider.md`](references/custom-provider.md) | Add a custom OpenAI-compatible provider, with management API and CLI examples. |
