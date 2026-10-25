# Merge Rules

Rules for merging skills in Phase 2 of `skill-lifecycle`.

## Name survival

The surviving skill keeps the `name:` that best matches the merged scope; if
neither matches, pick the more specific one.

## Frontmatter union

Merge `tags` and `when-to-use` as unions, de-duplicated; merge any body Routing
sections and drop entries pointing at skills that no longer exist. Merge
`triggers:` terms into `description:`/`when-to-use:` — the key is not parsed.
If the surviving skill had `tags: []` and the dropped skill had populated
`tags`, carry the dropped skill's tags into the survivor — otherwise the
surviving skill loses its searchability for that topic and catalog search no
longer reaches it.

## Body merge

Shared rules go in the `SKILL.md` body exactly once. Scenario-specific rules
move to `references/<scenario>.md`. Never restate a rule that already exists in
a reference.

## Conflict Resolution

If merged skills contain contradictory rules (e.g., opposing instructions),
prioritize the rule from the skill with the more complete body. If a clear
winner isn't obvious, flag the contradiction in the report for the user to
resolve manually.

## Scripts

Keep `scripts/` of the surviving skill; move or re-link scripts of dropped
skills only if the surviving skill's scenario needs them. Ensure no scripts
referenced in the surviving body are deleted.

## Empty Category Cleanup

If deleting duplicate skills leaves a category folder entirely empty (no skill
subfolders remain), delete the empty category folder and its `DESCRIPTION.md`
as well. Note this in the DELETED section of the report.

## DESCRIPTION.md

If a category is not empty, its description stays one line; update it only if
the category's skill count changed in a way that breaks the description.
