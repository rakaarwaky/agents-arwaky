# Step 4 — Apply

# Apply rules — deletes, disables, asks, groups

Trash and restrict run through the `aa skills trace-state` CLI.

## actions.json field shapes

Each entry in `actions.json` carries:

```json
{
  "run_dir": "<run_dir>",
  "generated_at": "<today>",
  "actions": [
    {
      "id": "A1",
      "kind": "skill | plugin | mcp | workflow | hook | config | group",
      "action": "create | edit | enable | disable | delete | propose | ask",
      "target": "<name>",
      "path": "<absolute path of the file or directory the action touches>",
      "protected": "plugin | bundled | git-tracked | null",
      "referenced_by": ["<loaded skill names that mention this skill>"],
      "reversible": true,
      "requires_confirmation": false,
      "evidence": {
        "sessions": ["<session id>", "..."],
        "count": 0,
        "quote": "<exact phrase or stale line, at most 300 chars>"
      },
      "reason": "<one sentence>",
      "edit": {
        "anchor": "<exact substring of the current file, or \"\" for create>",
        "replacement": "<full replacement text, or full file content for create>",
        "mode": "replace | insert_after | append"
      },
      "items": []
    }
  ]
}
```

Rules for the fields:

- `id` is `A1`, `A2`, … in report order.
- `path` is exact. For `plugin` and `mcp` actions it is the config file (`<GROK_HOME>/config.toml` or `settings.json`), and `edit.anchor` is the exact list or table header line to change. Never include config values other than names.
- `reversible` is `true` for edits with an anchor, enables/disables, and deletes (the apply step moves deleted files to `<GROK_HOME>/learn/trash/<run name>/`). It is `false` only when the apply step cannot undo the change from the trash directory or the anchor.
- `protected` and `referenced_by` are copied from `surfaces.json`. A protected skill is never edited or deleted in place: the action is `propose`, with `requires_confirmation: true` and a `reason` that says where the fix belongs — a user-skill override with the same name for `plugin` and `bundled`, a pull request for `git-tracked`. `propose` carries an `edit` block so the apply step can write the override or the patch.
- A `delete` whose `referenced_by` is non-empty is emitted as `ask`, and `reason` names the referrers.
- `requires_confirmation` is `true` for `ask`, `propose`, any `delete` of the only copy of a job, and any unverified claim.
- **Narrow windows prove nothing.** `manifest.json` → `disuse_evidence.sufficient` is `false` when the run was scoped to one working directory or listed sessions, kept fewer than 20 sessions, or spans under 7 days. In that case section 3 is titled `## 3. Not seen in this window`, lists the zero-use surfaces as information only, emits **no** `delete`, `disable`, `ask`, or `group` action for them, and the Overview's deletes/disables count is 0 with `disuse_evidence.reason` quoted ("window too narrow to judge disuse: scoped to one working directory; only 3 sessions kept"). A skill unused in three sessions from one folder may be the user's most-used skill everywhere else.
- **Grouping.** Unused surfaces that share a kind and a disposition (for example "12 zero-use bundled skills → propose overrides" or "9 zero-use plugin skills → ask") are one action with `kind: group`, `action` set to the shared disposition, `target` a short label, and an `items` array of `{name, kind, path, protected, referenced_by, count, last_used}`. One decision is worth one row; 40 rows that each say "ask" are not 40 decisions. Never group across dispositions and never group anything with evidence of use (`count > 0`). A referenced zero-use skill is never a `delete`; its disposition is `ask`, so it joins the `ask` group of its kind with `referenced_by` filled in its item — it does not get its own row. The Overview's action count counts a group as one.
- `edit` is required for `create`, `edit`, and `propose`; omit it for enable, disable, delete, ask.
- `create` writes `<user skills dir>/<name>/SKILL.md`. The `replacement` is the whole file: `---` frontmatter with `name`, `description` (what it does plus the trigger phrases), `user-invocable: true`, `origin: learn` (provenance the client reports as `skill_origin`; never omit it, never another value), then a body of imperative steps. Use the quoted phrases as the trigger list and the body.

## delete

- If `referenced_by` is non-empty, stop and ask, naming the referrers; the action is `ask`, not `delete`.
- Otherwise `aa skills trace-state trash --run-name <run name> <path>` moves the skill directory, workflow file, or hook file into `<GROK_HOME>/learn/trash/<run name>/` (never the OS temp dir; it must survive a reboot) and prints where it went.
- For an MCP server in `config.toml`, cut its `[mcp_servers.<name>]` tables (with sub-tables) out with `search_replace`, write them with the `write` tool to `<GROK_HOME>/learn/trash/<run name>/mcp-<name>.toml`, then `aa skills trace-state restrict <that file>`; never echo the contents. For an MCP server in `settings.json`, write the `mcpServers.<name>` object to `<GROK_HOME>/learn/trash/<run name>/mcp-<name>.json` and `restrict` it the same way **before** removing the key. Do not copy whole config files.
- Undo is moving the file or the table back; pass the trash path as `--undo`.

## disable

- Edit only the `[plugins]` `disabled` list in `GROK_HOME/config.toml`. Read only that block; never echo config values other than plugin names.
- `edit.anchor` is the exact list line to change; the reversal is moving the name back to `enabled`. Reversible.

## ask

- `requires_confirmation: true`. Emitted for the only copy of a job or a referenced skill; `reason` names what makes it unsafe (the referrer list, or "only copy of a job"). The user decides whether to retire it; this skill does not apply it without the pick.

## group

- One `kind: group` action bundles several zero-use surfaces that share a kind and a disposition (for example "12 zero-use bundled skills → propose overrides" or "9 zero-use plugin skills → ask"). `items` carries `{name, kind, path, protected, referenced_by, count, last_used}` per member.
- One question with three options: **apply to all** (run the group's `action` on every item), **pick items** (expand into `multi_select` questions of at most eight items each), or **skip all** (defer). Record one `aa skills trace-state decide` line per item either way, with the group id in `--path` so a later run can tell the batch apart. A referenced zero-use skill joins the `ask` group of its kind with `referenced_by` filled in its item — it does not get its own row.

## Records

- `aa skills trace-state decide` one line per item (groups: one per member), `applied` / `rejected` / `deferred`.
- A narrow window (`disuse_evidence.sufficient == false`) emits none of these; see the SKILL.md narrow-window rule.
