---
name: hermes-home-cleanup
description: Purge traces of an MCP server or skill from ~/.hermes.
---

# Hermes Home Inventory & Cleanup

Use when asked to list configured MCP servers/tools or to "clean all X
references from my hermes". Both tasks share one map of where Hermes keeps
state.

## Inventory: sources of truth, in order
1. **Live config**: `mcp_servers:` block in `~/.hermes/config.yaml` AND each
   `~/.hermes/profiles/<name>/config.yaml` — profiles are independent islands;
   a server can exist in one profile only. `enabled: true/false` per entry.
2. **Tool counts + names**: `~/.hermes/cache/mcp_schema_cache.json` — top-level
   keys are server names, each with a `tools` list. Same file exists per
   profile at `~/.hermes/profiles/<name>/cache/mcp_schema_cache.json`. A server
   present ONLY in this cache but absent from config = stale entry — report it
   as such, not as live.
3. Plugins: `~/.hermes/plugins/`, `profiles/*/plugins/`. Skills:
   `~/.hermes/skills/`, `profiles/*/skills/` (+ `.usage.json` per profile).

## Purge procedure (finding ALL traces)
1. Build a **name-variant regex**: `x[-_.]?y` AND the glued form `xy` — the
   skills hub index cache (`skills/.hub/index-cache/hermes-index.json`) stores
   normalized display names ("Leanctx Integration") that a hyphen-only grep
   misses. Case-insensitive.
2. Sweep with exclusions — never raw `grep -r ~/.hermes/`:
   `grep -rIli '<regex>' ~/.hermes/ --exclude-dir=sessions --exclude-dir=logs --exclude-dir=checkpoints --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=hermes-agent --exclude='*.log'`
   (sessions/logs are history, not config; `hermes-agent` is the source repo —
   don't edit product code to satisfy a cleanup).
3. Known orphan homes to check explicitly: per-profile
   `cache/mcp_schema_cache.json`, `profiles/*/skills/.usage.json`,
   `skills/.hub/index-cache/hermes-index.json`, `cache/tool_discovery_cache.json`,
   `cache/plugin_toolset_keys.json`, `cron/**`, leftover blocked-script temps
   in `profiles/*/cache/blocked-scripts/`.
4. Also verify the component isn't actually installed (`which <bin>`, `pip show`,
   skill/plugin dirs) before and after — that proves runtime cleanliness, not
   just text removal.
5. Re-run the sweep at the end; report remaining files and ask before touching
   user backups (e.g. `config.yaml.bak`) — inert but they're the user's restore
   point, and the user prefers being asked over guessing.

## Editing the JSON stores
- Load/dump with Python (`json.load` → mutate → `json.dump`) — never sed/regex
  on JSON; removing a server from `mcp_schema_cache.json` or a skill from
  `.usage.json` is a dict pop; in `hermes-index.json` the entry lives in the
  `skills` list (filter by regex over `json.dumps(entry)`).
- Back up large hub files before editing (copy to `<file>.bak` suffix) so the
  ~90k-entry skills index is restorable.

## Pitfalls
- **Keep each terminal command small and single-purpose.** A long `;`-chained
  one-liner of greps/echoes trips the hardline blocklist for oversized inline
  payloads; the rejected command is written to
  `profiles/*/cache/blocked-scripts/blocked-*.sh` — which then becomes yet
  another file containing the name you're purging. Do multi-file walks in
  `execute_code` Python instead of chained shell.
- Grepping a giant single-line JSON with `grep -A/-B` returns the whole file;
  use `re.finditer(r'.{60}name.{100}', text)` in Python for context windows.

