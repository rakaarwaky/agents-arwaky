# Step 4 — Apply

For each owned action, follow these rules:

**edit** — Before the first edit to any file in a run, read it and write an untouched copy to `<GROK_HOME>/learn/trash/<run name>/originals/<name>.md`; that copy is the undo (`--undo`). Never echo a secret into `edit.anchor` or `edit.replacement`; redact evidence lines first. `search_replace` on `path` with `edit.anchor` as old string. `edit.mode`: `replace` swaps anchor for replacement, `insert_after` keeps anchor and adds replacement after it, `append` adds replacement at end. If anchor is missing, re-read the file and fix the anchor — never overwrite the whole file. After applying, re-read the changed file and confirm the change is present.

**propose** — A protected skill (plugin, bundled, git-tracked) is never edited in place. Read the protected SKILL.md in full, apply `edit.anchor` → `edit.replacement` to that text, and write the complete result to `<user skills dir>/<name>/SKILL.md`. For git-tracked targets, write the patch to `<RUN>/patches/<name>.diff` and tell the user it needs a PR. `requires_confirmation: true`.

**enable / disable** — Edit only the `[plugins]` enabled/disabled lists in `GROK_HOME/config.toml`. Read only that block; never echo config values other than plugin names. Reversible by swapping the list.

Then record every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill|workflow|hook --action create|update|delete|reject --target <name> --path <path> --decision applied|rejected|deferred [--date DATE] [--undo <trash path>]`. Map edit/propose/enable/disable to `--action update`.
