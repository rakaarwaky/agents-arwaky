---
name: anytype-daemon
description: Manage Anytype headless daemon lifecycle, bot accounts, authentication tokens, and P2P space sync.
version: 1.0.0
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
