## Execution Mode

### MCP (preferred; this is what runs on this host)

The server is registered under the name **`workspace`** (in `~/.qwen/settings.json` and in
`mcp_servers.generated.json`; manifest id `workspace`, alias `google-workspace`, binary
`workspace-mcp`). So the callable tool names are **`mcp__workspace__search_gmail_messages`**,
`mcp__workspace__manage_event`, and so on.

The tables below list **base names only**. Prefix them with the server name your harness
exposes (`mcp__workspace__` on Qwen Code). Do **not** use a `google-workspace:` prefix — no
server is registered under that name and the calls fail.

If no `mcp__workspace__*` tools are visible, the server is not registered in that harness —
re-provision it (`aa connect <harness>` or `aa mcp generate`) rather than falling back to raw REST.

### CLI (headless / no MCP client)

`workspace-mcp` itself only serves MCP — it has **no `--cli` flag** (verified against
`workspace-mcp --help`). Its companion console script is `workspace-cli`, which talks to a
**running** server and needs no MCP client:

```bash
# Start the server with HTTP transport first (default target http://localhost:8000/mcp):
workspace-mcp --transport streamable-http &

workspace-cli list
workspace-cli call search_gmail_messages query="is:unread" max_results=5
# Override the target with WORKSPACE_MCP_URL; `uv run --directory vendor/google-workspace-mcp workspace-cli ...` if not on PATH.

```text

Server-side flags worth knowing (all documented in [references/server-options.md](references/server-options.md)):

```bash
aa tool run workspace-mcp --help        # or: workspace-mcp --help
workspace-mcp --tool-tier core          # fewer tools, fewer tokens
workspace-mcp --read-only               # read-only scopes, write tools disabled

```text

For any tool, read the matching `references/<service>.md` before calling it. Only use
parameters documented there — do not invent parameters.
