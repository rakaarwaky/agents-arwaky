# anytype-arwaky

Wrapper around [anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp) — an MCP server
enabling AI assistants to interact with Anytype (encrypted, local, collaborative wiki) via
natural language: search, objects, lists, properties, types, templates.

## Why this wrapper

- Pins the upstream source as a submodule for reproducible local use.
- Provides `script/install.sh` for a local Bun build into `dist/`.
- Ships a ready-made MCP client snippet (`anytype_local.json`).

## Prerequisites

1. **Anytype desktop app running** (it exposes the API at `http://127.0.0.1:31009`).
2. **API key**: Anytype → App Settings → API Keys → *Create new*
   (or `npx -y @anyproto/anytype-mcp get-key`).
3. Node.js (for `npx`) or [Bun](https://bun.com) (for local build).

## Quick start (no build needed)

```bash
npx -y @anyproto/anytype-mcp
```

## Local build

```bash
script/install.sh
```

## MCP client config

Use `anytype_local.json`, replacing `<YOUR_API_KEY>`:

```json
{
  "mcpServers": {
    "anytype": {
      "command": "npx",
      "args": ["-y", "@anyproto/anytype-mcp"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer <YOUR_API_KEY>\", \"Anytype-Version\":\"2025-11-08\"}"
      }
    }
  }
}
```

### Hermes Agent

```bash
hermes mcp add anytype \
  -e OPENAPI_MCP_HEADERS='{"Authorization":"Bearer <YOUR_API_KEY>", "Anytype-Version":"2025-11-08"}' \
  -- npx -y @anyproto/anytype-mcp
```

### Headless alternative (anytype-cli)

If you run the headless [`anytype-cli`](https://github.com/anyproto/anytype-cli) instead of the
desktop app (API on port `31012`), add:

```json
"env": {
  "ANYTYPE_API_BASE_URL": "http://localhost:31012",
  "OPENAPI_MCP_HEADERS": "{ ... }"
}
```

## Layout

```
anytype-arwaky/
├── anytype-mcp/        # upstream submodule (anyproto/anytype-mcp)
├── script/install.sh   # local Bun build -> dist/
├── anytype_local.json  # MCP client config snippet
└── README.md
```

## License

Upstream is MIT — see `anytype-mcp/LICENSE.md`.
