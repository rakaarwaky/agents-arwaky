# Apply rules — creation, protected targets

## create

- Target: `<user skills dir>/<name>/SKILL.md`, where `user_skills_dir` comes from `surfaces.json` (normally `<GROK_HOME>/skills`). Create the directory if missing.
- Content: `edit.replacement` is the whole file — `---` frontmatter with `name` (matching the directory), `description` (what it does plus the trigger phrases observed in the traces), `user-invocable: true`, `origin: learn` (see `report-format.md`), then a body of imperative steps. Use the quoted repeated phrases as the trigger list.
- One repeated phrase is one action; it joins the skill that already owns the job when one exists — that is an `edit`, route it to `skill-evolving`, not a new skill.
- After applying, re-read the written file and confirm the frontmatter parses.

## propose (protected target)

A protected skill is never created-over or edited in place; the action is `propose` with `requires_confirmation: true`, and `reason` says where the fix belongs.

- `plugin` or `bundled` owner: read the protected SKILL.md in full, apply `edit.anchor` → `edit.replacement` to that text, and write the **complete** result to `<user skills dir>/<name>/SKILL.md`. A user skill of the same name takes precedence over the bundled or plugin copy; a fragment would replace the whole skill with the fragment. Plugin and bundle syncs overwrite the protected file itself — the override is the only durable fix.
- `git-tracked` owner: write the patch to `<RUN>/patches/<name>.diff` and tell the user it needs a pull request. Never edit a git-tracked skill file: the edit lands in someone else's branch.

## ask

- Emitted when a `create` would collide with, or a phrase-join targets, a surface whose owner the user must decide (for example a skill name collision in `surfaces.json → skill_name_collisions`). `reason` names the colliding owners and their paths. `requires_confirmation: true`.

## Records

- Undo for a `create` is deleting `<user skills dir>/<name>/`; pass it as `--undo` to `state.py decide`.
- Never print secrets; the body of a created skill must not carry tokens, keys, or credentials quoted from the traces.
