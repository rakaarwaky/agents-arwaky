# Step 4 — Apply

## actions.json field shapes

Each entry in `actions.json` carries:

```json
{
  "id": "A1",
  "kind": "skill",
  "action": "create | propose | ask",
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
  }
}
```

Field rules:

- `id` is `A1`, `A2`, … in report order.
- `path` is exact.
- `protected` and `referenced_by` are copied from `surfaces.json`.
- `requires_confirmation` is `true` for `ask`, `propose`, any `delete` of the only copy of a job, and any unverified claim.
- `edit` is required for `create`, `edit`, and `propose`; omit it for enable, disable, delete, ask.

## Per-action rules

**create** — The target is `<user skills dir>/<name>/SKILL.md` (the directory is created if missing); the user skills dir comes from `surfaces.json`. The `edit.replacement` is the whole file: `---` frontmatter with `name` (matching the directory), `description` (what it does plus the trigger phrases observed in the traces), `user-invocable: true`, `origin: learn` (provenance the client reports as `skill_origin`; never omit it, never another value), then a body of imperative steps using the quoted phrases as the trigger list.

**propose** — A protected skill (plugin, bundled, git-tracked) is never created-over or edited in place; the action is `propose` with `requires_confirmation: true`, and `reason` says where the fix belongs.

- `plugin` or `bundled` owner: read the protected SKILL.md in full, apply `edit.anchor` → `edit.replacement` to that text, and write the **complete** result to `<user skills dir>/<name>/SKILL.md`. A user skill of the same name takes precedence over the bundled or plugin copy; a fragment would replace the whole skill with the fragment. Plugin and bundle syncs overwrite the protected file itself — the override is the only durable fix.
- `git-tracked` owner: write the patch to `<RUN>/patches/<name>.diff` and tell the user it needs a pull request. Never edit a git-tracked skill file: the edit lands in someone else's branch.

**ask** — Emitted when a `create` would collide with, or a phrase-join targets, a surface whose owner the user must decide (for example a skill name collision in `surfaces.json → skill_name_collisions`). `reason` names the colliding owners and their paths. `requires_confirmation: true`.

## Records

- Undo for a `create` is deleting `<user skills dir>/<name>/`; pass it as `--undo` to `aa skills trace-state decide`.
- Never print secrets; the body of a created skill must not carry tokens, keys, or credentials quoted from the traces.

Then record every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill --action create|propose|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <path>]`.