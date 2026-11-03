# Step 4 — Apply

## actions.json field shapes

Each entry in `actions.json` carries:

```json
{
  "id": "A1",
  "kind": "skill",
  "action": "create | edit | delete | propose | ask | group",
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
    "anchor": "<exact substring of the current file, or \"\" for create>",
    "replacement": "<full replacement text, or full file content for create>",
    "mode": "replace | insert_after | append"
  }
}
```

Field rules:

- `id` is `A1`, `A2`, … in report order.
- `path` is exact: the SKILL.md file for the skill the action touches, or the skill
  directory for `delete`.
- `protected` and `referenced_by` are derived from the skill's file location and the
  session records; the run dir holds no `surfaces.json`.
- `requires_confirmation` is `true` for `ask`, `propose`, any `delete` of the only
  copy of a job, and any unverified claim.
- `edit` is required for `create`, `edit`, and `propose`; omit it for `delete`,
  `ask`, and `group`.

## Per-action rules

**create** (`--learn`) — The target is `<user skills dir>/<name>/SKILL.md` (the
directory is created if missing). The `edit.replacement` is the whole file: `---`
frontmatter with `name` (matching the directory), `description` (what it does plus
the trigger phrases observed in the traces), `user-invocable: true`, `origin: learn`
(provenance the client reports as `skill_origin`; never omit it, never another
value), then a body of imperative steps using the quoted phrases as the trigger
list.

**edit** (`--evolve`) — Before the first edit to any file in a run, read it and
write an untouched copy to `<GROK_HOME>/learn/trash/<run name>/originals/<name>.md`;
that copy is the undo (`--undo`). Never echo a secret into `edit.anchor` or
`edit.replacement`; redact evidence lines first. `search_replace` on `path` with
`edit.anchor` as old string. `edit.mode`: `replace` swaps anchor for replacement,
`insert_after` keeps anchor and adds replacement after it, `append` adds replacement
at end. If anchor is missing, re-read the file and fix the anchor — never overwrite
the whole file. After applying, re-read the changed file and confirm the change is
present.

**delete** (`--unlearn`) — If `referenced_by` is non-empty, stop and ask, naming the
referrers; the action is `ask`, not `delete`. Otherwise move the skill directory to
`<GROK_HOME>/learn/trash/<run name>/` (never the OS temp dir; it must survive a
reboot) and print where it went. Undo is moving the directory back; pass the trash
path as `--undo`.

**propose** — A protected skill (bundled or git-tracked) is never created-over or
edited in place. Read the protected SKILL.md in full, apply `edit.anchor` →
`edit.replacement` to that text, and write the **complete** result to `<user skills
dir>/<name>/SKILL.md`. A user skill of the same name takes precedence over the
bundled copy; a fragment would replace the whole skill with the fragment. For
git-tracked targets, write the patch to `<RUN>/patches/<name>.diff` and tell the
user it needs a pull request. `requires_confirmation: true`. A `propose` owned by
both `--learn` and `--evolve` is applied once, recorded under the first listed mode.

**ask** — Emitted when an action would collide with, or target, a surface the user
must decide on: a skill name collision, a referenced zero-use skill, or the only
copy of a job. `reason` names the referrers or the collision. `requires_confirmation:
true`.

**group** (`--unlearn`) — One `kind: group` action bundles several zero-use skills
that share a disposition (for example "9 zero-use user skills -> ask"). `items`
carries `{name, path, protected, referenced_by, count, last_used}` per member. One
question with three options: **apply to all** (run the group's `action` on every
item), **pick items** (expand into `multi_select` questions of at most eight items
each), or **skip all** (defer). Record one `aa skills traces state decide` line per
item either way, with the group id in `--path` so a later run can tell the batch
apart.

## Records

- Undo for `create` is deleting `<user skills dir>/<name>/`; for `edit` and
  `delete` it is the trash copy. Pass the trash path as `--undo` to
  `aa skills traces state decide`.
- Never print secrets; created and edited skill files must not carry tokens, keys,
  or credentials quoted from the traces.

## Lifecycle status

The status machine over `GROK_HOME/learn/state.json` is driven by `aa skills traces state set`:

```
aa skills traces state set --run-dir <RUN> --status running
```

Set `running` when the apply phase begins. The `done` status is written by `clear` (step 0) when a run completes or is abandoned.

## Trash and restrict

When an `edit` or `delete` action produces a trash copy, the apply step writes it
to `<GROK_HOME>/learn/trash/<run name>/`. To move additional validated paths into
the same trash dir (for example a workflow `.rhai` file or a `hooks/*` file the
action touched), use:

```
aa skills traces state trash --run-name <run name> <path> [<path> ...]
```

Only `skills/<name>` directories, `workflows/*.rhai` files, and `hooks/*` files
under `$GROK_HOME`, `~/.agents`, or a project `.grok` directory are accepted; any
other shape is refused.

After applying changes, restrict the modified skill files to owner-only so no
secret leaked into a trace record can be read by other users:

```
aa skills traces state restrict <path> [<path> ...]
```

This chmods each path to `0600` where the OS supports it.

Then record every decision with `aa skills traces state decide --run-dir <RUN>
--id <id> --kind skill --action create|edit|delete|propose|ask|group --target
<name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`.
