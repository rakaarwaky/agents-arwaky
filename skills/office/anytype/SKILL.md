---
name: anytype
description: Manage the Anytype headless daemon (start/stop, bot accounts, API keys, P2P space sync) and query Anytype spaces, objects, and notes via the Anytype MCP server. Use when running Anytype for agents, generating auth keys, or creating, searching, and updating Anytype objects.
metadata:
  tags:
    - anytype
    - note-taking
---

# Anytype

Anytype runs a local-first knowledge graph. This skill covers both layers: the **headless
daemon** (a dedicated local Anytype node in a rootless container or host process that
provides P2P data sync and the local REST API at `127.0.0.1:31012`) and the **MCP server**
that connects agents to spaces, objects, and notes through that API.

## When to Use This Skill

Activate this skill when:

- Starting, stopping, or verifying the health of the local Anytype background daemon.
- Setting up a bot account for AI agents to interact with Anytype spaces.
- Generating or rotating API authentication keys for MCP integrations.
- Joining an Anytype space via invite links to allow agent synchronization.
- Searching for existing knowledge, notes, documentation, or tasks within Anytype.
- Creating or editing pages, bookmarks, notes, or tasks in an Anytype space.
- Inspecting space members, object types, templates, and relation properties.

## Sub-scenarios

| Scenario | Where |
|---|---|
| MCP tools — searching, creating, and updating objects, notes, and spaces | `references/mcp.md` |

## Prerequisites & Daemon Connection

The Anytype MCP server communicates locally with the Anytype daemon at
`http://127.0.0.1:31012`. Ensure the daemon is running before making calls:

```bash
# Check daemon status
aa anytype status

# Start daemon if not active
aa anytype start
```

## Daemon Management Commands

Execute daemon commands using the `agents-arwaky` (`aa`) CLI:

| Command | Action | Example |
|---|---|---|
| `aa anytype start` | Launch the Anytype background container | `aa anytype start` |
| `aa anytype stop` | Gracefully stop the running daemon | `aa anytype stop` |
| `aa anytype restart` | Restart the background daemon | `aa anytype restart` |
| `aa anytype status` | Check running state, port, and process info | `aa anytype status` |
| `aa anytype logs` | Tail recent container logs for debugging | `aa anytype logs -f` |

## Troubleshooting "API: not ready" (port 31012 not listening)

**Check first, before any restart:** whether the CLI is authenticated:

```bash
podman exec anytype-daemon anytype auth status
```

If it says *Not authenticated*, that is the root cause — not a port or network issue. The
REST API on 31012 is only bound **after** a bot account is created; the gRPC listeners on
31010/31011 start regardless, which makes the symptom look like a port misconfiguration.
Fix by creating a bot account (`aa anytype auth-create arwaky-bot` or
`podman exec anytype-daemon anytype auth create arwaky-bot`), then port 31012 comes up
automatically. A restart without authentication will not help. `aa anytype status`
reporting "Container: RUNNING / API: not ready" with the gRPC ports up is the fingerprint
of this exact state — check `auth status` before restarting.

If auth status shows *Logged in* but the port is still absent, restart the container.

## API Key Pitfall (verified 2026-09)

`aa anytype auth-key` parses the key with a token regex that STRIPS the trailing `=` of the
base64 key → daemon returns 401 "invalid api key" forever, even after restart. Correct
procedure:

1. `podman exec anytype-daemon anytype auth apikey create "<name>"` — copy the Key verbatim
   (it ends in `=`).
2. Verify with REST before wiring clients:
   `curl -s -H "Authorization: Bearer <KEY>" -H "Anytype-Version: 2025-11-08" http://127.0.0.1:31012/v1/spaces`
3. Update client configs manually (`~/.config/agents-arwaky/anytype.env`). For Hermes
   `mcp_servers.anytype.env.OPENAPI_MCP_HEADERS`, write the value as a **JSON string**, not a
   YAML mapping: `hermes config set` and YAML dumping re-parse a quoted JSON string into a
   nested dict, and the MCP stdio schema (`StdioServerParameters.env`) rejects dict env
   values with a `ValidationError: ... Input should be a valid string` at connect time.
   Apply it with a targeted YAML write that keeps the scalar:

   ```python
   import yaml, json
   p = "~/.hermes/config.yaml".expanduser()
   cfg = yaml.safe_load(open(p))
   cfg["mcp_servers"]["anytype"]["env"]["OPENAPI_MCP_HEADERS"] = json.dumps(
       {"Authorization": f"Bearer {key}", "Anytype-Version": "2025-11-08"})
   yaml.dump(cfg, open(p, "w"), default_flow_style=False, sort_keys=False)
   ```

   Confirm with `grep -A2 OPENAPI_MCP_HEADERS config.yaml` that the value is a quoted
   scalar, not an indented mapping.
4. After updating the key in Hermes config, restart the gateway: `hermes gateway restart` —
   the MCP server loads env at gateway start, not at tool call time.
5. Duplicate names in `auth apikey list` (old broken keys) are harmless; list shows KEY
   prefix `...` so compare the tail `=`.

Authentication headers for the MCP layer are configured per `references/mcp.md`
(Authentication Configuration).

## Agent Provisioning Workflow

1. **Start the daemon:**

   ```bash
   aa anytype start
   ```

2. **Create a dedicated bot account for the agent:**

   ```bash
   aa anytype auth-create "arwaky-bot"
   ```

   The account key is printed once and saved to `/root/.anytype/config.json` inside the
   container. The CLI auto-logs-in immediately. After this step the REST API on port 31012
   should be up — verify with `ss -ltn | grep 31012` before proceeding.

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
