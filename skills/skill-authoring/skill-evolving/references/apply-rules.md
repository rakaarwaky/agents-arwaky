# Apply rules — edits, protected targets, enables

## edit

- Before the first edit to any file in a run, read it and write an untouched copy to `<GROK_HOME>/learn/trash/<run name>/originals/<name>.md`; that copy is the undo and goes in `--undo`.
- Never echo a secret or credential into `edit.anchor` or `edit.replacement`; if the evidence line contains one, redact it in the action text before applying.
- `search_replace` on `path` with `edit.anchor` as the old string. `edit.mode` says how: `replace` swaps the anchor for `replacement`, `insert_after` keeps the anchor and adds `replacement` after it, `append` adds `replacement` at the end of the file.
- If the anchor is missing, re-read the file and fix the anchor; never overwrite the whole file.
- After applying, re-read the changed file and confirm the change is present.

## propose (protected target)

A protected skill is never edited in place: plugin and bundle syncs overwrite the file, and a git-tracked edit lands in someone else's branch.

- `plugin` or `bundled`: read the protected SKILL.md in full, apply `edit.anchor` → `edit.replacement` to that text, and write the **complete** result to `<user skills dir>/<name>/SKILL.md` (a user skill of the same name takes precedence; a fragment would replace the whole skill with the fragment). `reason` says the override carries the fix.
- `git-tracked`: write the patch to `<RUN>/patches/<name>.diff` and tell the user it needs a pull request. `reason` says the fix belongs upstream.

Both are `requires_confirmation: true`.

## enable / disable

- Edit only the `[plugins]` `enabled` and `disabled` lists in `GROK_HOME/config.toml`. Read only that block; never echo config values other than plugin names.
- `edit.anchor` is the exact list line to change; the reversal is swapping the list. Reversible.

## Records

- Undo for an `edit` is the backup under `<GROK_HOME>/learn/trash/<run name>/originals/`; pass it as `--undo`.
- Undo for a `propose` is deleting the user-skill override or the patch.
- `state.py decide` one line per action, `applied` / `rejected` / `deferred`.
