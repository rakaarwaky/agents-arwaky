# Apply rules — deletes, disables, asks, groups

`<pipeline>` is the `_trace-pipeline` directory holding `scripts/state.py`.

## delete

- If `referenced_by` is non-empty, stop and ask, naming the referrers; the action is `ask`, not `delete`.
- Otherwise `<PYTHON> <pipeline>/scripts/state.py trash --run-name <run name> <path>` moves the skill directory, workflow file, or hook file into `<GROK_HOME>/learn/trash/<run name>/` (never the OS temp dir; it must survive a reboot) and prints where it went.
- For an MCP server in `config.toml`, cut its `[mcp_servers.<name>]` tables (with sub-tables) out with `search_replace`, write them with the `write` tool to `<GROK_HOME>/learn/trash/<run name>/mcp-<name>.toml`, then `<PYTHON> <pipeline>/scripts/state.py restrict <that file>`; never echo the contents. For an MCP server in `settings.json`, write the `mcpServers.<name>` object to `<GROK_HOME>/learn/trash/<run name>/mcp-<name>.json` and `restrict` it the same way **before** removing the key. Do not copy whole config files.
- Undo is moving the file or the table back; pass the trash path as `--undo`.

## disable

- Edit only the `[plugins]` `disabled` list in `GROK_HOME/config.toml`. Read only that block; never echo config values other than plugin names.
- `edit.anchor` is the exact list line to change; the reversal is moving the name back to `enabled`. Reversible.

## ask

- `requires_confirmation: true`. Emitted for the only copy of a job or a referenced skill; `reason` names what makes it unsafe (the referrer list, or "only copy of a job"). The user decides whether to retire it; this skill does not apply it without the pick.

## group

- One `kind: group` action bundles several zero-use surfaces that share a kind and a disposition (for example "12 zero-use bundled skills → propose overrides" or "9 zero-use plugin skills → ask"). `items` carries `{name, kind, path, protected, referenced_by, count, last_used}` per member.
- One question with three options: **apply to all** (run the group's `action` on every item), **pick items** (expand into `multi_select` questions of at most eight items each), or **skip all** (defer). Record one `state.py decide` line per item either way, with the group id in `--path` so a later run can tell the batch apart. A referenced zero-use skill joins the `ask` group of its kind with `referenced_by` filled in its item — it does not get its own row.

## Records

- `state.py decide` one line per item (groups: one per member), `applied` / `rejected` / `deferred`.
- A narrow window (`disuse_evidence.sufficient == false`) emits none of these; see the SKILL.md narrow-window rule.
