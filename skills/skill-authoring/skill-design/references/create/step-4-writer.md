# Create — Step 4: Choose the writer

Two ways to write the skill; pick by description length:

- **`aa skills create skill <name> --category <cat> --apply`** — the CLI verb; creates the directory and `SKILL.md` in one call with frontmatter keys `name`, `description`, `when-to-use`, `argument-hint`, and the body. Pass `--apply` to write; without it you get a dry-run plan.
- **`skill_manage(action=create)`** — safe default; creates the directory and `SKILL.md` in one call. It enforces a ~60-char budget on the `description:` line (the skill index clips anything longer) and rolls back the whole batch on any violation. Draft the description first and count it; if it will exceed ~60 chars, don't fight the validator loop — use the direct writer below. When this writer succeeds, skip to `step-6-verify.md`.
- **Write the files directly** (`write_file`) — continue with `step-5-write-skill.md`. Use this when the description needs more than ~60 chars, when building a richer multi-file skill, or when `aa skills create skill` keeps rejecting frontmatter. After writing, run `aa skills catalog` to register the skill.

The ~60-char index budget and the 1,024-char parser limit (Global Rules: Grok Build parser limits) are different ceilings: the parser accepts long descriptions, the index display clips them.

## Completion

- A writer path is chosen: `skill_manage` (short description, skip to verify) or `write_file` (long/rich, continue to Step 5).
