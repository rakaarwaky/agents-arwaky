---
name: skill-library
description: Manages the skills library by maintaining CATALOG.md, discovering skills, auditing category placement, repairing skill metadata, weeding duplicates, and organizing categories. Also provides the `aa skills list/show` discovery surface (formerly skill-manager). Use when the user runs /skill-library or asks to find, audit, repair, weed, organize, or catalog skills.
when-to-use: Use when the user wants to search the skill library, rebuild the skill catalog, move misplaced skills, fix skill frontmatter, detect duplicate skills, archive obsolete skills, create skill categories, or update category DESCRIPTION.md files.
argument-hint: --discover query, --catalog, --audit, --repair, --weed, --organize
---

# Skill Library

Manages the skills pack as a library. The master index is `CATALOG.md` at the skills root. Category intent is stored in each category's `DESCRIPTION.md`.

## Library layout

- Skills root: the directory three levels above `scripts/librarian.py`.
- Category folder: `skills-root/category/`
- Skill folder: `skills-root/category/skill-name/SKILL.md`
- Category metadata: `skills-root/category/DESCRIPTION.md`
- Master catalog: `skills-root/CATALOG.md`

The helper script resolves the skills root from its own file location. Do not hardcode the skills root inside this skill.

## Helper script

**Canonical path (preferred for new code):**

```bash
python3 skills/skill-authoring/scripts/cli.py COMMAND
```

**Back-compat shim (existing code continues to work):**

```bash
python3 skills/skill-authoring/skill-library/scripts/librarian.py COMMAND
```

The shim delegates to the canonical path. Both entrypoints print byte-identical stdout for all read-only subcommands.

### Examples

```bash
# Canonical form (preferred)
python3 skills/skill-authoring/scripts/cli.py catalog
python3 skills/skill-authoring/scripts/cli.py discover "github pull request"
python3 skills/skill-authoring/scripts/cli.py validate
python3 skills/skill-authoring/scripts/cli.py repair
python3 skills/skill-authoring/scripts/cli.py weed
python3 skills/skill-authoring/scripts/cli.py move automation/file-renamer productivity
python3 skills/skill-authoring/scripts/cli.py new-category data-engineering "Skills for pipelines, datasets, and data processing"
python3 skills/skill-authoring/scripts/cli.py archive old-skill

# Back-compat shim (same behavior)
python3 skills/skill-authoring/skill-librarian/scripts/librarian.py catalog
```

Dependencies: Python 3.9+. PyYAML is optional but recommended for robust YAML parsing. Without PyYAML, the script uses a minimal frontmatter parser.

## Commands

- `catalog`: rebuild `CATALOG.md`.
- `discover QUERY`: search the catalog and return matching skills.
- `validate`: report frontmatter, naming, placement, and category issues.
- `weed`: report duplicates, empty categories, and missing category descriptions.
- `repair`: apply safe mechanical repairs, then rebuild the catalog.
- `move SKILL TARGET_CATEGORY`: move a skill folder to another category, then rebuild the catalog.
- `new-category NAME DESCRIPTION`: create a category folder and write its `DESCRIPTION.md`.
- `archive SKILL`: move a skill into `_archive/` and disable its `SKILL.md`.

### Exit codes

- `0`: clean (no issues found, or read-only success)
- `1`: issues found (validation errors, weeds present)
- `2`: usage error (bad arguments, missing required input, nonexistent skill)
- `3`: catalog drift (`catalog --check` only)

## Discovery mode

Use this when the user asks to find a skill or runs `/skill-library --discover QUERY`.

- [ ] Run `discover QUERY`.
- [ ] If the catalog is missing, rebuild it first.
- [ ] Read the returned table.
- [ ] Recommend the best matching skill or skills.
- [ ] If no good match exists, say that no matching skill was found and suggest creating one with the skill-authoring skill if appropriate.

Discovery must use the catalog. Do not read every skill file unless the catalog is missing and must be rebuilt.

## Audit mode

Use this when the user asks to audit the library, fix categories, or organize skills.

- [ ] Run `validate`.
- [ ] Run `weed`.
- [ ] Read `CATALOG.md`.
- [ ] Read the relevant `DESCRIPTION.md` files.
- [ ] Decide the correct category for each misplaced skill.
- [ ] If no existing category fits, create a new category with `new-category`.
- [ ] Move misplaced skills with `move`.
- [ ] Rebuild the catalog.
- [ ] Report every move, created category, and catalog update.

The Librarian operates in Auto-Pilot mode. Apply the changes directly, then report what changed.

## Repair mode

Use this when the user asks to repair skills, fix metadata, or validate the library.

- [ ] Run `validate`.
- [ ] Run `repair` for safe mechanical fixes.
- [ ] Review remaining validation issues.
- [ ] Edit broken `SKILL.md` files to fix missing descriptions, weak trigger wording, broken references, or invalid YAML.
- [ ] Rerun `validate` until no errors remain.
- [ ] Rebuild the catalog.

The script repairs mechanical problems such as mismatched `name:` fields and missing category `DESCRIPTION.md` files. Use the agent to improve weak descriptions and restore broken skill structure.

## Weed mode

Use this when the user asks to find duplicates, obsolete skills, or dead categories.

- [ ] Run `weed`.
- [ ] For duplicate skills, choose the best maintained version.
- [ ] Archive obsolete or duplicate skills with `archive`.
- [ ] Do not permanently delete skills unless the user explicitly asks.
- [ ] Rebuild the catalog.
- [ ] Report archived skills and remaining duplicates.

## Organize mode

Use this when the user asks to reorganize categories or create a new category.

- [ ] Read the Categories table in `CATALOG.md`.
- [ ] Identify broad, missing, overlapping, or empty categories.
- [ ] Create new categories with `new-category`.
- [ ] Move skills into the correct categories with `move`.
- [ ] Improve category `DESCRIPTION.md` wording where needed.
- [ ] Rebuild the catalog.
- [ ] Report the final category structure and moved skills.

## Category rules

Category shape and `DESCRIPTION.md` constraints are the rules in
[`../_rules/skill-rules.md`](../_rules/skill-rules.md) (`category-description-present`,
`category-description-nonempty`, `category-nonempty`, `category-depth`). The category
description helps the Librarian decide where skills belong; keep it short, concrete, and
domain-focused. `references/category-rules.md` carries the folder-shape examples.

## Auto-pilot rules

- Apply changes directly.
- Always rebuild `CATALOG.md` after moves, archives, repairs, or category changes.
- Never permanently delete skills by default; archive them instead.
- Every category should have a `DESCRIPTION.md`.
- Every skill should live at `category/skill-name/SKILL.md`.
- Do not author brand-new skills here; use the skill-authoring skill for creation.
- Do not nest skills deeper than one category level.

## References

- Catalog format: `references/catalog-format.md`
- Category rules: `references/category-rules.md`
- Maintenance workflows: `references/maintenance-workflows.md`

## Completion criteria

- `CATALOG.md` exists and matches the current disk state.
- Every listed skill has a category and description.
- Every category has a `DESCRIPTION.md`, or the missing file is reported.
- Misplaced skills have been moved to correct categories.
- Duplicate and obsolete skills have been reported or archived.
- The user receives a short summary of every change made.
