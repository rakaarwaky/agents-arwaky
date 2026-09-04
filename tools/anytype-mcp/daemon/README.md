# Anytype Headless Daemon for agents-arwaky

This component provides a dedicated, headless Anytype node (`anytype-cli`) designed for AI agents running inside Podman or directly on the host.

## Architecture

```
[ AI Agent / MCP Client ]
          │  (stdio MCP Protocol)
          ▼
    [ anytype-mcp ] (reads .env: ANYTYPE_API_KEY & ANYTYPE_API_BASE_URL)
          │  (HTTP REST API: 127.0.0.1:31012)
          ▼
[ anytype-daemon (Podman Container) ]
  ├── anytype-heart engine
  ├── Persistent Data: ~/.local/share/anytype-daemon/data
  └── P2P Sync with your Anytype Space
```

## Quick Start

### 1. Start the Daemon
```bash
arwaky anytype start
# or:
./tools/anytype-mcp/daemon/anytype-daemon.sh start
```

### 2. Create a Bot Account for the Agent
```bash
arwaky anytype auth-create "arwaky-agent"
```

### 3. Generate API Key (Auto-updates `.env`)
```bash
arwaky anytype auth-key "mcp-access-key"
```
This automatically updates `ANYTYPE_API_KEY` in `.env` and refreshes the MCP configuration.

### 4. Invite Agent to your Space
In your desktop/mobile Anytype app:
1. Open the Space settings.
2. Generate an **Invite Link** with appropriate permissions (e.g. Member or Editor).
3. Have the bot join:
```bash
arwaky anytype space-join "<your-invite-link>"
```

### 5. Check Status
```bash
arwaky anytype status
arwaky anytype space-list
```

### 6. (Optional) Auto-start on boot via systemd
```bash
arwaky anytype service-install
```
