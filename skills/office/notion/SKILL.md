---
name: notion
description: 'Notion API + ntn CLI: pages, databases, markdown, Workers.'
when-to-use: "Use when reading or writing Notion pages, databases, markdown, file uploads, or Workers via the ntn CLI or the Notion API (curl)."
argument-hint: "ntn api v1/search|ntn api v1/users|ntn api v1/pages <parent[page_id]> [properties...]|ntn api v1/pages/<id>/markdown|ntn api v1/pages/<id>/markdown -X PATCH|ntn api v1/blocks/<id>/children|ntn api v1/data_sources/<id>/query -X POST|ntn files create|ntn files list|ntn workers new|ntn workers deploy|ntn workers exec"
version: 2.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [NOTION_API_KEY]
metadata:
  hermes:
    tags: [Notion, Productivity, Notes, Database, API, CLI, Workers]
    homepage: https://developers.notion.com
---

# Notion

Talk to Notion two ways. Same integration token works for both — pick by what's available.

◆ **`ntn` CLI** — Notion's official CLI. Shorter syntax, one-line file uploads, required for Workers. macOS + Linux only as of May 2026 (Windows support "coming soon"). **Default when installed.**
◆ **HTTP + curl** — works everywhere including Windows. **Default fallback** when `ntn` isn't installed.

## Global rules

- **An integration token is required for both paths** — create it at notion.so/my-integrations and store it as `NOTION_API_KEY`; skip `ntn login` and use the token instead.
- **Share target pages/databases with the integration in Notion** (page menu `...` → `Connect to` → your integration name); without this the API returns 404 for that page even though it exists.
- **Rate limit is ~3 requests/second average** — the CLI doesn't bypass it; batch and back off rather than hammering.
- **Always pass `-s` to curl** to suppress progress bars (cleaner agent output); pipe JSON through `jq` when reading.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Setup, `ntn` CLI commands, path choice, notes | [`references/ntn-cli.md`](references/ntn-cli.md) | Integration-token setup, `ntn` install, raw API shorthand, search/read/create/patch/query/upload command blocks, env vars, and the choosing-the-right-path table. |
| Cross-platform HTTP + curl fallback | [`references/http-path.md`](references/http-path.md) | Full curl command set for search, pages, blocks, data sources, properties, and file uploads — the default on Windows or when `ntn` is absent. |
| Common property formats + API versioning | [`references/property-types.md`](references/property-types.md) | Property type reference for building data sources. |
| Block types | [`references/block-types.md`](references/block-types.md) | Block type reference for reading/writing page content as blocks. |
| Notion-flavored markdown | [`references/flavored-markdown.md`](references/flavored-markdown.md) | Notion-flavored markdown blocks and inline tags used by the `/markdown` endpoints. |
| Notion Workers | [`references/workers.md`](references/workers.md) | Workers scaffold, webhook capability, and lifecycle commands. |
