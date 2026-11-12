# Create — Step 3: Create the directory

**Goal:** create the skill directory, any needed subdirs, and register a new category in the catalog.

```bash
mkdir -p <SKILL_DIR>
```

Create `<SKILL_DIR>/scripts/` if the skill ships helper scripts and `<SKILL_DIR>/references/` if it needs reference docs. The file fails to save without the directory. If the category folder is new, create its `DESCRIPTION.md` — the pack audit requires one.

## Commands

```bash
# Create the skill directory
mkdir -p <SKILL_DIR>

# Register a new category (only when the category folder is new)
sac create category <cat> --description "<one-line category description>" --apply

# Rebuild the catalog so the new category appears
sac catalog
```

Without `--apply` the `create category` command previews the plan; with it, the category folder and `DESCRIPTION.md` are written.

**Catalog artifacts:** `sac catalog --build` regenerates `catalog.json` at the skills root. `catalog.json` carries each skill's `name`, `description`, `when_to_use`, and `category`. The drift check (exit 3) is available at the agent level; it is not a CLI flag on `sac catalog`.

## Completion

- `<SKILL_DIR>` exists with any needed `scripts/` / `references/` subdirs; a new category has a `DESCRIPTION.md`. `catalog.json` is rebuilt by the catalog subcommand, not by this step.
