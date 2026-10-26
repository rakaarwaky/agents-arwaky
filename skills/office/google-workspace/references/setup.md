## First-Time Setup

Auth is already configured on this host if `~/.google_workspace_mcp/credentials/<email>.json`
exists. Walk the user through setup only when a tool call fails with a credential error.

### 1. Create OAuth credentials

Direct the user to [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

- Create OAuth 2.0 Client ID (Desktop application type)
- Enable the Google APIs they need (Gmail, Drive, Calendar, etc.)
- Copy the Client ID and Client Secret

### 2. Make the client secret visible to the server process

Do not ask the user to paste secrets into the conversation. Either point the server at a
downloaded JSON file with `GOOGLE_CLIENT_SECRET_PATH`, or put the id/secret in the `env` block
of the harness config that **launches** the server — for Qwen Code that is
`~/.qwen/settings.json` (`mcpServers.workspace.env`, or the top-level `env` block); merge into
any existing `env` object instead of replacing it. This repo's copy lives at
`vendor/google-workspace-mcp/client_secret.json`, which is the default project-root location
because the `workspace-mcp` launcher runs the server from that directory. `vendor/` is a pinned
submodule: treat that file as machine-local config, never a thing to edit or commit.

### 3. Authenticate

- **MCP mode**: call `start_google_auth` to open the browser OAuth flow
- **CLI mode**: run any tool through a streamable-http server -- the first invocation opens the OAuth flow
- Credentials are cached in `~/.google_workspace_mcp/credentials/<email>.json` (override with
  `WORKSPACE_MCP_CREDENTIALS_DIR`, then legacy `GOOGLE_MCP_CREDENTIALS_DIR`) for future sessions

Full loading order, transports, and tool filtering: [references/server-options.md](references/server-options.md)
Reproduced error signatures and their workarounds: [references/pitfalls.md](references/pitfalls.md)

