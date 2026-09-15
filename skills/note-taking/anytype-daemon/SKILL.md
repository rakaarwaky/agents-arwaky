---
name: anytype-daemon
description: Manage Anytype headless daemon lifecycle, bot accounts, authentication tokens, and P2P space sync.
metadata:
  tags: []
---

# Anytype Headless Daemon

The Anytype Headless Daemon runs a dedicated local Anytype node in a rootless container or host process. It provides P2P data synchronization and exposes the local HTTP REST API at `127.0.0.1:31012` for `anytype-mcp`.

## When to Use This Skill

Activate this skill when:
- Starting, stopping, or verifying the health of the local Anytype background daemon.
- Setting up a bot account for AI agents to interact with Anytype spaces.
- Generating or rotating API authentication keys for MCP integrations.
- Joining an Anytype space via invite links to allow agent synchronization.

## Daemon Management Commands

Execute daemon commands using the `agents-arwaky` (`aa`) CLI:

| Command | Action | Example |
|---|---|---|
| `aa anytype start` | Launch the Anytype background container | `aa anytype start` |
| `aa anytype stop` | Gracefully stop the running daemon | `aa anytype stop` |
| `aa anytype restart` | Restart the background daemon | `aa anytype restart` |
| `aa anytype status` | Check running state, port, and process info | `aa anytype status` |
| `aa anytype logs` | Tail recent container logs for debugging | `aa anytype logs -f` |

## API Key Pitfall (verified 2026-09)

`aa anytype auth-key` parses the key with a token regex that STRIPS the trailing `=` of the base64 key → daemon returns 401 "invalid api key" forever, even after restart. Correct procedure:

1. `podman exec anytype-daemon anytype auth apikey create "<name>"` — copy the Key verbatim (it ends in `=`).
2. Verify with REST before wiring clients:
   `curl -s -H "Authorization: Bearer <KEY>" -H "Anytype-Version: 2025-11-08" http://127.0.0.1:31012/v1/spaces`
3. Update client configs manually (`~/.config/agents-arwaky/anytype.env`, Hermes via `hermes config set mcp_servers.anytype.env.OPENAPI_MCP_HEADERS ...`). `patch`/direct edit of Hermes config.yaml is blocked; `hermes config set` works.
4. Duplicate names in `auth apikey list` (old broken keys) are harmless; list shows KEY prefix `...` so compare the tail `=`.

## Agent Provisioning Workflow

1. **Start the daemon:**
   ```bash
   aa anytype start
   ```

2. **Create a dedicated bot account for the agent:**
   ```bash
   aa anytype auth-create "arwaky-bot"
   ```

3. **Generate an API key:**
   ```bash
   aa anytype auth-key "agent-mcp-key"
   ```
   *(This automatically updates `.env` with `ANYTYPE_API_KEY`)*

4. **Join target space:**
   In your Anytype desktop/mobile app, generate an invite link for your space, then:
   ```bash
   aa anytype space-join "<your-invite-link>"
   ```

5. **Verify membership:**
   ```bash
   aa anytype space-list
   ```
