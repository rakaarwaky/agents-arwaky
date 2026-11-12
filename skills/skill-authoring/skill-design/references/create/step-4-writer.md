# Create — Step 4: Choose the writer

**Goal:** pick the writer path by description length: CLI verb, `skill_manage`, or direct `write_file`.

Three ways to write the skill; pick by description length:

- **`sac create skill <name> --category <cat> --apply`** — the CLI verb; creates the directory and `SKILL.md` in one call with frontmatter keys `name`, `description`, `when-to-use`, `argument-hint`, and the body. Pass `--apply` to write; without it you get a dry-run plan.
- **`skill_manage(action=create)`** — safe default; creates the directory and `SKILL.md` in one call. It enforces a ~60-char budget on the `description:` line (the skill index clips anything longer) and rolls back the whole batch on any violation. Draft the description first and count it; if it will exceed ~60 chars, don't fight the validator loop — use the direct writer below. When this writer succeeds, skip to `step-6-verify.md`.
- **Write the files directly** (`write_file`) — continue with `step-5-write-skill.md`. Use this when the description needs more than ~60 chars, when building a richer multi-file skill, or when `sac create skill` keeps rejecting frontmatter. After writing, run `sac catalog` to register the skill.

- **Splitting a monolith into a modular category folder** — when the user asks to turn one existing `SKILL.md` + `references/` into several sibling skill folders (e.g. `account-manager/`, `password-manager/`, `brave-setup/`), each new subfolder must be a self-contained skill with its own `SKILL.md` (four mandatory frontmatter keys, `# Title` / `## Rules` / `## Routing` body) and its own `references/` subfolder. The old monolith `SKILL.md` and its `references/` are deleted in the same commit — never leave both the old and new trees in the tree. The category folder gains a `DESCRIPTION.md` (frontmatter `description:` key, one-line) so `sac lint` does not fire `missing-category-description`. Sibling skills cross-reference each other by name in their `when-to-use:` field (e.g. "setup belongs to the sibling `brave-setup` skill"); resolve each named sibling against the tree before committing (Rules: dangling refs rot fast). After writing all files, rebuild `catalog.json` (Rules: tracked catalog artifact) and verify each new skill's frontmatter parses with `yaml.safe_load` — unquoted `description:` values containing `: ` (colon + space) silently break the YAML and the skill list will show no description.

## Commands

```bash
# CLI verb (description ≤ ~60 chars)
sac create skill <name> --category <cat> --apply

# Register after direct write_file (long/rich skills)
sac catalog
```

The ~60-char index budget and the 1,024-char parser limit (Rules: Grok Build parser limits) are different ceilings: the parser accepts long descriptions, the index display clips them.

## Completion

- A writer path is chosen: `skill_manage` (short description, skip to verify) or `write_file` (long/rich, continue to Step 5).
