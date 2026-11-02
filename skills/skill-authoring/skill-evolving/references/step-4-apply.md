# Step 4 — Apply

## actions.json field shapes

Each entry in `actions.json` carries:

```json
{
  "id": "A1",
  "kind": "skill | plugin | mcp | workflow | hook | config",
  "action": "edit | propose | enable | disable",
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
    "anchor": "<exact substring of the current file>",
    "replacement": "<full replacement text>",
    "mode": "replace | insert_after | append"
  }
}
```

Field rules:

- `id` is `A1`, `A2`, … in report order.
- `path` is exact. For `plugin` and `mcp` actions it is the config file (`<GROK_HOME>/config.toml` or `settings.json`), and `edit.anchor` is the exact list or table header line to change. Never include config values other than names.
- `protected` and `referenced_by` are copied from `surfaces.json`.
- `requires_confirmation` is `true` for `propose` and any unverified claim.
- `reversible` is `true` for edits with an anchor and enables/disables (the apply step moves originals to trash). It is `false` only when the apply step cannot undo the change.
- `edit` is required for `edit` and `propose`; omit it for enable, disable.

## Per-action rules

**edit** — Before the first edit to any file in a run, read it and write an untouched copy to `<GROK_HOME>/learn/trash/<run name>/originals/<name>.md`; that copy is the undo (`--undo`). Never echo a secret into `edit.anchor` or `edit.replacement`; redact evidence lines first. `search_replace` on `path` with `edit.anchor` as old string. `edit.mode`: `replace` swaps anchor for replacement, `insert_after` keeps anchor and adds replacement after it, `append` adds replacement at end. If anchor is missing, re-read the file and fix the anchor — never overwrite the whole file. After applying, re-read the changed file and confirm the change is present.

**propose** — A protected skill (plugin, bundled, git-tracked) is never edited in place. Read the protected SKILL.md in full, apply `edit.anchor` → `edit.replacement` to that text, and write the complete result to `<user skills dir>/<name>/SKILL.md`. For git-tracked targets, write the patch to `<RUN>/patches/<name>.diff` and tell the user it needs a PR. `requires_confirmation: true`.

**enable / disable** — Edit only the `[plugins]` enabled/disabled lists in `GROK_HOME/config.toml`. Read only that block; never echo config values other than plugin names. Reversible by swapping the list.

## Records

- Undo for an `edit` is the trash copy; pass it as `--undo` to `trace-state decide`.
- Never print secrets; the replacement must not carry tokens, keys, or credentials quoted from the traces.

Then record every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill|workflow|hook --action create|update|delete|reject --target <name> --path <path> --decision applied|rejected|deferred [--date DATE] [--undo <trash path>]`. Map edit/propose/enable/disable to `--action update`.