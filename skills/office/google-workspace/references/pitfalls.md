# Google Workspace — Verified Pitfalls

Failure modes of the `workspace` MCP server that are not visible from the tool schemas. Read before debugging a 400, a 404, or an auth prompt that should not exist.

## Tool-call shape

- `mcp__workspace__*` are LOCAL tools: one schema entry per `tool_call`. To parallelize,
  send multiple `tool_call` blocks in a single message — the server does not batch for you.

## Recurring calendar events reject UTC-offset times

- `manage_event` with `recurrence` returns **400 "Missing time zone definition"** when
  `start_time`/`end_time` carry a `+07:00` (or any) offset.
- Fix: send wall-clock `YYYY-MM-DDTHH:MM:SS` with **no offset and no `Z`**, plus
  `timezone: "Asia/Jakarta"` (or the account's IANA zone).
- Non-recurring events accept offsets happily, so a successful single create does **not**
  prove the same arguments are safe for a recurring series.

## Rejected calls trigger a server-side pause

- After **3 rejected calls** the MCP server auto-pauses for **~60 seconds**. Waiting is
  faster than retrying; hammering extends the backoff you are trying to escape.

## Some secondary calendars 404 on event endpoints

- Calendars that appear normally in `list_calendars` (e.g. a "Study" calendar) can 404 on
  `get_events` / `manage_event`. Write to `primary` and encode the real grouping in the
  event `summary` (or `color_id`) instead of fighting the 404.

## Where credentials actually live

- **Per-account OAuth tokens**: `~/.google_workspace_mcp/credentials/<email>.json`
  (override with `WORKSPACE_MCP_CREDENTIALS_DIR`, then legacy `GOOGLE_MCP_CREDENTIALS_DIR`).
- **Client secret** resolution order: `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`
  env vars → `GOOGLE_CLIENT_SECRET_PATH` → `client_secret.json` in the server's project root.
  `vendor/` is a **pinned git submodule**: never edit it from the root repo and never commit a secret into it.
- The XDG-looking paths `~/.config/google-workspace-mcp/client_secret.json` and
  `~/.local/share/google-workspace-mcp/credentials/` are **not** read by this server and do not
  exist on this host. Creating them does nothing; do not document them as the auth location.
- Restoring `~/.google_workspace_mcp/credentials/` from a backup still needs
  **one fresh browser consent**: the scopes stored in the backup do not match the scopes the
  currently loaded tool set requests.
- Backup location: `~/Downloads/Agents-Arwaky-Backups-*/Agents-Arwaky-Backups/<snapshot>/workspace/`.

## Mail-only escape hatch

- If the user only needs email and Workspace OAuth is the blocker, `himalaya` is the
  mail-only alternative (Gmail App Password, no Google Cloud project) — see the email
  umbrella's `§ himalaya`. Check it is installed before recommending it.
