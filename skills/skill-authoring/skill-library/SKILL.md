---
name: skill-library
description: Manages the skills library by maintaining CATALOG.md, discovering skills, auditing category placement, repairing skill metadata, weeding duplicates, and organizing categories. Also provides the `aa skills list/show` discovery surface (formerly skill-manager). Use when the user runs /skill-library or asks to find, audit, repair, weed, organize, catalog, or validate skills.
when-to-use: Use when the user wants to search the skill library, rebuild the skill catalog, validate or audit frontmatter rules, move misplaced skills, fix skill frontmatter, detect duplicate skills, archive obsolete skills, create skill categories, or update category DESCRIPTION.md files.
argument-hint: "[--discover <query>] [--catalog] [--validate] [--repair] [--weed] [--move <skill> <category>] [--new-category <name> <desc>] [--archive <skill>]"
---

# Skill Library

You manage the skills pack as a library. The master index is `CATALOG.md` at the skills root; category intent lives in each category's `DESCRIPTION.md`. Every write command (`move`, `archive`, `new-category`) defaults to dry-run; pass `--apply` to execute. The Librarian operates in auto-pilot: apply the changes directly, then report what changed.

## Execution Flow

1. **Pick the mode** from `description:` / `when-to-use:` and the argument: discover, audit, repair, weed, organize, rename-category, or the scheduled/headless maintenance pass.
2. **Run the helper** for the mode (`aa skills <command>`); always rebuild the catalog after moves, archives, repairs, or category changes.
3. **Apply** safe mechanical changes directly; for anything that would permanently delete a skill, archive instead and report.
4. **Validate**: after any move, run `aa skills validate` and grep the pack for the moved or deleted skill name to catch stranded cross-references and stale `metadata.related_skills` pointers before committing.
5. **Report**: summarize every move, created category, and catalog update.

## Global Rules (SSOT)

Rules that apply to every mode. Reference files cite these; they never restate them.

- **Library layout**: skills root is `skills/` at the repository root; the helper resolves it from its own file location — never hardcode the skills root inside this skill. Category folder = `skills-root/category/`; skill folder = `skills-root/category/skill-name/SKILL.md`; category metadata = `skills-root/category/DESCRIPTION.md`; master catalog = `skills-root/CATALOG.md`.
- **Auto-pilot rules**: apply changes directly; always rebuild `CATALOG.md` after moves, archives, repairs, or category changes; never permanently delete skills by default (archive instead); every category should have a `DESCRIPTION.md`; every skill lives at `category/skill-name/SKILL.md`; never nest skills deeper than one category level; do not author brand-new skills here (route to `skill-design`).
- **Dry-run discipline**: write commands default to dry-run that only prints the planned changes; exit 0 does not mean the change was made — check the output for "Planned" lines before claiming anything was applied.
- **Exit codes**: `0` clean (no issues, or read-only success), `1` issues found (validation errors, weeds present), `2` usage error (bad arguments, missing required input, nonexistent skill), `3` catalog drift (`catalog --check` only).
- **Validation rules** (enforced by `aa skills validate` for categories and skill placement): category-description-present — Every category has a DESCRIPTION.md; category-description-nonempty — Category DESCRIPTION.md describes the category; category-nonempty — Every category holds at least one skill; category-depth — No nesting deeper than <category>/<skill>/; skill-placement — SKILL.md lives at <category>/<skill>/SKILL.md.
- **Verification after writes**: `aa skills validate` checks structure, not link validity — grep the pack for the moved or deleted skill name and fix dangling pointers before committing.

## Run Steps

Each mode is a self-contained recipe; the Global Rules above apply throughout.

| Mode | Reference / command | Purpose |
| ---- | ------------------- | ------- |
| Discover | `aa skills discover QUERY` (rebuild the catalog first if it is missing) | Find skills by query; recommend the best match; if none, suggest creating one via `skill-design`. |
| Audit | `aa skills validate` + `aa skills weed` + read `CATALOG.md` and the relevant `DESCRIPTION.md` files | Decide the correct category for each misplaced skill; create a missing category with `new-category`; move with `move --apply`; report every move, created category, and catalog update. |
| Repair | `aa skills validate` + `aa skills repair` (preview by default, `--apply` to execute) | Fix mechanical faults (`name:` mismatches, missing category `DESCRIPTION.md`); the agent edits broken `SKILL.md` bodies for weak descriptions and broken structure; rerun `validate` until clean; rebuild the catalog. |
| Weed | `aa skills weed` | For duplicates, choose the best-maintained version; archive obsolete or duplicate skills with `archive`; never delete permanently unless explicitly asked; rebuild the catalog; report. |
| Organize | Read the Categories table in `CATALOG.md`; `aa skills new-category`; `aa skills move --apply` | Reorganize or create categories; improve `DESCRIPTION.md` wording; rebuild the catalog if hand-edited. |
| Rename a category | [`references/rename-category.md`](references/rename-category.md) | In-place category rename: `mv` + cross-reference grep + catalog/validate rebuild. |
| Maintenance pass (scheduled / headless) | [`references/maintenance-workflows.md`](references/maintenance-workflows.md) | Mirrors `skill-lifecycle --evolution`: reversible writes apply directly, destructive writes require a recorded undo path; log every `aa skills` command for later undo. |

Supporting references: [`references/catalog-format.md`](references/catalog-format.md) (catalog shape), [`references/category-rules.md`](references/category-rules.md) (folder-shape examples).

## Completion Criteria

- `CATALOG.md` exists and matches the current disk state.
- Every listed skill has a category and description; every category has a `DESCRIPTION.md`, or the missing file is reported.
- Misplaced skills moved to correct categories; duplicate and obsolete skills reported or archived.
- The user receives a short summary of every change made.
