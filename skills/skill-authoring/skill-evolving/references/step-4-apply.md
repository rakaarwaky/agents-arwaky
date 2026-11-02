# Step 4 — Apply

## actions.json field shapes

Each entry in `actions.json` carries:

```json
{
  "id": "A1",
  "kind": "skill",
  "action": "edit | propose",
  "target": "<name>",
  "path": "<absolute path of the file or directory the action touches>",
  "protected": "bundled | git-tracked | null",
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
- `path` is exact: the SKILL.md file for the skill being edited.
- `protected` and `referenced_by` are copied from `surfaces.json`.
- `requires_confirmation` is `true` for `propose` and any unverified claim.
- `reversible` is `true` for `edit` (the apply step moves the original to trash). It is `false` only when the apply step cannot undo the change from the trash copy.
- `edit` is required for both `edit` and `propose`.

## Per-action rules

**edit** — Before the first edit to any file in a run, read it and write an untouched copy to `<GROK_HOME>/learn/trash/<run name>/originals/<name>.md`; that copy is the undo (`--undo`). Never echo a secret into `edit.anchor` or `edit.replacement`; redact evidence lines first. `search_replace` on `path` with `edit.anchor` as old string. `edit.mode`: `replace` swaps anchor for replacement, `insert_after` keeps anchor and adds replacement after it, `append` adds replacement at end. If anchor is missing, re-read the file and fix the anchor — never overwrite the whole file. After applying, re-read the changed file and confirm the change is present.

**propose** — A protected skill (bundled or git-tracked) is never edited in place. Read the protected SKILL.md in full, apply `edit.anchor` → `edit.replacement` to that text, and write the complete result to `<user skills dir>/<name>/SKILL.md`. For git-tracked targets, write the patch to `<RUN>/patches/<name>.diff` and tell the user it needs a PR. `requires_confirmation: true`.

## Records

- Undo for an `edit` is the trash copy; pass it as `--undo` to `trace-state decide`.
- Never print secrets; the replacement must not carry tokens, keys, or credentials quoted from the traces.

Then record every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill --action update --target <name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`. Map both `edit` and `propose` to `--action update`.