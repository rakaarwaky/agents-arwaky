# Step 5: Verify

Re-read every file the apply step touched:

- `create` — confirm `<user skills dir>/<name>/SKILL.md` exists and its frontmatter
  parses with the `name`, `description`, `user-invocable: true`, and `origin:
  learn` keys.
- `edit` / `propose` — confirm the change is present in the target file and the
  original exists in the run's trash (`<GROK_HOME>/learn/trash/<run
  name>/originals/`).
- `delete` — confirm the skill directory is gone from its original location and
  present in the run's trash.
- `group` — verify each member individually under the rules above.

Confirm every recorded decision is in the run dir (`stc traces state get`
shows the `decided` entries for this run). Run `stc skills lint` over the
touched skill paths. Stop at the first failure and report it before continuing.
