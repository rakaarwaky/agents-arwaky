---
name: hermes-home-cleanup
description: Purge traces of an MCP server or skill from ~/.hermes.
metadata:
  tags: []
---

# Hermes Home Cleanup (forensic purge)

Use when asked to "clean all X references from my hermes" / remove an MCP server or
skill completely. "Just list what's configured" is the same enumeration minus the
deletion steps. Where Hermes keeps state is NOT inventoried here — see below.

## Where Hermes keeps state (not repeated here)

The provisioning map lives in the `agent-harness-connectors` skill — what `aa connect`
writes and where (MCP server map into each harness config, `NINEROUTER_*`/`MNEMOSYNE_*`
into `<harness>/.env` plus `~/.config/environment.d/`, skills as one root symlink into the
pack, and the dot-prefixed state files that land beside them). Profile layout and the
`skills.disabled` mechanism are in `hermes-profiles` (`hermes-profiles` skill's `references/skills-layout.md`,
`references/skill-filtering.md`).

Two facts this procedure depends on, so they are stated here anyway:

- **Profiles are independent config islands.** `mcp_servers:` exists in
  `~/.hermes/config.yaml` AND in every `~/.hermes/profiles/<name>/config.yaml`; a server
  can live in one profile only. `enabled: true/false` is per entry.
- **Cache ≠ config.** `cache/mcp_schema_cache.json` (root and per profile) has server
  names as top-level keys with a `tools` list. A server present only there and absent
  from config is a stale entry — report it as stale, not as live.

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

