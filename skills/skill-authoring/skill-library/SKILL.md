---
name: skill-library
description: Manages the skills library — maintains CATALOG.md, discovers skills, audits category placement, repairs metadata, weeds duplicates, and organizes categories. Use when the user runs /skill-library or asks to find, audit, repair, weed, organize, catalog, or validate skills.
when-to-use: Use when the user wants to search the skill library, rebuild the catalog, move misplaced skills, or create skill categories.
argument-hint: "[--discover <query>] [--catalog] [--validate] [--repair] [--weed] [--move <skill> <category>] [--new-category <name> <desc>] [--archive <skill>]"
---

# Skill Library

You manage the skills pack as a library. The master index is `CATALOG.md` at the skills root; category intent lives in each category's `DESCRIPTION.md`. Every write command (`move`, `archive`, `new-category`) defaults to dry-run; pass `--apply` to execute. The Librarian operates in auto-pilot: apply the changes directly, then report what changed.

## Global Rules

Rules that apply to every mode. Reference files cite these; they never restate them.

- **Library layout**: skills root is `skills/` at the repository root; the helper resolves it from its own file location — never hardcode the skills root inside this skill. Category folder = `skills-root/category/`; skill folder = `skills-root/category/skill-name/SKILL.md`; category metadata = `skills-root/category/DESCRIPTION.md`; master catalog = `skills-root/CATALOG.md`.
- **Auto-pilot rules**: apply changes directly; always rebuild `CATALOG.md` after moves, archives, repairs, or category changes; never permanently delete skills by default (archive instead); every category should have a `DESCRIPTION.md`; every skill lives at `category/skill-name/SKILL.md`; never nest skills deeper than one category level; do not author brand-new skills here (route to `skill-design`).
- **Dry-run discipline**: write commands default to dry-run that only prints the planned changes; exit 0 does not mean the change was made — check the output for "Planned" lines before claiming anything was applied.
- **Exit codes**: `0` clean (no issues, or read-only success), `1` issues found (validation errors, weeds present), `2` usage error (bad arguments, missing required input, nonexistent skill), `3` catalog drift (`catalog --check` only).
- **Validation rules** (enforced by `aa skills validate` for categories and skill placement): category-description-present — Every category has a DESCRIPTION.md; category-description-nonempty — Category DESCRIPTION.md describes the category; category-nonempty — Every category holds at least one skill; category-depth — No nesting deeper than <category>/<skill>/; skill-placement — SKILL.md lives at <category>/<skill>/SKILL.md.
- **Verification after writes**: `aa skills validate` checks structure, not link validity — grep the pack for the moved or deleted skill name and fix dangling pointers before committing.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| discover | `[discover.md](references/discover.md)` | find skills by query; recommend the best match; if none, suggest creating one via skill-design. |
| repair | `[repair.md](references/repair.md)` | fix mechanical faults; the agent edits broken SKILL.md bodies; rerun validate until clean; rebuild the catalog. |
| weed | `[weed.md](references/weed.md)` | for duplicates, choose the best-maintained version; archive obsolete or duplicate skills; rebuild the catalog; report. |
| organize | `[organize.md](references/organize.md)` | reorganize or create categories; improve DESCRIPTION.md wording; rebuild the catalog if hand-edited. |
| audit | `aa skills validate + aa skills weed + read CATALOG.md` | decide the correct category for each misplaced skill; move with move --apply; report. |
| rename-category | `[rename-category.md](references/rename-category.md)` | in-place category rename: mv + cross-reference grep + catalog/validate rebuild. |