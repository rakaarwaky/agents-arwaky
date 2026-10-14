# MCP server vs CLI vs both — decision pattern

Worked out 2026-08-25 for Anytype; generalizes to any project shipping both an MCP
server and a CLI over the same API.

## Key insight

They usually operate at DIFFERENT layers, not competing:

- **MCP server** = data-plane consumer: converts the project's API into AI-callable
  tools (search, CRUD). Needs SOME server already running (desktop app or headless).
- **CLI** = control/infra plane: account management, running/stopping the embedded
  headless server, service install, join/leave spaces. Usually cannot edit content.
- They interoperate: CLI can run a headless instance on a different port; MCP servers
  typically accept a base-URL env var (e.g. `ANYTYPE_API_BASE_URL=http://localhost:31012`)
  to point at it instead of the desktop app port.

```
anytype-cli ──(runs)──► Anytype API ◄──(used by)── anytype-mcp ◄── AI/Hermes
desktop app ─(serves)─► Anytype API ◄────────────────────────────┘
```

## Interview questions to decide for a user

1. Do they run the desktop app regularly? (Yes → MCP alone suffices.)
2. Goals: chat-with-data / scripting automation / headless-on-server / backup?
   - Chat + automation + backup → MCP alone (the agent runs scripts itself).
   - Headless 24/7 or no desktop app → CLI (+ optionally MCP pointed at its port).
3. Which AI client? Hermes/Claude/Cursor all take stdio npx MCP configs.
4. Comfort with terminal; OS; Node/Bun availability.
5. Privacy scope & remote access needs.

## Anytype specifics

| | anytype-mcp | anytype-cli |
|---|---|---|
| Content CRUD, search, types/templates | ✅ full OpenAPI→MCP | ❌ |
| Account auth create/login, service mgmt | ❌ | ✅ |
| Space join/leave via invite link | ❌ | ✅ |
| Default API port | uses app's `31009` | serves own `31012` |
| Auth model | API key from desktop app | dedicated bot account (`anytype auth create`) |

Desktop config snippet lives in the user's repo:
`~/agents-arwaky/anytype-arwaky/anytype_local.json` (replace `<YOUR_API_KEY>`).
Hermes registration: `hermes mcp add` / setup_mcp consent card; restart required after adding.
