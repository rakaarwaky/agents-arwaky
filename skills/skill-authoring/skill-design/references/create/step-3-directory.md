# Create — Step 3: Create the directory

```bash
mkdir -p <SKILL_DIR>
```

Create `<SKILL_DIR>/scripts/` if the skill ships helper scripts and `<SKILL_DIR>/references/` if it needs reference docs. The file fails to save without the directory. If the category folder is new, create its `DESCRIPTION.md` — the pack audit requires one:

```bash
aa skills create category <cat> --description "<one-line category description>" --apply
```

Without `--apply` the command previews the plan; with it, the category folder and `DESCRIPTION.md` are written. Rebuild the catalog afterwards so the new category appears:

```bash
aa skills catalog
```

## Completion

- `<SKILL_DIR>` exists with any needed `scripts/` / `references/` subdirs; a new category has a `DESCRIPTION.md`.
